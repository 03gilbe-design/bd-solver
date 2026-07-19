#!/usr/bin/env python3
"""reverse_er.py — dato uno schema RELAZIONALE (tabelle+PK+FK), euristica deterministica
per risalire allo schema ER concettuale. E' l'esercizio (c) tipico della I parte:
"Dato lo schema relazionale seguente [...] riportare lo schema concettuale ER".

REGOLE (dedotte dal caso reale R1/R2/R3/R4 fornito dall'utente):
  - Tabella senza FK uscenti che nessuna FK referenzia con chiave intera -> ENTITA' root.
  - FK il cui insieme di colonne == l'INTERA PK della tabella -> relazione (1,1)-(0,1)
    (spesso ISA/estensione: la tabella figlia "e'" un'estensione 1:1 del padre).
  - FK le cui colonne sono un SOTTOINSIEME PROPRIO della PK (chiave composta da piu' FK)
    -> la tabella e' una RELAZIONE N-aria fra le entita' referenziate; le colonne PK non-FK
    diventano identificatore parziale/attributo della relazione.
  - FK su colonna NON in PK, nullable -> relazione 1:N, cardinalita' (0,1) sul lato N.
  - FK su colonna NON in PK, NOT NULL -> relazione 1:N, cardinalita' (1,1) sul lato N.

FONTE: confermato contro le slide teoria del prof (lezione.pdf) E contro trascrizioni
manuali delle soluzioni ufficiali di 3 esami reali (Raccolta_Biglietti_Appunti/
Trascrizioni_ER/Trascrizione_12_22_{A,B,C}.md). Regole verificate (non solo dedotte):
  - FK fuori dalla PK, nullable/NOT NULL         -> 1:N, cardinalita' da nullable
  - FK = 1 SOLA, copre PARTE della PK            -> IDENTIFICAZIONE ESTERNA (entita' debole),
                                                     cardinalita' FISSA debole=(1,1) owner=(0,N)
  - FK = 1 SOLA, copre TUTTA la PK               -> relazione 1:1/estensione (1,1)-(0,1)
  - FK = 2+ , insieme coprono la PK (N-aria)     -> relazione N-aria pura, cardinalita'
                                                     DEFAULT (0,N) su OGNI lato
  - FK multi-colonna (2+ col) verso un target    -> quelle colonne SONO la PK del target
                                                     (corregge un parser che avesse assunto
                                                     PK sbagliata)
Storico correzioni in questa sessione (bug reali trovati testando su casi veri, non ipotetici):
  1. Il ramo "1 sola FK parziale" non era gestito (silenziosamente ignorato) -> fixato.
  2. Relazioni N-arie non avevano cardinalita' di default -> aggiunto (0,N) su ogni lato.
  3. PK dedotta solo come "primo attributo" quando non specificata -> corretta da FK
     multi-colonna quando disponibile.

LIMITE ONESTO RESIDUO: le 4 varianti di copertura ISA (totale/parziale, esclusiva/
sovrapposta, citate in lezione.pdf) non sono ancora distinte dal motore diretto (er.py),
vedi TEORIA_CHECKLIST.md. Il caso "FK singola parziale" assume SEMPRE identificazione
esterna: se in realta' fosse un'altra semantica (raro) va controllato a mano. Non
sostituisce il ragionamento sul testo se il testo e' disponibile.
"""

def _fix_pk_from_multicol_fk(tables):
    """Se una FK usa 2+ colonne verso un target, quelle colonne SONO (quasi sempre) la PK
    del target - una FK deve referenziare una chiave candidata. Corregge pk[target] se il
    parser di base l'aveva sbagliata (es. assunta = primo attributo). Confermato su caso
    reale: R4.(B,E)->R2 significa che la PK vera di R2 e' (B,E), non solo B (verificato
    contro trascrizione manuale della soluzione ufficiale, non solo dedotto)."""
    for name, t in tables.items():
        for cols, target in t.get("fk", []):
            if len(cols) >= 2 and target in tables:
                tables[target]["pk"] = list(cols)
    return tables

def infer_er(tables):
    """tables: {name: {'pk': [...], 'fk': [(cols, target), ...], 'attrs': [...]}}
    Ritorna lista di frasi (spiegazione) + struttura {entita: [...], relazioni: [...]}."""
    tables = _fix_pk_from_multicol_fk(tables)
    notes = []
    entita, relazioni = [], []
    for name, t in tables.items():
        pk = set(t["pk"])
        fk_full = [f for f in t["fk"] if set(f[0]) == pk]          # FK = intera PK
        fk_partial = [f for f in t["fk"] if set(f[0]) < pk]         # FK = parte della PK
        fk_normal = [f for f in t["fk"] if not (set(f[0]) & pk)]    # FK fuori dalla PK

        if len(fk_partial) >= 2:
            # chiave composta da 2+ FK -> relazione N-aria fra le entita' referenziate.
            # cardinalita' default (0,N) su OGNI lato: confermato (non solo dedotto) contro
            # trascrizione della soluzione ufficiale 12-22_C, dove R4 (ternaria pura, PK=
            # solo le 3 FK, nessun altro attributo di chiave) ha tutti e 3 i lati (0,N).
            others = [f[1] for f in fk_partial]
            relazioni.append({"nome": name, "tra": others, "grado": len(others),
                               "card": {o: [0, "N"] for o in others}})
            notes.append(f"{name}: PK composta da FK verso {others} -> RELAZIONE "
                         f"{'N:N' if len(others)==2 else f'{len(others)}-aria'} fra queste entita'"
                         f" (non e' un'entita' a se'), cardinalita' default (0,N) su ogni lato.")
            extra_pk = pk - {c for f in fk_partial for c in f[0]}
            if extra_pk:
                notes.append(f"  attributi propri della relazione (chiave oltre le FK): {sorted(extra_pk)}")
        else:
            entita.append(name)
            notes.append(f"{name}: ENTITA' (PK propria {sorted(pk)}).")
            for cols, target in fk_partial:
                # ESATTAMENTE 1 FK che copre solo PARTE della PK (non tutta, non 2+) ->
                # IDENTIFICAZIONE ESTERNA (entita' debole): la parte extra della PK e' la
                # chiave parziale propria, la FK e' l'id esterno. Cardinalita' FISSA
                # (debole sempre (1,1) verso l'owner, owner sempre (0,N)) - trovato bug:
                # prima questo ramo non era gestito affatto (fk_partial ignorata quando
                # len==1), silenziosamente sbagliato. Confermato contro trascrizione
                # ufficiale 12-22_A: R2(A,D) PK=(A,D), FK solo su A -> R1(0,N)--R2(1,1).
                notes.append(f"  FK({','.join(cols)}) e' parte della PK {sorted(pk)} (non tutta, 1 sola FK) "
                              f"-> IDENTIFICAZIONE ESTERNA: {name} e' entita' DEBOLE, "
                              f"cardinalita' {name}:(1,1) fisso, {target}:(0,N) fisso.")
                relazioni.append({"nome": f"{name}_{target}_ident", "tra": [name, target], "grado": 2,
                                   "card": {name: [1, 1], target: [0, "N"]}})
            for cols, target in fk_full:
                notes.append(f"  FK({','.join(cols)})={sorted(pk)} verso {target}: "
                              f"e' l'INTERA chiave -> relazione (1,1)-(0,1) con {target} "
                              f"(estensione/ISA 1:1, {name} 'e' un' {target} con dati aggiuntivi).")
                relazioni.append({"nome": f"{name}_{target}_1a1", "tra": [name, target], "grado": 2,
                                   "card": {name: [1, 1], target: [0, 1]}})
            for cols, target in fk_normal:
                nullable = any(c in t.get("nullable", []) for c in cols)
                card_n = [0, 1] if nullable else [1, 1]
                notes.append(f"  FK({','.join(cols)}) verso {target}, "
                              f"{'nullable' if nullable else 'NOT NULL'} -> relazione 1:N, "
                              f"cardinalita' lato {name}: ({card_n[0]},{card_n[1]}), lato {target}: (0,N).")
                relazioni.append({"nome": f"{name}_{target}", "tra": [name, target], "grado": 2,
                                   "card": {name: card_n, target: [0, "N"]}})
    return notes, {"entita": entita, "relazioni": relazioni}


def _parse_schema_text(text):
    """Parser minimale per il formato usato negli esami: R1(A, C), R2(A, D)... con
    'R2.A -> R1' come vincoli. Sufficiente per i casi visti nel corpus, non un parser SQL."""
    import re
    tables = {}
    for m in re.finditer(r"(\w+)\(([^)]+)\)", text):
        name, body = m.group(1), m.group(2)
        cols, nullable = [], []
        for c in body.split(","):
            c = c.strip().rstrip("*")
            if c.endswith("*") or "*" in c:
                nullable.append(c.replace("*", ""))
            cols.append(c.replace("*", ""))
        pk = [cols[0]] if cols else []  # euristica: primo attributo = PK se non specificato altrove
        tables[name] = {"pk": pk, "fk": [], "attrs": cols, "nullable": nullable}
    for m in re.finditer(r"(\w+)\.(\w+)\s*(?:->|→|®)\s*(\w+)", text):
        src, col, target = m.groups()
        if src in tables:
            tables[src]["fk"].append(([col], target))
            if col not in tables[src]["pk"]:
                tables[src]["pk"].append(col)  # se e' FK ed e' nel testo come parte-chiave, aggiungila
    return tables
