"""Audit regola-per-regola: il codice dei motori pt2_* segue le SLIDE di teoria
ufficiali del corso (non solo gli esercizi risolti).
Fonti: Lezione_04_Strutture_Fisiche_BTree_Hash.pdf (B+tree), "7/8 - Esecuzione
concorrente di transazioni" (conflitti/CSR/VSR/2PL), "10 - Ottimizzazione di
interrogazioni - Parte II" (formule NLJ)."""
import math
import pt2_btree as bt
import pt2_schedule as ps
import pt2_costo as pc

# ---- B+tree (Lezione_04) ----
# vincoli riempimento: foglia ceil((n-1)/2)<=#chiavi<=n-1, interno ceil(n/2)<=#punt<=n
for f in (3, 4, 5, 6, 7):
    mp, mk = bt._mins(f)
    assert mk == math.ceil((f - 1) / 2), (f, mk)
    assert mp == math.ceil(f / 2), (f, mp)

# split foglia (pag.18): primi ceil((n-1)/2) valori nel primo nodo, rimanenti nel secondo
t = bt.build([[10, 20, 30, 40], [50, 60]], 5)
t = bt.insert(t, 25, 5)
lv = bt.levels(t)
assert lv[-1][0] == [10, 20] and lv[-1][1] == [25, 30, 40], lv[-1]

# merge (pag.22): totale <= n-1 chiavi -> nodo unico; altrimenti redistribuzione
t = bt.build([[1, 2], [3, 4], [5, 6, 7, 8]], 5)
assert bt.levels(bt.delete(t, 2, 5))[-1][0] == [1, 3, 4]
t = bt.build([[1, 2], [3, 4, 5, 6], [7, 8]], 5)
last = bt.levels(bt.delete(t, 1, 5))[-1]
assert all(2 <= len(n) <= 4 for n in last), last

# chiave nodo interno = minimo del sotto-albero destro (20_esR pag.6)
t = bt.build([["A", "B"], ["C", "D"], ["E", "F"]], 5)
assert bt.levels(t)[0] == [["C", "E"]]

# ---- Schedule (slide 7/8 concorrenza) ----
# conflitto: transazioni diverse, stesso oggetto, almeno una scrittura
ops = ps.parse("r1(x), r2(x), w1(x), r1(y)")
c = ps.conflicts(ops)
assert (("r", 1, "x"), ("r", 2, "x")) not in c
assert (("r", 2, "x"), ("w", 1, "x")) in c

# teorema 2PL c CSR: controesempio ufficiale slide 8 pag.14 (CSR ma non 2PL)
s = ps.parse("r1(x), w1(x), r2(x), w2(x), r3(y), w1(y)")
assert ps.is_csr(s) and not ps.is_2pl(s)

# VSR via LEGGE_DA + SCRITTURE_FINALI: caso classico VSR-ma-non-CSR
assert ps.classify("r1(x), w2(x), w1(x), w3(x)") == "VSR"

# ---- Costo query (slide 10 Ottimizzazione II, pag.5/7) ----
assert pc.costo_nlj(1000, 50) == 1000 * 50
assert pc.costo_nlj_indice(1000, 3, 40000, 2000) == 1000 * (3 + 20)

print("AUDIT SLIDE OK: tutti i motori seguono le regole delle slide di teoria")
