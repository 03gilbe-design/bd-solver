#!/usr/bin/env python3
"""doc_schema.py — schema delle collezioni di documenti (JSON) da uno spec ER etichettato.
Esercizio tipo "ER etichettato -> schema documenti" (esami dal 2025, es. TURISTA/GRUPPO).

Mai esistito un motore per questo (GAPS.md punto 8): scritto sempre a mano e sempre
sbagliato quando testato. Regola deterministica (la stessa usata dal prof nei diagrammi
etichettati DOCxxx visti negli esami):

  - Le entita' marcate come RADICE (parametro roots) diventano collezioni di documenti.
  - Un'entita' X collegata a un documento-padre P si ANNIDA dentro P se X partecipa alla
    relazione con cardinalita' max=1 verso P (ogni istanza di X appartiene a UN solo P:
    puo' vivere dentro quel documento).
  - Se X partecipa con max=N (o e' essa stessa una radice), NON si annida: si mette un
    RIFERIMENTO (campo con la chiave di X).
  - L'annidamento e' ricorsivo: dentro un'entita' annidata si prosegue con le sue relazioni.

Output: dict {radice: struttura}, dove struttura = {"campi": [...], "annidati": {...},
"riferimenti": {...}} + un render JSON-like testuale per il PDF.
"""

def build(spec, roots):
    ent = spec["entita"]
    rel = spec.get("relazioni", {})

    def neighbors(e):
        out = []
        for r, d in rel.items():
            tra = d.get("tra", [])
            if e in tra:
                for o in tra:
                    if o != e:
                        out.append((r, o, d))
        return out

    def docof(e, visited):
        node = {"campi": list(ent[e].get("attr", [])), "annidati": {}, "riferimenti": {}}
        for r, o, d in neighbors(e):
            if o in visited:
                continue
            card_o = d["card"].get(o, [0, "N"])
            if card_o[1] == 1 and o not in roots:
                # o appartiene a UN solo e -> annidabile. Lista se e ne ha molti, oggetto se 1.
                many = d["card"].get(e, [0, "N"])[1] == "N"
                sub = docof(o, visited | {e})
                sub["_lista"] = many
                node["annidati"][o] = sub
            else:
                pk = ent[o].get("id", [["id"]])[0] if ent[o].get("id") else ["id"]
                node["riferimenti"][o] = [a for a in pk if a in ent[o].get("attr", [])] or list(pk)
        return node

    return {r: docof(r, {r}) for r in roots}

def labels(spec, roots):
    """Etichette in notazione UFFICIALE del prof — fonte VERIFICATA:
    slide `27b_ER_MongoDB_Embedding.pdf` (BasiDati_Unificata/Prof/Altri):
      X    = figlio incapsulato come OGGETTO SINGOLO nel padre (il padre ne ha al piu' 1)
      XRL  = figlio incapsulato come ARRAY nel padre (il padre ne ha molti)
      X_L  = incapsulamento con LOSS: figlio (0,1) verso il padre -> gli orfani
             (istanze senza padre) si PERDONO se si incapsula
      X_R  = incapsulamento con RIDONDANZA: relazione N:M -> lo stesso figlio viene
             DUPLICATO in ogni padre (alternativa: array di riferimenti, no duplicati)
    La cardinalita' del FIGLIO verso il padre decide la sicurezza ((1,1)=sicuro,
    (0,1)=loss, N:M=ridondanza); quella del PADRE decide oggetto singolo vs array."""
    rel = spec.get("relazioni", {})
    out = {}
    for r, d in rel.items():
        tra = d.get("tra", [])
        if len(tra) != 2:
            continue
        for padre in tra:
            if padre not in roots:
                continue
            figlio = [o for o in tra if o != padre][0]
            card_f = d["card"].get(figlio, [0, "N"])   # cardinalita' figlio verso la relazione
            card_p = d["card"].get(padre, [0, "N"])
            many_p = card_p[1] == "N" or (isinstance(card_p[1], int) and card_p[1] > 1)
            many_f = card_f[1] == "N" or (isinstance(card_f[1], int) and card_f[1] > 1)
            if many_f:                      # N:M -> ridondanza se incapsuli
                lab = "X_R"
            elif card_f == [1, 1]:          # sicuro
                lab = "XRL" if many_p else "X"
            elif card_f[0] == 0:            # (0,1): orfani -> loss
                lab = "X_L"
            else:
                lab = "XRL" if many_p else "X"
            # entita' raggiungibile da PIU' radici: tieni l'incapsulamento piu' SICURO
            # (X > XRL > X_L > X_R) - e' quello che si sceglie nella soluzione
            rank = {"X": 0, "XRL": 1, "X_L": 2, "X_R": 3}
            if figlio not in out or rank[lab] < rank[out[figlio]]:
                out[figlio] = lab
    return out

def render_text(docs):
    """Render JSON-like leggibile (per verbatim LaTeX)."""
    lines = []
    def emit(name, node, indent):
        pad = "  " * indent
        lines.append(f"{pad}{name}: {{" if name else f"{pad}{{")
        for c in node["campi"]:
            lines.append(f"{pad}  {c},")
        for o, sub in node["annidati"].items():
            opener = f"{o.lower()}: [" if sub.get("_lista") else f"{o.lower()}:"
            if sub.get("_lista"):
                lines.append(f"{pad}  {opener}")
                emit("", sub, indent + 2)
                lines.append(f"{pad}  ],")
            else:
                emit(f"{o.lower()}", sub, indent + 1)
        for o, keys in node["riferimenti"].items():
            lines.append(f"{pad}  {o.lower()}: {{ rif: {', '.join(keys)} }},")
        lines.append(f"{pad}}}")
    for name, node in docs.items():
        emit(f"DOC_{name}", node, 0)
        lines.append("")
    return "\n".join(lines)
