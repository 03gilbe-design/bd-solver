"""Test reverse_er su caso reale: R1(A,C) R2(A,D) R3(B,E,F*) R4(B,A,L,M)
con R2.A->R1, R4.A->R1, R4.B->R3"""
import reverse_er as rv

tables = {
    "R1": {"pk": ["A"], "fk": [], "attrs": ["A", "C"], "nullable": []},
    "R2": {"pk": ["A"], "fk": [(["A"], "R1")], "attrs": ["A", "D"], "nullable": []},
    "R3": {"pk": ["B"], "fk": [], "attrs": ["B", "E", "F"], "nullable": ["F"]},
    "R4": {"pk": ["B", "A"], "fk": [(["A"], "R1"), (["B"], "R3")], "attrs": ["B", "A", "L", "M"], "nullable": []},
}
notes, er = rv.infer_er(tables)
for n in notes:
    print(n)

assert "R1" in er["entita"], er["entita"]
assert "R3" in er["entita"], er["entita"]
assert "R2" in er["entita"], "R2 ha FK=intera PK -> resta entita', ma in relazione 1:1 con R1"
assert "R4" not in er["entita"], "R4 ha 2 FK parziali sulla PK -> e' relazione N:N, non entita'"

# R2 deve generare relazione 1:1 con R1
rel_names = [r["nome"] for r in er["relazioni"]]
assert any("R2" in r["nome"] and "R1" in r["nome"] for r in er["relazioni"]), rel_names
# R4 deve generare relazione N-aria (grado 2) tra R1 e R3
r4rel = [r for r in er["relazioni"] if r["nome"] == "R4"]
assert len(r4rel) == 1, rel_names
assert set(r4rel[0]["tra"]) == {"R1", "R3"}, r4rel[0]

# test parser testo grezzo (formato esame)
testo = "R1(A, C), R2(A, D), R3(B, E, F*) e R4(B, A, L, M) con i seguenti vincoli di integrita' referenziale: R2.A -> R1, R4.A -> R1, R4.B -> R3"
parsed = rv._parse_schema_text(testo)
assert set(parsed.keys()) == {"R1", "R2", "R3", "R4"}, parsed.keys()
assert ("A", "R1") == (parsed["R2"]["fk"][0][0][0], parsed["R2"]["fk"][0][1])

# --- caso TERNARIA, dalle slide teoria vere del prof (lezione.pdf, Telegram Desktop):
# "A(a1,a2) B(b1,b2) C(c1,c2) A_B_C(a1,b1,c1,att)" -> A_B_C e' relazione 3-aria fra A,B,C.
# Conferma che l'euristica "n FK parziali sulla PK" si generalizza oltre il caso N:N binario.
tables3 = {
    "A": {"pk": ["a1"], "fk": [], "attrs": ["a1", "a2"], "nullable": []},
    "B": {"pk": ["b1"], "fk": [], "attrs": ["b1", "b2"], "nullable": []},
    "C": {"pk": ["c1"], "fk": [], "attrs": ["c1", "c2"], "nullable": []},
    "A_B_C": {"pk": ["a1", "b1", "c1"], "fk": [(["a1"], "A"), (["b1"], "B"), (["c1"], "C")],
              "attrs": ["a1", "b1", "c1", "att"], "nullable": []},
}
_, er3 = rv.infer_er(tables3)
assert "A_B_C" not in er3["entita"]
r3 = [r for r in er3["relazioni"] if r["nome"] == "A_B_C"]
assert len(r3) == 1 and set(r3[0]["tra"]) == {"A", "B", "C"} and r3[0]["grado"] == 3, r3

# --- caso IDENTIFICAZIONE ESTERNA (1 sola FK, parte della PK) + N:N puro, dalla
# trascrizione ufficiale VERIFICATA di 12-22_A (Trascrizione_12_22_A.md):
# R1(A,C) R2(A,D) [PK=(A,D), FK A->R1] R3(B,E,F*) R4(A,B,L,M) [FK A->R1, B->R3]
# ground truth: R1(0,N)--R2(1,1) identificazione esterna; R4 relazione N:N con R1(0,N)-R3(0,N)
tables_a = {
    "R1": {"pk": ["A"], "fk": [], "attrs": ["A", "C"], "nullable": []},
    "R2": {"pk": ["A", "D"], "fk": [(["A"], "R1")], "attrs": ["A", "D"], "nullable": []},
    "R3": {"pk": ["B"], "fk": [], "attrs": ["B", "E", "F"], "nullable": ["F"]},
    "R4": {"pk": ["A", "B"], "fk": [(["A"], "R1"), (["B"], "R3")], "attrs": ["A", "B", "L", "M"], "nullable": []},
}
_, er_a = rv.infer_er(tables_a)
assert "R2" in er_a["entita"] and "R4" not in er_a["entita"]
r2rel = [r for r in er_a["relazioni"] if "R2" in r["nome"]][0]
assert r2rel["card"] == {"R2": [1, 1], "R1": [0, "N"]}, r2rel
r4rel = [r for r in er_a["relazioni"] if r["nome"] == "R4"][0]
assert r4rel["card"] == {"R1": [0, "N"], "R3": [0, "N"]}, r4rel

# --- caso 12-22_C completo, dalla trascrizione ufficiale VERIFICATA
# (Trascrizione_12_22_C.md): R2 PK=(B,E) dedotta da FK multi-colonna R4.(B,E)->R2,
# relazione R2-R3 (0,1)-(0,N), R4 ternaria tutti lati (0,N).
tables_c = {
    "R1": {"pk": ["A"], "fk": [], "attrs": ["A", "C", "D"], "nullable": ["D"]},
    "R2": {"pk": ["B"], "fk": [(["H"], "R3")], "attrs": ["B", "E", "H"], "nullable": ["H"]},
    "R3": {"pk": ["H"], "fk": [], "attrs": ["H", "K"], "nullable": []},
    "R4": {"pk": ["A", "B", "E", "H"], "fk": [(["A"], "R1"), (["B", "E"], "R2"), (["H"], "R3")],
           "attrs": ["A", "B", "E", "H", "S", "T"], "nullable": ["S"]},
}
_, er_c = rv.infer_er(tables_c)
assert tables_c["R2"]["pk"] == ["B", "E"], "PK R2 doveva essere corretta a (B,E) da FK multi-colonna"
r2r3 = [r for r in er_c["relazioni"] if r["nome"] == "R2_R3"][0]
assert r2r3["card"] == {"R2": [0, 1], "R3": [0, "N"]}, r2r3
r4c = [r for r in er_c["relazioni"] if r["nome"] == "R4"][0]
assert r4c["card"] == {"R1": [0, "N"], "R2": [0, "N"], "R3": [0, "N"]}, r4c

print("TUTTI I TEST OK")
