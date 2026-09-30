"""controllo_trascrizione: lo spec giusto passa; l'errore del 14/09 (<> trascritto come =) viene preso;
un numero sbagliato e due trascrizioni diverse vengono presi. Testo sintetico (i testi d'esame non sono nel repo)."""
import copy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from controllo_trascrizione import contro_testo, due_trascrizioni

TESTO = """e) Gestore dell'affidabilita' LOG: DUMP; B(T1), B(T2), U(T1,O1,B1,A1), CK(T1,T2), C(T1), guasto
f) S: r1(x), w2(x), r2(y), w1(y)
g) WHERE P.Regione <> 'Lombardia' ... il risultato viene salvato in 100 pagine della memoria secondaria.
NP(VISITA) = 2000, NP(PAZIENTE) = 130, NR(VISITA) = 250000, NR(PAZIENTE) = 12500
VAL(Regione, PAZIENTE) = 20, VAL(CodiceSSN, VISITA) = 12500, indice B+-tree profondita' 3
h) B+-tree (fan-out=5) foglie 1 4 9 12 14 18 20 ; inserimento del valore chiave 22"""
SPEC = {"esercizi": [
    {"tipo": "ripresa", "id": "e", "log": "B(T1), B(T2), U(T1,O1,B1,A1), CK(T1,T2), C(T1)"},
    {"tipo": "schedule", "id": "f", "schedule": "r1(x), w2(x), r2(y), w1(y)"},
    {"tipo": "costo", "id": "g", "parametri": {"np_outer": 130, "nr_outer": 12500, "val_sel_outer": 20,
     "np_inner": 2000, "pagine_sel_inner": 2000, "nr_sel_inner": 250000, "val_join_inner": 12500,
     "prof_indice": 3, "interna_selezionata": False, "outer_pagine_scritte": 100, "selezione_diverso": True}},
    {"tipo": "btree", "id": "h", "fanout": 5, "foglie": [[1, 4, 9], [12, 14], [18, 20]],
     "operazioni": [{"op": "insert", "key": 22}]}]}

ok, err = contro_testo(SPEC, TESTO)
assert not err and len(ok) == 4, (ok, err)

chat = copy.deepcopy(SPEC)                      # errore reale del 14/09
del chat["esercizi"][2]["parametri"]["selezione_diverso"]
assert any("selezione_diverso" in e for e in contro_testo(chat, TESTO)[1])

sbagliato = copy.deepcopy(SPEC)                 # numero trascritto male
sbagliato["esercizi"][2]["parametri"]["np_inner"] = 2100
assert any("np_inner=2100" in e for e in contro_testo(sbagliato, TESTO)[1])

log_male = copy.deepcopy(SPEC)                  # record del log mancante
log_male["esercizi"][0]["log"] = "B(T1), U(T1,O1,B1,A1), CK(T1,T2), C(T1)"
assert contro_testo(log_male, TESTO)[1]

scambio = copy.deepcopy(SPEC)                   # NP scambiati: il testo non lo vede, la doppia trascrizione si'
p = scambio["esercizi"][2]["parametri"]
p["np_outer"], p["np_inner"] = p["np_inner"], p["np_outer"]
assert not contro_testo(scambio, TESTO)[1], "limite noto: presenza dei numeri, non il loro ruolo"
assert due_trascrizioni(SPEC, scambio), "la doppia trascrizione deve vedere lo scambio"
assert not due_trascrizioni(SPEC, copy.deepcopy(SPEC))
print("TUTTI I TEST OK")
