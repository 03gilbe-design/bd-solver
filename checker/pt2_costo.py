#!/usr/bin/env python3
"""pt2_costo.py — esercizio "Ottimizzazione" (costo query) della III prova.
Deterministico, stdlib puro.

FONTE PRIMARIA VERIFICATA: slide teoria del corso "10 - Ottimizzazione di
interrogazioni - Parte II.pdf", sezione "Nested-Loop JOIN: costo" (pag.5) e
"Nested-Loop JOIN con indice B+-tree: costo" (pag.7) — non solo un esercizio
isolato, e' la formula del libro di testo:
    NLJ (1 buffer per R, 1 per S), R esterna, S interna:
        costo_join = NP(R) + NR(R) * NP(S)
    NLJ con indice B+-tree di profondita' d sull'attributo di join di S:
        costo_join = NP(R) + NR(R) * (d + NR(S)/VAL(attributo_join, S))
Nel nostro modello NP(R) del join e' gia' contato a parte come "scansione
esterna" (spesso a costo 0 perche' il testo dice "mantenuto nel buffer"), quindi
costo_nlj/costo_nlj_indice qui sotto implementano solo il termine
NR(R_sel) * NP(S_sel) [risp. NR(R_sel)*(d+NR(S_sel)/VAL)].
Riscontro aggiuntivo su esercizio interamente risolto:
lesson_12_03_esercitazione_ottimizzazione_soluzioni.pdf, Ottimizzazione 2:
475*(3+20)=10925 esatto (Ottimizzazione 1 punto (2) nel PDF ha refusi
aritmetici nel numero finale — non usarlo come riferimento, solo la formula).

CASI DI SELEZIONE SULLA TABELLA INTERNA (parametro interna_selezionata):
- True (default, caso standard d'esame "il risultato della selezione viene
  salvato in N pagine"): si scansiona la tabella interna per applicare il
  filtro (costo NP(interna)) e si scrive il risultato ridotto su disco (costo
  pagine_sel_inner), poi il JOIN rilegge quella versione ridotta.
- False (nessun WHERE sulla tabella interna, es. esame 21/04/2022 dove VISITA
  non ha alcun filtro): NON esiste selezione da scansionare ne' da scrivere —
  si salta gli step (a)/(b) e il JOIN usa NP(interna) pieno direttamente,
  come da formula base della slide. Impostare pagine_sel_inner=np_inner e
  nr_sel_inner=nr_inner in questo caso (nessuna riduzione).

LIMITE NOTO (scoperto 2026-07-19 su Esercitazione_2015-soluzioni.pdf, esame con
join a 3 tabelle RICETTA-COMPOSIZIONE-INGREDIENTE): questo motore gestisce SOLO
join a 2 tabelle. Con 3+ tabelle la formula ufficiale si estende naturalmente
(costo = NP(prima) + NR(prima_sel)*NP(seconda)*NP(terza), con indice sostituire
l'ultimo NP con [d+NR_sel/VAL]) ma NON e' implementata: solve() qui sotto
accetta solo outer+inner. Se un esame ha join a 3 tabelle, calcolare a mano
con la stessa logica (moltiplicare per NP di ogni tabella aggiuntiva in catena)
o estendere solve() con una lista di tabelle interne invece di una singola.

CASO SIMMETRICO: selezione sull'ESTERNA scritta su disco (parametro
outer_pagine_scritte, es. esame 08/06/2023 es.f: "il risultato viene salvato in
10 pagine" per PAZIENTE che e' la tabella ESTERNA del join, mentre VISITA
[interna] non ha filtro). Normalmente l'esterna selezionata si assume
"mantenuta nel buffer" (costo aggiuntivo 0); se il testo dice esplicitamente
che viene scritta su disco, passare outer_pagine_scritte = pagine indicate."""
import math

def nr_sel(nr, val):
    """tuple stimate dopo selezione su attributo con VAL valori distinti"""
    return nr // val if nr % val == 0 else nr / val

def costo_scan(np_table):
    return np_table

def costo_nlj(nr_outer_sel, np_inner):
    return nr_outer_sel * np_inner

def costo_nlj_indice(nr_outer_sel, prof, nr_inner_sel, val_join):
    return nr_outer_sel * (prof + math.ceil(nr_inner_sel / val_join))

def solve(np_outer, nr_outer, val_sel_outer,
          np_inner, pagine_sel_inner, nr_sel_inner, val_join_inner,
          prof_indice=None, interna_selezionata=True, outer_pagine_scritte=0):
    """Schema d'esame standard (come es. f 23/06/2025 e Ottimizzazione 1):
    - scansione interna completa + scrittura selezione su disco (pagine_sel_inner)
      SOLO se interna_selezionata=True (altrimenti nessun WHERE sull'interna:
      si salta questo passo e si usa np_inner pieno nel join, formula base slide)
    - scansione esterna, selezione tenuta in buffer
    - NLJ esterna x (selezione interna materializzata); variante con indice sull'interna.
    Ritorna dict con passi e totali (senza e con indice)."""
    steps = []
    pre = 0
    if interna_selezionata:
        a = costo_scan(np_inner)                  # scansione tabella interna
        b = pagine_sel_inner                      # scrittura selezione interna
        steps += [f"(a) scansione interna = NP = {a}",
                  f"(b) scrittura selezione interna = {b}"]
        pre = a + b
        np_join_inner = pagine_sel_inner
    else:
        steps.append("(nessun filtro sulla tabella interna: niente selezione da scrivere, "
                      f"il JOIN legge direttamente NP(interna) = {np_inner})")
        np_join_inner = np_inner
    c = costo_scan(np_outer)                      # scansione tabella esterna
    steps.append(f"(c) scansione esterna = NP = {c}")
    if outer_pagine_scritte:
        pre += outer_pagine_scritte
        steps.append(f"(c-bis) scrittura selezione esterna = {outer_pagine_scritte}")
    ns = nr_sel(nr_outer, val_sel_outer)
    d = costo_nlj(ns, np_join_inner)
    steps.append(f"(d) JOIN NLJ = NR_sel_esterna x NP_sel_interna = {ns:g} x {np_join_inner} = {d}")
    out = {"steps": steps, "totale": pre + c + d, "nr_sel_esterna": ns}
    if prof_indice is not None:
        tpv = math.ceil(nr_sel_inner / val_join_inner)
        e = costo_nlj_indice(ns, prof_indice, nr_sel_inner, val_join_inner)
        steps_idx = steps[:-1] + [
            f"(e) JOIN con indice = {ns:g} x ({prof_indice} + ceil({nr_sel_inner}/{val_join_inner})) "
            f"= {ns:g} x ({prof_indice}+{tpv}) = {e:g}"]
        out["steps_indice"] = steps_idx
        out["totale_indice"] = pre + c + e
    return out
