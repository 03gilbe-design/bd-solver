"""Test end-to-end contro Esercitazione_2016-soluzioni.pdf (prova intermedia
7 giugno 2016, SOLUZIONI UFFICIALI complete) — ground truth mai usato in
sviluppo: i motori erano gia' scritti quando queste soluzioni sono state lette.
Match esatto 3/3 verificato il 2026-07-19. Include il primo caso d'esame reale
VSR-ma-non-CSR (prima verificato solo su esercizi/teoria)."""
import pt2_schedule as ps
import pt2_costo as pc
import pt2_btree as bt

# 1) Esecuzione concorrente: nonCSR ma VSR, conflitti come da soluzione
S = "r4(t), w2(t), r1(t), r4(y), r3(y), w4(y), w4(z), w3(z), w1(t), w2(x), w1(z)"
ops = ps.parse(S)
official_conf = {(("r",4,"t"),("w",2,"t")), (("r",4,"t"),("w",1,"t")),
                 (("w",2,"t"),("r",1,"t")), (("w",2,"t"),("w",1,"t")),
                 (("r",3,"y"),("w",4,"y")), (("w",4,"z"),("w",3,"z")),
                 (("w",4,"z"),("w",1,"z")), (("w",3,"z"),("w",1,"z"))}
assert set(ps.conflicts(ops)) == official_conf
assert not ps.is_csr(ops)
assert ps.classify(S) == "VSR"

# 2) Ottimizzazione: MEDICO(sel in buffer) x VISITA(no filtro) = 96012; con indice = 9756
r = pc.solve(np_outer=12, nr_outer=1200, val_sel_outer=25,
             np_inner=2000, pagine_sel_inner=2000,
             nr_sel_inner=240000, val_join_inner=1200, prof_indice=3,
             interna_selezionata=False)
assert r["totale"] == 96012, r["totale"]
assert r["totale_indice"] == 9756, r["totale_indice"]

# 3) B+tree fan-out 5: build root (L,P,S); insert B -> split, root (D,L,P,S);
#    C, E, Q senza split
t = bt.build([["A","D","F","H"], ["L","M","O"], ["P","R"], ["S","T","U","Z"]], 5)
assert bt.levels(t)[0] == [["L","P","S"]]
t = bt.insert(t, "B", 5)
assert bt.levels(t) == [[["D","L","P","S"]],
                        [["A","B"],["D","F","H"],["L","M","O"],["P","R"],["S","T","U","Z"]]]
for k in ("C", "E", "Q"):
    t = bt.insert(t, k, 5)
assert bt.levels(t) == [[["D","L","P","S"]],
                        [["A","B","C"],["D","E","F","H"],["L","M","O"],["P","Q","R"],["S","T","U","Z"]]]

print("ESERCITAZIONE 2016: 3/3 match esatto con soluzioni ufficiali")
