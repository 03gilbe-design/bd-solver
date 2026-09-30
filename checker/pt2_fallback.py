#!/usr/bin/env python3
"""Due tecniche per completare pezzi mancanti/poco chiari in una foto
d'esame, entrambe leggere (stdlib Python, zero download):

1. CONSTRAINT PROPAGATION (per numeri): se conosci la formula e il totale
   finale ma un pezzo intermedio e' illeggibile, risolvi l'equazione al
   contrario per quel pezzo. Tecnica standard in AI/CSP (constraint
   satisfaction problem): non indovini, DEDUCI dal vincolo.

2. FUZZY MATCHING (per testo/parole): se una parola letta dalla foto e'
   sporca (OCR incerto, scrittura a mano ambigua), la confronti con un
   vocabolario di parole GIA' VISTE nell'archivio (nomi tabelle, colonne,
   parole chiave SQL) e prendi la piu' vicina per distanza di edit
   (Levenshtein). Usa `difflib` dello stdlib - nessuna libreria esterna.

Entrambe vanno usate SOLO quando la foto e' davvero illeggibile in quel
punto - MAI al posto di guardare bene la foto prima.
"""
import difflib
import itertools


def deduci_valore_mancante(formula_nota, totale_osservato, dominio, tolleranza=0.01):
    """CONSTRAINT PROPAGATION: prova ogni valore del dominio (i candidati
    plausibili per il pezzo illeggibile) nella formula, tiene solo quelli
    che riproducono il totale osservato. Se resta UN solo candidato, quello
    e' dedotto con certezza (non indovinato: e' l'unico che soddisfa il
    vincolo). Se ne restano piu' di uno, dice quali sono - onesto, non sceglie
    a caso.

    formula_nota: funzione che prende un valore candidato e ritorna il totale
    totale_osservato: il numero che SI VEDE nella foto (es. il totale finale)
    dominio: lista di valori plausibili da provare (es. range di pagine 1..999,
             o le chiavi possibili di un B+-tree, o le transazioni T1..T9)
    """
    trovati = [v for v in dominio
              if abs(formula_nota(v) - totale_osservato) <= tolleranza]
    if len(trovati) == 1:
        return {"esito": "dedotto_certo", "valore": trovati[0]}
    if len(trovati) == 0:
        return {"esito": "nessun_candidato_torna", "valore": None}
    return {"esito": "ambiguo", "candidati": trovati}


def correggi_parola(parola_sporca, vocabolario, soglia=0.6):
    """FUZZY MATCHING: la parola letta male dalla foto (OCR/scrittura
    ambigua) confrontata con un vocabolario di parole GIA' VISTE
    nell'archivio (tabelle, colonne, parole chiave). Ritorna la piu' vicina
    se supera la soglia di somiglianza, altrimenti dice che non trova nulla
    di simile abbastanza (onesto, non forza un match debole)."""
    corrispondenze = difflib.get_close_matches(
        parola_sporca, vocabolario, n=3, cutoff=soglia)
    if not corrispondenze:
        return {"esito": "nessuna_corrispondenza", "parola": parola_sporca}
    punteggi = [(c, difflib.SequenceMatcher(None, parola_sporca, c).ratio())
               for c in corrispondenze]
    punteggi.sort(key=lambda x: -x[1])
    return {"esito": "trovata", "migliore": punteggi[0][0],
            "somiglianza": round(punteggi[0][1], 2),
            "alternative": [p[0] for p in punteggi[1:]]}


def _autotest():
    # --- test 1: constraint propagation su un caso B+-tree reale ---
    # "costo con indice = NR_sel x (profondita + qualcosa)" - se vedo il
    # totale ma la profondita' e' illeggibile nella foto, la deduco.
    def formula(prof):
        return 625 * (prof + 20)   # come nell'esercizio ottimizzazione verificato oggi
    r = deduci_valore_mancante(formula, totale_osservato=14375, dominio=range(1, 10))
    assert r["esito"] == "dedotto_certo" and r["valore"] == 3, r
    print("test 1 (constraint propagation) ok: profondita' dedotta =", r["valore"])

    # caso ambiguo: deve dirlo, non forzare una risposta
    def formula_ambigua(x):
        return x * 0   # sempre 0, qualunque x va bene: davvero ambiguo
    r2 = deduci_valore_mancante(formula_ambigua, 0, range(1, 5))
    assert r2["esito"] == "ambiguo", r2
    print("test 2 (caso ambiguo, onesto): ", r2["esito"], r2["candidati"])

    # caso senza soluzione: deve dirlo
    def formula_impossibile(x):
        return x + 1000
    r3 = deduci_valore_mancante(formula_impossibile, 5, range(1, 5))
    assert r3["esito"] == "nessun_candidato_torna", r3
    print("test 3 (nessun candidato torna): ok")

    # --- test 2: fuzzy matching su parole sporche viste in questa sessione ---
    vocabolario = ["CodiceSSN", "CFMedico", "Specialita", "PAZIENTE", "VISITA",
                  "MEDICO", "Regione", "checkpoint", "guasto"]
    casi = [("CodiceSN", "CodiceSSN"), ("CFMedco", "CFMedico"),
           ("Specialit", "Specialita"), ("chekpoint", "checkpoint")]
    for sporca, attesa in casi:
        r = correggi_parola(sporca, vocabolario)
        assert r["esito"] == "trovata" and r["migliore"] == attesa, (sporca, r)
        print("fuzzy: '%s' -> '%s' (somiglianza %.2f)"
             % (sporca, r["migliore"], r["somiglianza"]))

    # caso senza corrispondenza vera: deve dirlo, non forzare
    r = correggi_parola("xyzqwerty", vocabolario)
    assert r["esito"] == "nessuna_corrispondenza", r
    print("fuzzy (nessuna corrispondenza vera): ok, non ha forzato nulla")

    print("\nTUTTI I TEST OK")


if __name__ == "__main__":
    _autotest()
