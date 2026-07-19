"""Test pt2_schedule contro le SOLUZIONI UFFICIALI del corso
(17_esR_VSR_CSR_soluzioni.pdf): S1=CSR, S2=nonSR, S3=nonSR, S4=CSR con 3 ordinamenti
topologici (t3,t1,t2,t4,t5), (t3,t2,t1,t4,t5), (t3,t1,t4,t2,t5)."""
import pt2_schedule as ps

S1 = "r1(x), w1(x), r2(z), r1(y), w1(y), r2(x), w2(x), w2(z)"
S2 = "r1(x), w1(x), w3(x), r2(y), r3(y), w3(y), w1(y), r2(x)"
S3 = "r1(x), r2(x), w2(x), r3(x), r4(z), w1(x), w3(y), w3(x), w1(y), w5(x), w1(z), w5(y), r5(z)"
S4 = "r1(x), r3(y), w1(y), w4(x), w1(t), w5(x), r2(z), r3(z), w2(z), w5(z), r4(t), r5(t)"

assert ps.classify(S1) == "CSR", ps.classify(S1)
assert ps.classify(S2) == "nonSR", ps.classify(S2)
assert ps.classify(S3) == "nonSR", ps.classify(S3)
assert ps.classify(S4) == "CSR", ps.classify(S4)

# S1: unico seriale equivalente = (T1,T2) [dalla soluzione ufficiale]
tops1 = ps.topological_orders(ps.parse(S1))
assert tops1 == [(1, 2)], tops1

# S4: esattamente i 3 ordinamenti della soluzione ufficiale
tops4 = set(ps.topological_orders(ps.parse(S4)))
expected4 = {(3, 1, 2, 4, 5), (3, 2, 1, 4, 5), (3, 1, 4, 2, 5)}
assert tops4 == expected4, tops4

# parse round-trip
ops = ps.parse(S1)
assert ops[0] == ("r", 1, "x") and ops[-1] == ("w", 2, "z")

# LEGGE_DA di S2 (dalla soluzione: {(r2(x), w3(x))} + letture iniziali)
rf2 = ps.reads_from(ps.parse(S2))
assert (("r", 2, "x"), ("w", 3, "x")) in rf2, rf2
# SCRITTURE_FINALI di S2 = {w3(x)... no: w3(x) poi nessuno riscrive x? S2: w1(x)? no.
# soluzione ufficiale: {w3(x), w1(y)}
fw2 = ps.final_writes(ps.parse(S2))
assert fw2 == {("w", 3, "x"), ("w", 1, "y")}, fw2

# 2PL: uno schedule seriale e' sempre 2PL; S2 (nonSR) mai 2PL
assert ps.is_2pl(ps.parse("r1(x), w1(x), r2(x), w2(x)"))
assert not ps.is_2pl(ps.parse(S2))

# 2PL: controesempio UFFICIALE non banale (CSR ma NON 2PL), dalla slide del corso
# "8 - Esecuzione concorrente di transazioni - Parte III.pdf" pag.14:
# s: r1(x) w1(x) r2(x) w2(x) r3(y) w1(y) -- T1 rilascia lock su x per far passare T2,
# poi riacquisisce lock su y: viola la regola delle due fasi pur restando CSR.
S5 = "r1(x), w1(x), r2(x), w2(x), r3(y), w1(y)"
ops5 = ps.parse(S5)
assert ps.conflicts(ops5) == [
    (("r", 1, "x"), ("w", 2, "x")), (("w", 1, "x"), ("r", 2, "x")),
    (("w", 1, "x"), ("w", 2, "x")), (("r", 3, "y"), ("w", 1, "y")),
], ps.conflicts(ops5)
assert ps.is_csr(ops5) is True
assert ps.is_2pl(ops5) is False

print("TUTTI I TEST OK")
