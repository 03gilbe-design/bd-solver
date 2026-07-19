"""Test pt2_costo contro le soluzioni UFFICIALI di
lesson_12_03_esercitazione_ottimizzazione_soluzioni.pdf.
Ottimizzazione 1 punto (1): 780+180+150+9000 = 10110.
Ottimizzazione 2: join senza indice = 475*155; con indice = 475*(3+20) = 10925.
(Il punto (2) di Ottimizzazione 1 ha refusi aritmetici nel PDF: si testano le formule.)"""
import pt2_costo as pc

# Ottimizzazione 1, punto (1)
r = pc.solve(np_outer=150, nr_outer=900, val_sel_outer=18,
             np_inner=780, pagine_sel_inner=180,
             nr_sel_inner=19800 / 50, val_join_inner=90,
             prof_indice=2)
assert r["nr_sel_esterna"] == 50, r
assert r["totale"] == 780 + 180 + 150 + 9000 == 10110, r["totale"]
# punto (2): formula ufficiale 50*(2+ceil(396/90)) = 50*(2+5) = 350
assert pc.costo_nlj_indice(50, 2, 19800 / 50, 90) == 350

# Ottimizzazione 2 (aritmetica ufficiale corretta)
assert pc.nr_sel(1900, 4) == 475
assert pc.costo_nlj(475, 155) == 475 * 155
assert pc.costo_nlj_indice(475, 3, 38000, 1900) == 10925

# Esame 23/06/2025 es. f (calcolo del motore, coerente col modello)
r = pc.solve(np_outer=250, nr_outer=15500, val_sel_outer=10,
             np_inner=2500, pagine_sel_inner=1750,
             nr_sel_inner=201500, val_join_inner=15500,
             prof_indice=3)
assert r["nr_sel_esterna"] == 1550
assert r["totale"] == 2500 + 1750 + 250 + 1550 * 1750 == 2717000, r["totale"]
assert r["totale_indice"] == 2500 + 1750 + 250 + 1550 * (3 + 13) == 29300, r["totale_indice"]

# Caso interna_selezionata=False (nessun WHERE sull'interna, es. esame 21/04/2022
# PAZIENTE join VISITA senza filtro su VISITA): formula BASE della slide teoria
# "10 - Ottimizzazione Parte II" pag.5-7: costo_join = NP(outer)+NR(outer_sel)*NP(inner),
# senza passo di scrittura selezione (che non esiste se non c'e' filtro).
r = pc.solve(np_outer=140, nr_outer=13500, val_sel_outer=15,
             np_inner=2100, pagine_sel_inner=2100,
             nr_sel_inner=270000, val_join_inner=13500, prof_indice=3,
             interna_selezionata=False)
assert r["nr_sel_esterna"] == 900
assert r["totale"] == 140 + 900 * 2100 == 1890140, r["totale"]
assert r["totale_indice"] == 140 + 900 * (3 + 20) == 20840, r["totale_indice"]

for s in r["steps"] + r["steps_indice"][3:]:
    print(s)
print("TUTTI I TEST OK")
