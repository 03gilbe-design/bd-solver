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

def fmt_op(op):
    a, t, o = op
    return f"{a}{t}({o})"


def ciclo(ops):
    """Un ciclo del grafo dei conflitti come lista [T_a, T_b, ..., T_a], o None."""
    edges = conflict_graph(ops)
    adj = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
    def dfs(n, path):
        for m in sorted(adj.get(n, [])):
            if m in path:
                return path[path.index(m):] + [m]
            r = dfs(m, path + [m])
            if r:
                return r
        return None
    for s in sorted(adj):
        r = dfs(s, [s])
        if r:
            return r
    return None


def vincoli_view(ops):
    """Precedenze che un seriale view-equivalente DEVE rispettare, come nelle soluzioni
    del prof ('LeggeDa(S) = ... => t2 < t1'): lettura da w_j -> T_j < T_i; lettura del
    valore iniziale -> T_i prima di ogni scrittore di x; scrittura finale di T_f su x ->
    ogni altro scrittore di x prima di T_f."""
    writers = {}
    for a, t, o in ops:
        if a == "w":
            writers.setdefault(o, set()).add(t)
    v = set()
    for (r, w) in reads_from(ops):
        _, ti, o = r
        _, tj, _ = w
        if tj == 0:
            v |= {(ti, tk) for tk in writers.get(o, ()) if tk != ti}
        else:
            v.add((tj, ti))
    for _, tf, o in final_writes(ops):
        v |= {(tk, tf) for tk in writers.get(o, ()) if tk != tf}
    return sorted(v)


def seriale_view(ops):
    """Primo ordine seriale view-equivalente a S, o None (esaustivo come is_vsr)."""
    ts = transactions(ops)
    rf, fw = reads_from(ops), final_writes(ops)
    for perm in permutations(sorted(ts)):
        serial = [op for t in perm for op in ts[t]]
        if reads_from(serial) == rf and final_writes(serial) == fw:
            return perm
    return None


def _intervalli(ops, t, p):
    """lock di T con lock point p: per oggetto -> (inizio S, inizio X o None, fine).
    Acquisizione al primo uso o prima (anticipata fino a p), rilascio all'ultimo uso o dopo p."""
    out = {}
    for i, (a, tt, o) in enumerate(ops):
        if tt != t:
            continue
        s0, x0, e = out.get(o, (i, None, i))
        if a == "w" and x0 is None:
            x0 = i
        out[o] = (s0, x0, max(e, i))
    return {o: (min(s0, p), None if x0 is None else min(x0, p), max(e, p)) for o, (s0, x0, e) in out.items()}


def lock_2pl(ops):
    """Ricerca esatta di un'assegnazione lock/unlock a due fasi (lock anticipabili, come nelle
    slide: il controesempio 'r1(x) w1(x) r2(x) w2(x) r3(y) w1(y)' contiene r3(y) proprio perche'
    T1 non possa prendere y in anticipo). Ritorna {T: lock point} oppure None.
    ponytail: forza bruta sui lock point (n+1)^T, ok per esami (3-5 transazioni, ~12 azioni)."""
    from itertools import product
    if not is_csr(ops):
        return None
    ts = sorted(transactions(ops))
    pos = {t: [i for i, op in enumerate(ops) if op[1] == t] for t in ts}
    # lock point tra due azioni; +t/1000 rende distinti gli istanti di transazioni diverse
    scelte = [[k + 0.5 + t / 1000 for k in range(pos[t][0] - 1, pos[t][-1] + 1)] for t in ts]
    for pts in product(*scelte):
        iv = {t: _intervalli(ops, t, p) for t, p in zip(ts, pts)}
        ok = True
        for a in ts:
            for b in ts:
                if a >= b:
                    continue
                for o in iv[a].keys() & iv[b].keys():
                    sa, xa, ea = iv[a][o]
                    sb, xb, eb = iv[b][o]
                    # conflitto se si sovrappongono e almeno uno dei due tiene X nel tratto comune
                    if xa is not None and xa < eb and sb < ea or xb is not None and xb < ea and sa < eb:
                        ok = False
                        break
                if not ok: break
            if not ok: break
        if ok:
            return dict(zip(ts, pts))
    return None


def sequenza_lock(ops, lp):
    """schedule con sl/xl/u inseriti (testimone 2PL): sl=lock condiviso, xl=esclusivo, u=unlock."""
    ev = []
    for i, op in enumerate(ops):
        ev.append((i, fmt_op(op)))
    for t, p in lp.items():
        for o, (s0, x0, e) in _intervalli(ops, t, p).items():
            if x0 is None or s0 < x0:
                ev.append((s0 - 0.01 if s0 == int(s0) else s0, f"sl{t}({o})"))
            if x0 is not None:
                ev.append((x0 - 0.01 if x0 == int(x0) else x0, f"xl{t}({o})"))
            ev.append((e + 0.01 if e == int(e) else e + 0.0001, f"u{t}({o})"))
    return ", ".join(x for _, x in sorted(ev))


def perche_non_2pl(ops):
    """None se 2PL, altrimenti il motivo (per 'giustificare la risposta')."""
    if not is_csr(ops):
        return "S non è CSR e ogni schedule 2PL è CSR (2PL è contenuto in CSR)"
    if lock_2pl(ops) is not None:
        return None
    first_use, lock_point = {}, {}
    for idx, (a, t, o) in enumerate(ops):
        first_use.setdefault((t, o), idx)
    for (t, o), idx in first_use.items():
        lock_point[t] = max(lock_point.get(t, -1), idx)
    for i in range(len(ops)):
        for j in range(i + 1, len(ops)):
            a1, t1, o1 = ops[i]
            a2, t2, o2 = ops[j]
            if t1 != t2 and o1 == o2 and "w" in (a1, a2) and lock_point[t1] > j:
                return (f"T{t1} deve rilasciare il lock su {o1} prima di {fmt_op(ops[j])}, "
                        f"ma deve ancora acquisire un lock dopo ({fmt_op(ops[lock_point[t1]])}) "
                        f"e non puo' prenderlo in anticipo senza bloccare un'altra transazione: "
                        f"violata la regola delle due fasi")
    return "nessuna assegnazione di lock a due fasi e' compatibile con S"


def is_2pl(ops):
    """2PL sse esiste un'assegnazione di lock/unlock a due fasi compatibile con S (lock
    anticipabili). Prima (fino al 30/09/2026) il test era 'lock al primo uso', che dava falsi
    NO quando una transazione puo' prendere un lock in anticipo (es. r1(x), w2(x), r1(y))."""
    return lock_2pl(ops) is not None
