"""Test di PROPRIETA' su migliaia di casi casuali (non solo sugli esempi del prof).

Perche' esiste (30/09/2026): il test 2PL "lock al primo uso" passava tutti gli esempi ufficiali ma era
sbagliato (le slide ammettono lock anticipati); nessun esempio del prof distingueva le due letture.
Qui ogni motore e' confrontato con la TEORIA (teoremi delle slide) e con controllori indipendenti:
- schedule: 2PL => CSR => VSR; seriali sempre 2PL/CSR/VSR; il vecchio test (sufficiente) implica il nuovo;
  ogni testimone 2PL e' ricontrollato da un simulatore indipendente della tabella dei lock.
- ripresa: UNDO/REDO ricalcolati con la definizione (attive al CK + iniziate dopo - committate dopo).
- B+-tree: dopo ogni insert/delete foglie alla stessa profondita', riempimento nei limiti, chiavi ordinate
  e insieme delle chiavi = quello atteso.
Seed fisso: riproducibile. Stdlib pura (Termux)."""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt2_schedule as ps, pt2_ripresa as pr, pt2_btree as pb

rnd = random.Random(20260930)
N = 1500


# ---------- schedule ----------
def vecchio_2pl(ops):
    """test pre-30/09 ('lock alla prima azione'). SBAGLIATO in entrambe le direzioni: falsi NO (lock
    anticipabili) e falsi SI (es. w1(y) r2(y) r1(y): T1 dovrebbe riprendere y dopo averlo rilasciato)."""
    if not ps.is_csr(ops):
        return False
    first, lp = {}, {}
    for i, (a, t, o) in enumerate(ops):
        first.setdefault((t, o), i)
    for (t, o), i in first.items():
        lp[t] = max(lp.get(t, -1), i)
    return not any(ops[i][1] != ops[j][1] and ops[i][2] == ops[j][2] and "w" in (ops[i][0], ops[j][0])
                   and lp[ops[i][1]] > j for i in range(len(ops)) for j in range(i + 1, len(ops)))


def simula_lock(ops, lp):
    """controllore INDIPENDENTE: rigioca la sequenza sl/xl/u del testimone su una tabella dei lock."""
    import re
    seq = [x.strip() for x in ps.sequenza_lock(ops, lp).split(",")]
    held, rilasciato, azioni = {}, set(), []
    for ev in seq:
        m = re.match(r"(sl|xl|u|r|w)(\d+)\((\w)\)", ev)
        k, t, o = m.group(1), int(m.group(2)), m.group(3)
        h = held.setdefault(o, {})
        if k in ("sl", "xl"):
            assert t not in rilasciato, f"acquisizione dopo un rilascio: {ev}"
            altri = {tt: m_ for tt, m_ in h.items() if tt != t}
            assert not (k == "xl" and altri) and not any(m_ == "x" for m_ in altri.values()), f"conflitto {ev}"
            h[t] = "x" if k == "xl" or h.get(t) == "x" else "s"
        elif k == "u":
            h.pop(t, None); rilasciato.add(t)
        else:
            assert t in h and (k == "r" or h[t] == "x"), f"azione senza lock: {ev}"
            azioni.append((k, t, o))
    assert azioni == ops, "il testimone cambia l'ordine delle azioni"


def schedule_casuale():
    ts, objs = rnd.randint(2, 3), "xyz"[:rnd.randint(1, 3)]
    ops = [(rnd.choice("rw"), rnd.randint(1, ts), rnd.choice(objs)) for _ in range(rnd.randint(3, 8))]
    return ops


conta = {"2pl": 0, "csr": 0, "vsr": 0, "falsi_no": 0, "falsi_si": 0}
for _ in range(N):
    ops = schedule_casuale()
    csr, vsr, due = ps.is_csr(ops), ps.is_vsr(ops), ps.is_2pl(ops)
    assert not due or csr, f"2PL ma non CSR: {ops}"          # teorema slide 8 pag.13: 2PL => CSR
    assert not csr or vsr, f"CSR ma non VSR: {ops}"
    if due:
        simula_lock(ops, ps.lock_2pl(ops))          # ogni SI' ha un testimone valido
    v = vecchio_2pl(ops)
    conta["falsi_no"] += due and not v
    conta["falsi_si"] += v and not due
    serial = [op for t in sorted({o[1] for o in ops}) for op in ops if op[1] == t]
    assert ps.is_2pl(serial) and ps.is_csr(serial) and ps.is_vsr(serial), f"seriale non 2PL/CSR/VSR: {serial}"
    conta["2pl"] += due; conta["csr"] += csr; conta["vsr"] += vsr
# i due esempi della slide 8 Parte III
assert not ps.is_csr(ps.parse("w1(x) r2(x) w2(x) w2(y) r1(y)"))                       # pag.13
assert ps.is_csr(ps.parse("r1(x) w1(x) r2(x) w2(x) r3(y) w1(y)")) and \
    not ps.is_2pl(ps.parse("r1(x) w1(x) r2(x) w2(x) r3(y) w1(y)"))                     # pag.14
assert ps.is_2pl(ps.parse("r1(x) w1(x) r2(x) w2(x) w1(y)")), "senza r3(y) T1 anticipa il lock su y"
assert not ps.is_2pl(ps.parse("w1(y), r2(y), r1(y)")), "T1 dovrebbe riprendere y dopo il rilascio"
assert ps.is_2pl(ps.parse("r2(y), w2(z), w2(x), w1(z), w2(y), w2(s), r3(y), r3(x), r1(x), r1(y), w3(x), w1(s)")), \
    "esame 15/06/2026 (= 14/09): e' 2PL con lock anticipati"
print(f"SCHEDULE OK su {N} casuali: 2PL={conta['2pl']} CSR={conta['csr']} VSR={conta['vsr']}; il vecchio "
      f"test avrebbe sbagliato {conta['falsi_no']} falsi NO e {conta['falsi_si']} falsi SI")


# ---------- ripresa ----------
for _ in range(N):
    T = [f"T{i}" for i in range(1, rnd.randint(3, 6) + 1)]
    log, iniziate, finite, ck_fatto = [], [], set(), False
    for t in T:
        pass
    eventi = []
    for t in T:
        eventi.append(("B", t))
    rnd.shuffle(eventi)
    stato = {}
    k = 0
    for _ in range(rnd.randint(8, 18)):
        attive = [t for t in T if stato.get(t) == "attiva"]
        scelta = rnd.random()
        if not ck_fatto and scelta < 0.12 and len(log) > 2:
            log.append(("CK", attive)); ck_fatto = True
        elif scelta < 0.35:
            nuove = [t for t in T if t not in stato]
            if nuove:
                t = nuove[0]; stato[t] = "attiva"; log.append(("B", [t]))
        elif attive and scelta < 0.8:
            t = rnd.choice(attive); k += 1
            tipo = rnd.choice("UID")
            log.append((tipo, [t, f"O{k}"] + (["B" + str(k), "A" + str(k)] if tipo == "U" else ["X" + str(k)])))
        elif attive:
            t = rnd.choice(attive); c = "C" if rnd.random() < 0.7 else "A"
            stato[t] = c; log.append((c, [t]))
    testo = ", ".join(f"{k_}({','.join(a)})" for k_, a in log)
    r = pr.ripresa(testo)
    # definizione indipendente
    idx = max((i for i, (k_, _) in enumerate(log) if k_ == "CK"), default=None)
    undo = set(log[idx][1]) if idx is not None else set()
    redo = set()
    for k_, a in log[(idx + 1) if idx is not None else 0:]:
        if k_ == "B":
            undo.add(a[0])
        elif k_ == "C":
            undo.discard(a[0]); redo.add(a[0])
    assert set(r["undo"]) == undo and set(r["redo"]) == redo, (testo, r["undo"], r["redo"], undo, redo)
    assert not (undo & redo)
print(f"RIPRESA OK su {N} log casuali (UNDO/REDO = definizione, disgiunti)")


# ---------- B+-tree ----------
def foglie(n, d=0):
    return [(n, d)] if pb.is_leaf(n) else [x for c in n["ch"] for x in foglie(c, d + 1)]


def controlla(t, f, attese):
    min_ptr, min_keys = pb._mins(f)
    fl = foglie(t)
    assert len({d for _, d in fl}) == 1, "foglie a profondita' diverse"
    chiavi = [k for n, _ in fl for k in n]
    assert chiavi == sorted(attese), f"chiavi {chiavi} != {sorted(attese)}"
    for n, _ in fl:
        assert len(n) <= f - 1 and (len(fl) == 1 or len(n) >= min_keys), f"foglia fuori limiti {n}"

    def interni(n, radice):
        if pb.is_leaf(n):
            return
        k = len(n["ch"])
        assert k <= f and (k >= 2 if radice else k >= min_ptr), f"nodo interno con {k} figli"
        for c in n["ch"]:
            interni(c, False)
    interni(t, True)


prove = 0
for _ in range(300):
    f = rnd.choice([4, 5])
    tutte = list(range(1, 60))
    rnd.shuffle(tutte)
    min_keys = pb._mins(f)[1]
    nf = rnd.randint(2, f)
    presi = sorted(tutte[:nf * (f - 1)])
    lf, i = [], 0
    for j in range(nf):
        q = rnd.randint(min_keys, f - 1)
        lf.append(presi[i:i + q]); i += q
    t = pb.build(lf, f)
    attese = set(k for l in lf for k in l)
    controlla(t, f, attese)
    for _ in range(6):
        if rnd.random() < 0.5 or len(attese) <= min_keys * 2:
            k = rnd.choice([x for x in range(1, 60) if x not in attese])
            t = pb.insert(t, k, f); attese.add(k)
        else:
            k = rnd.choice(sorted(attese))
            t = pb.delete(t, k, f); attese.discard(k)
        controlla(t, f, attese); prove += 1
print(f"B+-TREE OK: {prove} insert/delete casuali (fan-out 4 e 5) con tutti gli invarianti")
print("TUTTI I TEST OK")
