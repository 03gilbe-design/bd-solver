"""Test end-to-end contro Esercitazione_2015-soluzioni.pdf (prova intermedia
giugno 2015, SOLUZIONI UFFICIALI). Trovato e fissato un bug reale: per un
nodo B+tree DI MEZZO in underflow, la scelta fratello sx/dx deve preferire
il lato che da' un vero merge (non redistribuzione) — vedi pt2_btree.py."""
import pt2_schedule as ps
import pt2_btree as bt

# Esecuzione concorrente: conflitti esatti, nonCSR, VSR (schedule a 4 transazioni)
S = "r0(t), r2(z), r3(z), w1(z), r3(x), r2(x), w3(x), w3(y), w2(y), w0(y), w1(t)"
ops = ps.parse(S)
official_conf = {(("r",0,"t"),("w",1,"t")), (("r",2,"z"),("w",1,"z")),
                 (("r",3,"z"),("w",1,"z")), (("r",2,"x"),("w",3,"x")),
                 (("w",3,"y"),("w",2,"y")), (("w",3,"y"),("w",0,"y")),
                 (("w",2,"y"),("w",0,"y"))}
assert set(ps.conflicts(ops)) == official_conf
assert not ps.is_csr(ops)
assert ps.classify(S) == "VSR"

# B+tree fan-out 4: stato iniziale root(L,T), foglie (B,E,G)(L,N)(T,Z)
t = {"ch": [["B","E","G"], ["L","N"], ["T","Z"]]}
# delete L: nodo di MEZZO in underflow, merge a DESTRA (vero merge) -> root(N)
t2 = bt.delete(t, "L", 4)
assert bt.levels(t2) == [[["N"]], [["B","E","G"],["N","T","Z"]]], bt.levels(t2)
# insert D (da t2): split del primo nodo -> root(E,N)
t3 = bt.insert(t2, "D", 4)
assert bt.levels(t3) == [[["E","N"]], [["B","D"],["E","G"],["N","T","Z"]]], bt.levels(t3)

print("ESERCITAZIONE 2015: schedule + B+tree match esatto con soluzioni ufficiali")
