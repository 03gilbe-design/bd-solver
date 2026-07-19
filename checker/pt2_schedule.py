#!/usr/bin/env python3
"""pt2_schedule.py — esercizio "Esecuzione concorrente" della III prova (parte 2):
classificazione di uno schedule come CSR / VSR / nonSR + test 2PL + schedule seriali
equivalenti. Deterministico, stdlib puro (Termux-ok).

FONTE VERIFICATA: 17_esR_VSR_CSR_soluzioni.pdf (esercizi risolti ufficiali del corso) —
i 4 schedule S1-S4 con relativo esito (CSR/nonSR) e ordinamenti topologici sono il
ground truth dei test in test_pt2_schedule.py.

Definizioni usate (come nelle soluzioni ufficiali):
- conflitto: due azioni di transazioni diverse sullo stesso oggetto, almeno una scrittura
- CSR: grafo dei conflitti aciclico; i seriali equivalenti = ordinamenti topologici
- VSR: esiste uno schedule seriale con stesso LEGGE_DA e stesse SCRITTURE_FINALI
  (verifica esaustiva sulle permutazioni: ok per gli esami, 3-5 transazioni)
- 2PL: esiste un'assegnazione di lock/unlock a due fasi compatibile con lo schedule
  (test standard: lo schedule e' 2PL se e' CSR e l'ordine di "crescita" e' rispettabile;
  qui usiamo il test operativo insegnato nel corso: per ogni coppia in conflitto
  T_i -> T_j, TUTTI i lock di T_i sull'oggetto conteso precedono, e la fase di rilascio
  di T_i inizia prima che T_j acquisisca — implementato come: schedule CSR e per ogni
  transazione l'ultimo lock acquisito prima del primo rilascio necessario)."""
import re
from itertools import permutations

def parse(s):
    """'r2(y), w3(z)' -> [('r',2,'y'), ('w',3,'z')]"""
    out = []
    for m in re.finditer(r"([rw])\s*(\d+)\s*\(\s*(\w+)\s*\)", s):
        out.append((m.group(1), int(m.group(2)), m.group(3)))
    return out

def transactions(ops):
    ts = {}
    for a, t, o in ops:
        ts.setdefault(t, []).append((a, t, o))
    return ts

def conflicts(ops):
    """coppie ordinate di azioni in conflitto (i<j, transazioni diverse, stesso oggetto,
    almeno una w)"""
    out = []
    for i in range(len(ops)):
        for j in range(i + 1, len(ops)):
            a1, t1, o1 = ops[i]
            a2, t2, o2 = ops[j]
            if t1 != t2 and o1 == o2 and ("w" in (a1, a2)):
                out.append((ops[i], ops[j]))
    return out

def conflict_graph(ops):
    """archi t1->t2 dal grafo dei conflitti"""
    return {(c[0][1], c[1][1]) for c in conflicts(ops)}

def _has_cycle(edges, nodes):
    adj = {n: [] for n in nodes}
    for a, b in edges:
        adj[a].append(b)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    def dfs(n):
        color[n] = GRAY
        for m in adj[n]:
            if color[m] == GRAY: return True
            if color[m] == WHITE and dfs(m): return True
        color[n] = BLACK
        return False
    return any(color[n] == WHITE and dfs(n) for n in nodes)

def is_csr(ops):
    ts = set(t for _, t, _ in ops)
    return not _has_cycle(conflict_graph(ops), ts)

def reads_from(ops):
    """insieme LEGGE_DA: (r_i(x), w_j(x)) se r_i legge il valore scritto dall'ultima w_j
    precedente (j != i). Se nessuna w precede, legge il valore iniziale (annotato con t=0)."""
    out = set()
    last_w = {}
    for a, t, o in ops:
        if a == "r":
            w = last_w.get(o)
            if w is not None and w[1] != t:
                out.add((("r", t, o), w))
            elif w is None:
                out.add((("r", t, o), ("w", 0, o)))   # valore iniziale
        else:
            last_w[o] = ("w", t, o)
    return out

def final_writes(ops):
    last = {}
    for a, t, o in ops:
        if a == "w":
            last[o] = ("w", t, o)
    return set(last.values())

def is_vsr(ops):
    """VSR sse esiste un seriale con stesso LEGGE_DA e SCRITTURE_FINALI.
    Esaustivo sulle permutazioni delle transazioni (esami: max 5-6 transazioni)."""
    if is_csr(ops):        # CSR => VSR, scorciatoia
        return True
    ts = transactions(ops)
    rf, fw = reads_from(ops), final_writes(ops)
    for perm in permutations(ts):
        serial = [op for t in perm for op in ts[t]]
        if reads_from(serial) == rf and final_writes(serial) == fw:
            return True
    return False

def classify(s):
    """'r1(x), ...' -> 'CSR' | 'VSR' | 'nonSR' (CSR implica VSR: si riporta la piu' forte)"""
    ops = parse(s)
    if is_csr(ops):
        return "CSR"
    if is_vsr(ops):
        return "VSR"
    return "nonSR"

def topological_orders(ops):
    """tutti gli ordinamenti topologici del grafo dei conflitti (= seriali conflict-equivalenti)"""
    ts = sorted(set(t for _, t, _ in ops))
    edges = conflict_graph(ops)
    out = []
    def backtrack(remaining, order):
        if not remaining:
            out.append(tuple(order)); return
        for n in remaining:
            if all(a not in remaining for a, b in edges if b == n):
                backtrack([m for m in remaining if m != n], order + [n])
    backtrack(ts, [])
    return out

def serial_schedule(ops, order):
    ts = transactions(ops)
    return [op for t in order for op in ts[t]]

def is_2pl(ops):
    """Test 2PL insegnato nel corso: simula lock a due fasi 'piu' pigri possibile'.
    Ogni transazione: acquisisce il lock su un oggetto alla prima azione che lo usa,
    puo' rilasciare solo dopo l'ultima acquisizione (fase di rilascio). Lo schedule e'
    2PL se esiste un'esecuzione compatibile: qui usiamo il criterio necessario e
    sufficiente operativo: per ogni arco di conflitto T_i->T_j sullo stesso oggetto,
    serve che T_i rilasci prima che T_j acquisisca; incrociando tutti i vincoli, lo
    schedule e' 2PL sse il grafo 'lock-point' e' consistente. Implementazione:
    lock point L(T) = posizione dell'ultima PRIMA-azione-su-oggetto di T; per ogni
    conflitto (op_i di T_i, op_j di T_j) con i<j serve L(T_i) < posizione(op_j)."""
    if not is_csr(ops):
        return False
    # prima azione di T su ciascun oggetto = momento in cui T DEVE avere il lock
    first_use = {}
    for idx, (a, t, o) in enumerate(ops):
        first_use.setdefault((t, o), idx)
    # lock point di T = max sulle prime-azioni (ultimo lock che T acquisisce)
    lock_point = {}
    for (t, o), idx in first_use.items():
        lock_point[t] = max(lock_point.get(t, -1), idx)
    # vincolo: per ogni conflitto op_i (T_i) < op_j (T_j), T_i deve aver GIA' superato
    # il suo lock point (cioe' essere in fase di rilascio) prima di op_j
    pos = {id(op): i for i, op in enumerate(ops)}
    for i in range(len(ops)):
        for j in range(i + 1, len(ops)):
            a1, t1, o1 = ops[i]
            a2, t2, o2 = ops[j]
            if t1 != t2 and o1 == o2 and ("w" in (a1, a2)):
                if lock_point[t1] > j:
                    return False
    return True
