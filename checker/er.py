#!/usr/bin/env python3
"""
er.py - Motore deterministico per esami Basi di Dati parte 1 (prof. Belussi, UniVR).

Input: uno schema ER descritto in JSON strutturato (vedi SCHEMA sotto).
Output:
  --check    valida lo schema (identificatori, cardinalita, FK) -> exit!=0 se errori
  --tikz     genera il diagramma ER in TikZ (stile Chen/Belussi)
  --rel      deriva lo schema RELAZIONALE con l'algoritmo standard di traduzione
  --all      check + tikz + rel

Perche esiste: il modello NON disegna a mano. Produce lo spec ER; il codice
deterministico rende SEMPRE il diagramma graficamente corretto e deriva la
traduzione relazionale con regole fisse. Cosi si vede la differenza ER<->logico
e si e' costretti a specificare cardinalita e identificatori (il check li pretende).

FORMATO SPEC (JSON):
{
  "entita": {
    "VOLO": {"attr": ["codice", "data", "ora", "ritardo", "durata"],
             "id": [["codice","data"]]},          # lista di identificatori (ognuno = lista di attr/relazioni)
    "AEROPORTO": {"attr": ["sigla","nome","citta","nazione"], "id": [["sigla"]]}
  },
  "relazioni": {
    "DESTINAZIONE": {"tra": ["VOLO","AEROPORTO"],
                     "card": {"VOLO": [1,1], "AEROPORTO": [0,"N"]},
                     "attr": []}
  },
  "isa": [ {"padre":"DIPENDENTE","figli":["PILOTA","ADDETTO"],"copertura":"esclusiva"} ]
}

card = (min, max). max puo' essere 1 o "N".
Identificatore esterno: metti nel campo id il NOME di una relazione (es ["codice", "DESTINAZIONE"]).
"""
import json, sys, argparse, os

# ---------------------------------------------------------------- validazione
def check(spec):
    errs = []
    ent = spec.get("entita", {})
    rel = spec.get("relazioni", {})
    if not ent:
        errs.append("nessuna entita definita")
    # figli ISA: ereditano l'identificatore dal padre
    figlio_di = {}
    for h in spec.get("isa", []):
        for f in h.get("figli", []):
            figlio_di[f] = h["padre"]
    # ogni entita ha almeno un identificatore (i figli ISA lo ereditano dal padre)
    for e, d in ent.items():
        ids = d.get("id", [])
        if not ids and e not in figlio_di:
            errs.append(f"entita '{e}' senza identificatore")
        # attributi validi per l'id: propri, relazioni, o (se figlio ISA) la chiave del padre
        valid = set(d.get("attr", [])) | set(rel)
        if e in figlio_di:
            valid |= set(ent.get(figlio_di[e], {}).get("attr", []))
        for idk in ids:
            for part in idk:
                if part not in valid and part not in rel:
                    errs.append(f"identificatore di '{e}' usa '{part}' non fra i suoi attributi ne una relazione")
                elif part in rel:
                    # identificazione esterna: la relazione identificante deve essere (x,1) sul lato di 'e'
                    c = rel[part].get("card", {}).get(e)
                    if c and c[1] != 1:
                        errs.append(f"identificazione esterna: '{e}' usa relazione '{part}' ma il suo lato ha max={c[1]}, deve essere 1 (regola (1,1))")
    # ogni relazione: 2+ entita partecipanti esistenti, cardinalita per ognuna
    for r, d in rel.items():
        tra = d.get("tra", [])
        if len(tra) < 2:
            errs.append(f"relazione '{r}' collega meno di 2 entita")
        for ka in d.get("key_attr", []):
            if ka not in d.get("attr", []):
                errs.append(f"relazione '{r}': key_attr '{ka}' non e' fra i suoi attributi propri")
        for e in tra:
            if e not in ent:
                errs.append(f"relazione '{r}' riferisce entita inesistente '{e}'")
        card = d.get("card", {})
        for e in tra:
            if e not in card:
                errs.append(f"relazione '{r}' manca cardinalita per '{e}'")
            else:
                mn, mx = card[e]
                # cardinalita' numeriche arbitrarie AMMESSE (GAPS/biblioteche: "almeno 2
                # sottocategorie" = min 2, "al massimo due" = max 2). Ai fini della
                # TRADUZIONE: min>0 = obbligatorio, max>1 o "N" = lato molti; il vincolo
                # numerico esatto va comunque annotato a parole nella soluzione.
                if not (isinstance(mn, int) and mn >= 0):
                    errs.append(f"relazione '{r}' entita '{e}': min deve essere un intero >=0 (trovato {mn})")
                if not (mx == "N" or (isinstance(mx, int) and mx >= 1)):
                    errs.append(f"relazione '{r}' entita '{e}': max deve essere intero >=1 o 'N' (trovato {mx})")
    # ISA: padre e figli esistono
    for h in spec.get("isa", []):
        if h["padre"] not in ent:
            errs.append(f"ISA padre '{h['padre']}' inesistente")
        for f in h["figli"]:
            if f not in ent:
                errs.append(f"ISA figlio '{f}' inesistente")
    return errs

# ---------------------------------------------------------------- traduzione relazionale
def _padre_di(spec, e):
    for h in spec.get("isa", []):
        if e in h.get("figli", []):
            return h["padre"]
    return None

def _pk_attrs(spec, e):
    """attributi della chiave primaria di e (primo id). Risolve id esterni ricorsivamente.
    Se e' un figlio ISA (strategia 'figli') la sua PK reale e' quella importata dal padre via
    FK, anche se nello spec l'id elenca un attributo del padre (es. 'matricola') - senza questo
    caso speciale _pk_attrs cade nel fallback sintetico sbagliato (bug trovato su scuola_sci)."""
    d = spec["entita"][e]
    ids = d.get("id", [])
    padre = _padre_di(spec, e)
    if not ids:
        if padre:
            return [f"{padre.lower()}_{a}" for a in _pk_attrs(spec, padre)]
        return [f"{e.lower()}_id"]
    out = []
    for part in ids[0]:
        if part in spec["entita"][e].get("attr", []):
            out.append(part)
        elif part in spec.get("relazioni", {}):
            # id esterno: prende la PK dell'altra entita della relazione
            other = [x for x in spec["relazioni"][part]["tra"] if x != e]
            if other:
                out += [f"{other[0].lower()}_{a}" for a in _pk_attrs(spec, other[0])]
        elif padre and part in spec["entita"][padre].get("attr", []):
            # id ereditato dal padre ISA (es. MAESTRO_SCI id=[["matricola"]], matricola e' di DIPENDENTE)
            out += [f"{padre.lower()}_{a}" for a in _pk_attrs(spec, padre)]
    return out or [f"{e.lower()}_id"]

def _is_many(mx):
    """max='N' o intero >1 -> lato 'molti' ai fini della traduzione (es. (1,2) e' molti)."""
    return mx == "N" or (isinstance(mx, int) and mx > 1)

def translate(spec):
    """Ritorna lista di tabelle: dict(name, cols=[(nome,pk,nullable)], fk=[(cols,ref)])."""
    ent, rel = spec["entita"], spec.get("relazioni", {})
    tables = {}
    # relazioni usate per IDENTIFICAZIONE ESTERNA (compaiono nell'id[0] di un'entita):
    # la loro FK e' gia' generata qui sotto -> vanno saltate nel loop relazioni (2), altrimenti
    # la stessa colonna FK verrebbe aggiunta due volte (bug trovato testando scuola_sci).
    identifying_rels = set()
    # 1) una tabella per entita
    for e, d in ent.items():
        pk = _pk_attrs(spec, e)
        opt = set(d.get("opt", []))          # attributi opzionali -> nullable (es. Ritardo*)
        cols = [(a, a in pk, a in opt) for a in d.get("attr", [])]
        fks = []
        # aggiungi colonne id esterno che non sono attributi propri + registra il vincolo FK
        for a in pk:
            if a not in d.get("attr", []):
                cols.insert(0, (a, True, False))
        for idk in d.get("id", [[]])[:1]:
            for part in idk:
                if part in rel:
                    identifying_rels.add(part)
                    other = [x for x in rel[part]["tra"] if x != e]
                    if other:
                        fkcols = [f"{other[0].lower()}_{a}" for a in _pk_attrs(spec, other[0])]
                        fks.append((fkcols, other[0]))
                    for extra in rel[part].get("attr", []):     # attributi propri della relazione identificante (es. 'voto')
                        cols.append((extra, False, extra in set(rel[part].get("opt_attr", []))))
        tables[e] = {"name": e, "cols": cols, "fk": fks}
        # attributi MULTIVALORE ("multi": [...]) -> tabella separata ENTITA_ATTR(pk, valore),
        # regola standard di traduzione. Gap reale: l'attributo "autori" di LIBRO era stato
        # PERSO in un esame vero perche' il motore non supportava i multivalore e lo spec
        # scritto a mano l'aveva dimenticato (GAPS.md punto 9, confronto sessione Termux).
        for m in d.get("multi", []):
            mt = f"{e}_{m.upper()}"
            mcols = [(f"{e.lower()}_{a}", True, False) for a in pk] + [(m, True, False)]
            tables[mt] = {"name": mt, "cols": mcols,
                          "fk": [([f"{e.lower()}_{a}" for a in pk], e)]}
    # 2) relazioni binarie (saltando quelle gia' tradotte come identificazione esterna sopra)
    for r, d in rel.items():
        if r in identifying_rels:
            continue
        tra = d.get("tra", [])
        card = d.get("card", {})
        if len(tra) != 2:
            # n-aria: tabella propria di default, MA se esattamente un lato ha max=1,
            # la relazione si ASSORBE in quell'entita' (come nel caso binario 1:N) invece
            # di generare una tabella - bug reale trovato: prima creavo sempre tabella
            # ignorando la cardinalita'. Fonte: Agente_A_Algebra_2.md (26/02/2014), caso
            # ternaria A-B-E con E:(0,1) -> E assorbe le FK di A e B invece di tabella R.
            ones = [e for e in tra if card.get(e, [0, "N"])[1] == 1]
            if len(ones) == 1:
                _add_fk_multi(spec, tables, host=ones[0], targets=[e for e in tra if e != ones[0]], rel=d)
            else:
                _rel_table(spec, tables, r, d)
            continue
        a, b = tra
        # max numerico >1 (es. "al massimo 2") = lato MOLTI ai fini della traduzione
        many_a, many_b = _is_many(card[a][1]), _is_many(card[b][1])
        if many_a and many_b:
            _rel_table(spec, tables, r, d)          # N:N -> tabella
        elif not many_a and many_b:
            _add_fk(spec, tables, host=a, target=b, rel=d, relname=r)   # FK sul lato "1" (=a), referenzia b
        elif many_a and not many_b:
            _add_fk(spec, tables, host=b, target=a, rel=d, relname=r)
        else:  # 1:1 -> FK sul lato con partecipazione totale (min>=1), default a
            host = a if card[a][0] >= 1 else b
            target = b if host == a else a
            _add_fk(spec, tables, host=host, target=target, rel=d, relname=r)
    # 3) generalizzazioni (ISA)
    for h in spec.get("isa", []):
        _translate_isa(spec, tables, h)
    # mantiene ordine: entita, poi relazioni-tabella (gia' inserite in tables)
    return list(tables.values())

def _translate_isa(spec, tables, h):
    """3 strategie di ristrutturazione ISA (tutte osservate in soluzioni ufficiali reali):
       - 'figli' (default): ogni figlio -> tabella propria con FK verso il padre. Il padre resta.
       - 'padre': accorpa i FIGLI nel padre (attr figli diventano nullable + discriminante
         'tipo'); le tabelle figlie spariscono, il padre resta.
       - 'accorpa_nei_figli': il PADRE sparisce, ogni figlio assorbe i SUOI attributi
         (nessuna FK, nessuna tabella padre). Trovato nella soluzione ufficiale di scuola_sci
         ("accorpo la generalizzazione con radice in DIPENDENTE nelle entita' figlie") - e' il
         caso SIMMETRICO a 'padre' e mancava."""
    padre, figli = h["padre"], h["figli"]
    strat = h.get("strategia", "figli")
    ppk = _pk_attrs(spec, padre)
    if strat == "accorpa_nei_figli":
        padre_cols = [(n, pk, nul) for n, pk, nul in tables[padre]["cols"]]
        for f in figli:
            if f in tables:
                proprie = [c for c in tables[f]["cols"] if not c[1]]  # scarta la pk sintetica del figlio
                tables[f]["cols"] = padre_cols + proprie
                tables[f]["fk"] = []  # nessuna FK: il padre e' sparito, gli attributi sono suoi ora
        del tables[padre]
        return
    if strat == "padre":
        for f in figli:
            if f in tables:
                for name, pk, nul in tables[f]["cols"]:
                    if not pk:                      # porta solo gli attr non-chiave, nullable
                        tables[padre]["cols"].append((name, False, True))
                del tables[f]
        tables[padre]["cols"].append(("tipo", False, False))   # discriminante
    else:  # figli
        for f in figli:
            if f in tables:
                fkcols = [f"{padre.lower()}_{a}" for a in ppk]
                # la PK del figlio diventa la PK importata dal padre (+ eventuali attr propri gia' presenti)
                newcols = [(c, True, False) for c in fkcols]
                for name, pk, nul in tables[f]["cols"]:
                    if not pk:                      # scarta la vecchia pk sintetica se c'era
                        newcols.append((name, False, nul))
                tables[f]["cols"] = newcols
                tables[f]["fk"].append((fkcols, padre))

def _add_fk(spec, tables, host, target, rel, relname):
    tpk = _pk_attrs(spec, target)
    nullable = rel["card"][host][0] == 0
    # "colname" opzionale: prefisso colonna FK custom al posto del nome-entita' target.
    # Serve per i RUOLI (GAPS.md punto 1): CAP e VICE sono due relazioni distinte verso la
    # stessa entita' PILOTA - senza prefisso diverso le colonne collidono (pilota_matricola x2).
    prefix = rel.get("colname", target.lower())
    fkcols = [f"{prefix}_{a}" for a in tpk]
    for c in fkcols:
        tables[host]["cols"].append((c, False, nullable))
    opt_attr = set(rel.get("opt_attr", []))
    for a in rel.get("attr", []):
        tables[host]["cols"].append((a, False, nullable or a in opt_attr))
    tables[host]["fk"].append((fkcols, target))

def _add_fk_multi(spec, tables, host, targets, rel):
    """Come _add_fk ma per relazioni N-arie assorbite in un'unica entita' host (quando UN
    solo partecipante ha max=1): aggiunge una FK per ogni altro target, ma gli attributi
    propri della relazione UNA SOLA VOLTA (non uno per target, altrimenti duplicati)."""
    nullable = rel["card"][host][0] == 0
    for target in targets:
        tpk = _pk_attrs(spec, target)
        fkcols = [f"{target.lower()}_{a}" for a in tpk]
        for c in fkcols:
            tables[host]["cols"].append((c, False, nullable))
        tables[host]["fk"].append((fkcols, target))
    opt_attr = set(rel.get("opt_attr", []))
    for a in rel.get("attr", []):
        tables[host]["cols"].append((a, False, nullable or a in opt_attr))

def _rel_table(spec, tables, r, d):
    """opt_attr: attributi della relazione N:N/n-aria che sono opzionali (es. Giudizio* nel
    testo prof) -> nullable=True. Prima venivano sempre resi obbligatori: gap reale trovato
    confrontando la traduzione con la soluzione ufficiale di scuola_sci.

    key_attr: attributi PROPRI della relazione che fanno parte della CHIAVE PRIMARIA insieme
    alle FK verso le entita' partecipanti — non solo le FK. Serve quando la stessa coppia (o
    tripla) di entita' puo' ripetersi nella tabella distinta da un attributo proprio (es. stesso
    STUDENTE+CORSO ma ANNO diverso: la chiave e' (studente_id, corso_id, anno), non solo le FK).
    Senza key_attr la tabella accetterebbe solo UNA riga per combinazione di entita', perdendo
    le ripetizioni legittime — bug reale, mai gestito prima (tutti gli attributi propri erano
    sempre pk=False)."""
    cols, fks = [], []
    for e in d["tra"]:
        for a in _pk_attrs(spec, e):
            cn = f"{e.lower()}_{a}"
            cols.append((cn, True, False))
        fks.append(([f"{e.lower()}_{a}" for a in _pk_attrs(spec, e)], e))
    opt_attr = set(d.get("opt_attr", []))
    key_attr = set(d.get("key_attr", []))
    for a in d.get("attr", []):
        is_key = a in key_attr
        cols.append((a, is_key, (a in opt_attr) and not is_key))
    tables[r] = {"name": r, "cols": cols, "fk": fks}

KEY_L, KEY_R = "\x01", "\x02"  # marcatori chiave (non collidono con '_' nei nomi)

def rel_text(tables):
    """Notazione Belussi: R(pk_sottolineate, attr, attr*=nullable) + vincoli FK.
    Le chiavi sono racchiuse fra \\x01..\\x02 (render.py li converte in underline)."""
    lines = []
    for t in tables:
        parts = []
        for name, pk, nul in t["cols"]:
            s = name
            if pk: s = f"{KEY_L}{s}{KEY_R}"   # chiave (sottolineata)
            if nul: s = f"{s}*"                # * = puo' essere NULL
            parts.append(s)
        lines.append(f"{t['name']}({', '.join(parts)})")
    lines.append("")
    lines.append("Vincoli di integrita referenziale:")
    for t in tables:
        for cols, ref in t["fk"]:
            lines.append(f"  {t['name']}.({', '.join(cols)}) -> {ref}")
    return "\n".join(lines)

# ---------------------------------------------------------------- TikZ ER (layout deterministico + anti-collisione)
# Ogni nodo modellato come box (cx,cy,semilarghezza,semialtezza). I rombi relazione
# partono a meta arco e vengono spostati perpendicolarmente finche' non collidono
# con nessun altro box. Deterministico (nessun random): l'ordine di nudge e' fisso.
GX, GY = 5.6, 4.4          # passo griglia entita (ridotto: era 8.5/6.4, "distanza troppo
                             # grande" - gli attributi ora vanno anche sui lati liberi quindi
                             # serve meno aria; la compattazione toglie il resto dei buchi)
E_HW, E_HH = 1.4, 0.7      # semi-dimensioni box entita
R_HW, R_HH = 1.5, 0.75     # semi-dimensioni box relazione

def _overlap(a, b, padx=0.3, pady=0.3):
    return (abs(a[0]-b[0]) < a[2]+b[2]+padx) and (abs(a[1]-b[1]) < a[3]+b[3]+pady)

def _graphviz_layout(spec):
    """Layout + ROUTING vero via Graphviz dot (splines=ortho): obstacle-avoidance reale,
    non solo posizioni. Ritorna (pos, edge_points) o None se 'dot' non e' installato
    (Termux-safe: fallback su _graph_layout/_fallback_positions)."""
    import subprocess, shutil, tempfile, os as _os
    # neato (force-directed) invece di dot (a livelli): dot separa SEMPRE rombi ed entita' in
    # 2 righe rigide perche' il grafo e' bipartito - non replica mai il rombo "inline" fra le
    # due entita' che collega, come fa il prof. neato non ha questo vincolo di livelli.
    dot = shutil.which("neato") or (r"C:\Program Files\Graphviz\bin\neato.exe"
                                     if _os.path.exists(r"C:\Program Files\Graphviz\bin\neato.exe") else None)
    if not dot:
        return None
    ent = list(spec["entita"].keys())
    rel = spec.get("relazioni", {})
    edges = []  # (a, b) coppie nell'ordine in cui le disegniamo
    # grafo NON diretto: con "digraph" + frecce sempre relazione->entita' Graphviz forza
    # rank rigido (tutti i rombi riga 1, tutte le entita' riga 2) - difetto confrontato con
    # 3 diagrammi reali del prof, dove il rombo sta INLINE tra le due entita' che collega,
    # non isolato in una riga a parte. "graph" (non diretto) lascia che il rank segua la
    # struttura naturale del grafo invece della direzione arbitraria delle mie frecce.
    lines = ["graph G {", "splines=ortho; overlap=false; sep=\"+18\";", "node [shape=box,width=1.4,height=0.6];"]
    for e in ent:
        lines.append(f'  "{e}";')
    for r, d in rel.items():
        tra = [e for e in d.get("tra", []) if e in ent]
        if len(tra) < 2:
            continue
        lines.append(f'  "{r}" [shape=diamond,width=1.6,height=0.7];')
        for e in tra:
            lines.append(f'  "{r}" -- "{e}";')
            edges.append((r, e))
    for h in spec.get("isa", []):
        p = h["padre"]
        for f in h.get("figli", []):
            if p in ent and f in ent:
                lines.append(f'  "{f}" -- "{p}";')
                edges.append((f, p))
    lines.append("}")
    try:
        with tempfile.TemporaryDirectory() as td:
            dotfile = _os.path.join(td, "g.dot")
            open(dotfile, "w", encoding="utf-8").write("\n".join(lines))
            out = subprocess.run([dot, "-Tplain", dotfile], capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return None
    pos, epoints = {}, {}
    SCALE = 2.6  # pollici -> unita' TikZ (~cm), tarato a occhio contro il layout precedente
    for ln in out.splitlines():
        parts = ln.split()
        if not parts:
            continue
        if parts[0] == "node":
            name, x, y = parts[1], float(parts[2]), float(parts[3])
            pos[name] = (x * SCALE, y * SCALE)
        elif parts[0] == "edge":
            tail, head, n = parts[1], parts[2], int(parts[3])
            pts = [(float(parts[4+2*i])*SCALE, float(parts[5+2*i])*SCALE) for i in range(n)]
            epoints[(tail, head)] = pts
    if not pos:
        return None
    return pos, epoints

def _graph_layout(spec):
    """Layout con networkx (Kamada-Kawai, deterministico: nessun random, minimizza lo stress
    grafo<->euclideo -> molti meno incroci del grid+nudge fatto a mano). Nodi = entita' + rombi
    relazione insieme, cosi' l'algoritmo li posiziona tutti coerentemente in un colpo solo.
    Fallback su grid+BFS se networkx non e' installato (es. Termux senza pip)."""
    try:
        import networkx as nx
    except ImportError:
        return None
    G = nx.Graph()
    ent = list(spec["entita"].keys())
    rel = spec.get("relazioni", {})
    G.add_nodes_from(ent)
    for r, d in rel.items():
        tra = [e for e in d.get("tra", []) if e in ent]
        if len(tra) < 2:
            continue
        G.add_node(r)
        for e in tra:
            G.add_edge(r, e)
    for h in spec.get("isa", []):
        p = h["padre"]
        for f in h.get("figli", []):
            if p in ent and f in ent:
                G.add_edge(p, f)
    if G.number_of_nodes() == 0:
        return None
    scale = max(4.0, 2.3 * (G.number_of_nodes() ** 0.5))
    pos = nx.kamada_kawai_layout(G, scale=scale) if G.number_of_edges() else \
          nx.spring_layout(G, scale=scale, seed=0)
    return {k: (float(v[0]), float(v[1])) for k, v in pos.items()}

def _adjacency_layout(spec):
    """Posizionamento a griglia per ADIACENZA (idea dell'utente): entita' collegate da una
    relazione finiscono in celle di griglia ADIACENTI (stessa riga o colonna), non sparse
    da un algoritmo fisico. Root al centro, BFS: ogni vicino nuovo prova le 4 direzioni
    (destra, giu', sinistra, su) e prende la prima cella libera. Deterministico (ordine
    fisso, nessun random). Stile di disegno (Chen: cerchi/rombi) invariato, cambia solo
    DOVE finiscono i nodi."""
    ent = list(spec["entita"].keys())
    if not ent:
        return {}
    adj = {e: [] for e in ent}
    for d in spec.get("relazioni", {}).values():
        tra = [e for e in d.get("tra", []) if e in adj]
        for a in tra:
            for b in tra:
                if a != b and b not in adj[a]:
                    adj[a].append(b)
    for h in spec.get("isa", []):
        p, figli = h["padre"], [f for f in h.get("figli", []) if f in adj]
        if p in adj:
            for f in figli:
                if f not in adj[p]: adj[p].append(f)
                if p not in adj[f]: adj[f].append(p)
    cell = {}          # (gx,gy) -> nome entita'
    gpos = {}           # nome entita' -> (gx,gy)
    DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # GIU' prima (pagina verticale), poi destra, su, sinistra
    def place(e, gx, gy):
        cell[(gx, gy)] = e; gpos[e] = (gx, gy)
    seen = set()
    row_y, row_start_x = 0, 0   # componenti disconnesse vanno a capo dopo ~5 colonne,
                                  # altrimenti una spec con tanti cluster indipendenti
                                  # (es. showcase progressivo) genera una striscia
                                  # larghissima e bassissima, illeggibile.
    for start in ent:
        if start in seen:
            continue
        if start not in gpos:
            maxx = max((c[0] for c in cell if c[1] == row_y), default=row_start_x - 3)
            if maxx - row_start_x > 12:
                row_y -= 5; row_start_x = 0
                maxx = row_start_x - 3
            gx0 = maxx + 3 if cell else 0
            place(start, gx0, row_y)
        queue = [start]; seen.add(start)
        while queue:
            cur = queue.pop(0)
            cx, cy = gpos[cur]
            for nb in sorted(adj[cur]):
                if nb in gpos:
                    if nb not in seen:
                        seen.add(nb); queue.append(nb)
                    continue
                for dx, dy in DIRS:
                    nx_, ny_ = cx + dx, cy + dy
                    if (nx_, ny_) not in cell:
                        place(nb, nx_, ny_); break
                else:
                    # tutte e 4 occupate: NON prima-libera-in-spirale (GAPS.md punto 5:
                    # allontanava entita' collegate su grafi densi). Ora: fra le celle libere
                    # in un raggio crescente, scegli quella che MINIMIZZA la distanza dal
                    # CENTROIDE dei vicini gia' piazzati di nb (resta vicino a chi lo tira).
                    anchors = [gpos[o] for o in adj[nb] if o in gpos] or [(cx, cy)]
                    ax = sum(p[0] for p in anchors) / len(anchors)
                    ay = sum(p[1] for p in anchors) / len(anchors)
                    best_cell, best_d = None, None
                    r = 2
                    while best_cell is None:
                        for dx in range(-r, r + 1):
                            for dy in range(-r, r + 1):
                                c_ = (cx + dx, cy + dy)
                                if c_ not in cell:
                                    d_ = (c_[0] - ax) ** 2 + (c_[1] - ay) ** 2
                                    if best_d is None or d_ < best_d:
                                        best_cell, best_d = c_, d_
                        r += 1
                    place(nb, best_cell[0], best_cell[1])
                seen.add(nb); queue.append(nb)
    # post-processing gerarchie ISA (stile prof, visto nei diagrammi ufficiali): i figli
    # vengono IMPILATI IN COLONNA accanto al padre, non sparsi attorno - cosi' il disegno
    # a spina/bus (hub |- figlio) produce un tratto verticale condiviso pulito invece di
    # 6+ linee che convergono da ogni direzione sul triangolo ("un fottio di relazioni").
    for h in spec.get("isa", []):
        p, figli = h["padre"], [f for f in h.get("figli", []) if f in gpos]
        if p not in gpos or not figli:
            continue
        px_, py_ = gpos[p]
        for col_dx in (1, -1, 2, -2):        # prova colonna a destra, poi sinistra...
            col_x = px_ + col_dx
            # celle in colonna centrate sull'altezza del padre
            offsets = [0, -1, 1, -2, 2, -3, 3, -4, 4]
            free = [(col_x, py_ + o) for o in offsets if (col_x, py_ + o) not in cell
                    or cell[(col_x, py_ + o)] in figli]
            if len(free) >= len(figli):
                for f in figli:                 # libera prima TUTTE le vecchie celle dei figli
                    if gpos.get(f) in cell and cell[gpos[f]] == f:
                        del cell[gpos[f]]
                for f, c in zip(figli, free):
                    place(f, c[0], c[1])
                break
    # COMPATTAZIONE finale (feedback utente: "sfrutta lo spazio al centro invece di
    # espanderti ai margini"): righe/colonne di griglia VUOTE vengono collassate
    # rimappando le coordinate usate a indici consecutivi - i buchi lasciati dal BFS
    # e dallo spostamento ISA spariscono senza cambiare la topologia relativa.
    used_x = sorted({g[0] for g in gpos.values()})
    used_y = sorted({g[1] for g in gpos.values()})
    remap_x = {v: i for i, v in enumerate(used_x)}
    remap_y = {v: i for i, v in enumerate(used_y)}
    return {e: (remap_x[gpos[e][0]] * GX, remap_y[gpos[e][1]] * GY) for e in ent}

def _bfs_order(spec):
    """Ordina le entita per adiacenza (BFS sul grafo delle relazioni), non per ordine di
    inserimento nello spec: entita connesse finiscono vicine in griglia -> meno linee lunghe
    che attraversano righe intere e si incrociano."""
    ent = list(spec["entita"].keys())
    adj = {e: set() for e in ent}
    for d in spec.get("relazioni", {}).values():
        tra = [e for e in d.get("tra", []) if e in adj]
        for a in tra:
            adj[a].update(x for x in tra if x != a)
    for h in spec.get("isa", []):
        p, figli = h["padre"], [f for f in h.get("figli", []) if f in adj]
        if p in adj:
            adj[p].update(figli)
            for f in figli: adj[f].add(p)
    seen, order = set(), []
    for start in ent:               # copre anche componenti disconnesse, ordine deterministico
        if start in seen:
            continue
        queue = [start]; seen.add(start)
        while queue:
            cur = queue.pop(0)
            order.append(cur)
            for nxt in sorted(adj[cur]):
                if nxt not in seen:
                    seen.add(nxt); queue.append(nxt)
    return order

def _node_radius(spec, name):
    """Raggio minimo di un nodo (entita' o relazione) includendo il ventaglio di attributi:
    kamada_kawai tratta i nodi come punti e li ammassa; questo raggio serve al passo di
    repulsione sotto per non far sovrapporre box+etichette."""
    ent, rel = spec.get("entita", {}), spec.get("relazioni", {})
    name_w = 0.11 * len(name) + 0.3   # il NOME del nodo puo' essere piu' largo del box di base
    if name in ent:
        n = len(ent[name].get("attr", []))
        base = max(E_HW, name_w)
    elif name in rel:
        n = len(rel[name].get("attr", []))
        # i rombi diamond crescono ~1.6x rispetto al testo per la forma a losanga
        base = max(R_HW, name_w * 1.6)
    else:
        return E_HW
    if n == 0:
        return base
    avg_w = 1.3  # stima larghezza media per attributo (etichetta+spaziatura)
    return max(base, n * avg_w / 2.0)

def _relax(spec, pos, iterations=120, pad=0.5):
    """Repulsione iterativa: se due nodi sono piu' vicini della somma dei loro raggi (attributi
    inclusi), li allontana lungo la retta che li congiunge. Deterministico (ordine fisso,
    nessun random) - preserva la topologia globale di kamada_kawai, risolve gli ammassamenti
    locali che l'algoritmo puro ignora (non conosce le dimensioni dei nodi)."""
    names = sorted(pos.keys())
    radius = {n: _node_radius(spec, n) for n in names}
    for _ in range(iterations):
        moved = False
        for i, a in enumerate(names):
            for b in names[i+1:]:
                ax, ay = pos[a]; bx, by = pos[b]
                dx, dy = bx - ax, by - ay
                dist = (dx*dx + dy*dy) ** 0.5
                need = radius[a] + radius[b] + pad
                if dist < need:
                    moved = True
                    if dist < 1e-6:
                        dx, dy, dist = 0.01 * (hash(a+b) % 7 - 3 or 1), 0.01, 0.015
                    push = (need - dist) / 2.0
                    ux, uy = dx / dist, dy / dist
                    pos[a] = (ax - ux*push, ay - uy*push)
                    pos[b] = (bx + ux*push, by + uy*push)
        if not moved:
            break
    return pos

def _place_relations(spec, pos):
    """Data una posizione per ogni entita' (pos, modificato in place), aggiunge la posizione
    di ogni rombo-relazione: centroide delle entita' partecipanti + nudge perpendicolare
    anti-collisione. Fattorizzato fuori da _fallback_positions cosi' anche
    _adjacency_layout puo' riusarlo senza duplicare la logica di nudge."""
    rel = spec.get("relazioni", {})
    boxes = [(x, y, E_HW, E_HH) for x, y in pos.values()]
    for r, d in rel.items():
        tra = [e for e in d["tra"] if e in pos]
        if len(tra) < 2:
            continue
        cx = sum(pos[e][0] for e in tra) / len(tra)
        cy = sum(pos[e][1] for e in tra) / len(tra)
        if len(tra) == 2:
            dx, dy = pos[tra[1]][0]-pos[tra[0]][0], pos[tra[1]][1]-pos[tra[0]][1]
            L = (dx*dx + dy*dy) ** 0.5 or 1.0
            px, py = -dy / L, dx / L
        else:
            px, py = 0.0, 1.0
        best = (cx, cy)
        for k in range(0, 40):
            s = ((k + 1) // 2) * 0.9 * (1 if k % 2 else -1) if k else 0
            cand = (cx + px*s, cy + py*s, R_HW, R_HH)
            if not any(_overlap(cand, b) for b in boxes):
                best = (cand[0], cand[1]); break
        pos[r] = best
        boxes.append((best[0], best[1], R_HW, R_HH))
    return pos

def _fallback_positions(spec):
    """Grid+BFS (nessuna dipendenza esterna, Termux-safe) usato solo se networkx manca."""
    ent = _bfs_order(spec)
    cols = max(1, int(len(ent) ** 0.5 + 0.99))
    pos = {}
    for i, e in enumerate(ent):
        pos[e] = ((i % cols) * GX, -(i // cols) * GY)
    return _place_relations(spec, pos)

def tikz(spec):
    rel = spec.get("relazioni", {})
    # neato+splines=ortho (routing ortogonale) ABBANDONATO come DEFAULT: l'utente ha visto
    # entrambe le versioni via PDF e ha detto chiaro che l'ortogonale "fa schifo" (linee che
    # piegano ad angolo retto in modo caotico) mentre la diagonale (kamada_kawai) era
    # "sensata". Tenuta disponibile via env var ER_LAYOUT=ortho per confronto/archivio,
    # default sempre diagonale.
    gv = _graphviz_layout(spec) if os.environ.get("ER_LAYOUT") == "ortho" else None
    epoints = {}
    if gv is not None:
        pos, epoints = gv   # posizioni + polilinee ortogonali gia' obstacle-avoiding, no relax
    elif os.environ.get("ER_LAYOUT") == "kamada":
        glayout = _graph_layout(spec)
        pos = glayout if glayout is not None else _fallback_positions(spec)
        pos = _relax(spec, pos)
    else:
        # default: adiacenza a griglia (idea utente) - entita' collegate finiscono in celle
        # adiacenti (stessa riga/colonna) invece che sparse da un algoritmo fisico. Stile
        # Chen di disegno invariato. Relax finale solo per rifinire eventuali sovrapposizioni
        # locali di attributi, non per spostare la struttura a griglia.
        # niente _relax qui: sposterebbe i nodi fuori griglia rompendo l'allineamento in
        # colonna dei figli ISA (necessario per la spina |- a tratto verticale condiviso).
        # La griglia GX/GY e' abbastanza spaziosa da non aver bisogno di repulsione.
        pos = _adjacency_layout(spec) or {}
        if pos:
            pos = _place_relations(spec, pos)
        else:
            pos = _fallback_positions(spec)
    out = [r"\begin{tikzpicture}[",
           r"  ent/.style={draw,thick,minimum width=2.4cm,minimum height=1cm,fill=blue!5},",
           r"  rel/.style={draw,thick,diamond,aspect=2,minimum width=2.4cm,fill=orange!10},",
           r"  keyattr/.style={draw,thick,circle,fill=black,minimum size=0.22cm,inner sep=0pt},",
           r"  attr/.style={draw,thick,circle,fill=white,minimum size=0.22cm,inner sep=0pt},",
           r"  isa/.style={draw,thick,isosceles triangle,shape border rotate=-90,"
           r"fill=green!20,minimum size=0.7cm,inner sep=1pt},",
           r"  every node/.style={font=\small}]"]
    def lbl(s): return s.replace("_", r"\_")

    def _draw_attr_fan(node_id, cx, cy, attrs, offs, keyset, optset, side):
        """Disegna un ventaglio di attributi su UN lato (N/S/E/W) del nodo, con indici
        (per id univoci) presi da offs cosi' i lati non si scontrano fra loro."""
        n = len(attrs)
        if n == 0:
            return
        widths = [max(0.9, 0.11 * len(a) + 0.35) for a in attrs]
        total = sum(widths)
        pos_along, cum = [], -total / 2.0
        for w in widths:
            pos_along.append(cum + w / 2.0); cum += w
        vertical = side in ("N", "S")
        ydir = 1 if side == "N" else (-1 if side == "S" else 0)
        xdir = 1 if side == "E" else (-1 if side == "W" else 0)
        for i, a in enumerate(attrs):
            if vertical:
                # altezza ALTERNATA (zigzag): pallini pari piu' vicini, dispari piu' lontani -
                # le etichette sopra i pallini non si toccano piu' in orizzontale
                ax, ay = cx + pos_along[i], cy + ydir * (1.05 if i % 2 == 0 else 1.65)
                anchor = "south" if side == "N" else "north"
            else:
                ax, ay = cx + xdir * 1.6, cy + pos_along[i]
                anchor = "west" if side == "E" else "east"
            aid = f"{node_id}_a{offs + i}"
            style = "keyattr" if a in keyset else "attr"
            out.append(f"    \\node[{style}] ({aid}) at ({ax:.2f},{ay:.2f}) {{}};")
            out.append(f"    \\node[font=\\tiny,anchor={anchor}] at ({aid}.{ {'N':'north','S':'south','E':'east','W':'west'}[side] }) {{{lbl(a)}}};")
            linestyle = "dashed" if a in optset else "solid"
            out.append(f"    \\draw[thick,{linestyle}] ({node_id}) -- ({aid});")

    # per ogni entita': quali lati (N/S/E/W) sono OCCUPATI da linee in arrivo (rombi
    # collegati, hub ISA)? Gli attributi vanno sui lati LIBERI (idea utente: "attributi
    # occupano quel lato che non viene occupato").
    def _busy_sides(e):
        busy = set()
        ex, ey = pos[e]
        neighbors = []
        for r, d in rel.items():
            if r in pos and e in d.get("tra", []):
                neighbors.append(pos[r])
        for h in spec.get("isa", []):
            if e == h["padre"] or e in h.get("figli", []):
                others = [h["padre"]] + list(h.get("figli", []))
                for o in others:
                    if o != e and o in pos:
                        neighbors.append(pos[o])
        for nx_, ny_ in neighbors:
            dx, dy = nx_ - ex, ny_ - ey
            if abs(dx) >= abs(dy):
                busy.add("E" if dx > 0 else "W")
            else:
                busy.add("N" if dy > 0 else "S")
        return busy

    def draw_attrs(node_id, cx, cy, attrs, keyset, optset, upward=True):
        """Attributi sui lati LIBERI dell'entita' (non attraversati da linee di relazione),
        in ordine di preferenza: prima i liberi, poi i meno trafficati. Multi-lato se tanti."""
        n = len(attrs)
        if n == 0:
            return 0.0
        busy = _busy_sides(node_id) if node_id in pos else set()
        pref = [s for s in ("N", "S", "E", "W") if s not in busy] + \
               [s for s in ("N", "S", "E", "W") if s in busy]
        if n <= 4:
            _draw_attr_fan(node_id, cx, cy, attrs, 0, keyset, optset, pref[0])
        elif n <= 8:
            half = (n + 1) // 2
            _draw_attr_fan(node_id, cx, cy, attrs[:half], 0, keyset, optset, pref[0])
            _draw_attr_fan(node_id, cx, cy, attrs[half:], half, keyset, optset, pref[1])
        else:
            q = (n + 3) // 4
            groups = [attrs[i:i+q] for i in range(0, n, q)]
            off = 0
            for g, side in zip(groups, pref):
                _draw_attr_fan(node_id, cx, cy, g, off, keyset, optset, side)
                off += len(g)
        return sum(max(0.9, 0.11 * len(a) + 0.35) for a in attrs)

    for e, (x, y) in pos.items():
        if e not in spec["entita"]:
            continue
        out.append(f"  \\node[ent] ({e}) at ({x:.2f},{y:.2f}) {{{lbl(e)}}};")
        d = spec["entita"][e]
        keyset = set(d.get("id", [[]])[0]) if d.get("id") else set()
        optset = set(d.get("opt", []))
        # multivalore inclusi nel ventaglio (il nome porta il suffisso (0,N) come fa il prof
        # per segnalare la molteplicita' quando non si usa il doppio ovale)
        attrs_all = d.get("attr", []) + [f"{m} (0,N)" for m in d.get("multi", [])]
        # CHIAVE COMPOSTA (2+ attributi nell'id): notazione prof (vista nelle trascrizioni
        # delle soluzioni ufficiali: "linea che esce dall'entita' termina con pallino nero
        # che si dirama nei due attributi") - UN pallino pieno da cui partono i rami verso
        # gli attributi della chiave, che diventano pallini VUOTI. Prima disegnavo N pallini
        # pieni separati: ambiguo (sembrano N chiavi distinte, non una chiave composta).
        key_attrs_local = [a for a in (d.get("id", [[]])[0] if d.get("id") else []) if a in attrs_all]
        if len(key_attrs_local) >= 2:
            kx, ky = x - E_HW - 0.55, y + E_HH + 0.55
            out.append(f"  \\node[keyattr] ({e}_kdot) at ({kx:.2f},{ky:.2f}) {{}};")
            out.append(f"  \\draw[thick] ({e}) -- ({e}_kdot);")
            keyset = set()          # gli attributi della chiave diventano pallini vuoti...
            composite_key_of = {a: f"{e}_kdot" for a in key_attrs_local}
        else:
            composite_key_of = {}
        draw_attrs(e, x, y, attrs_all, keyset, optset)
        # ...e si collegano al pallino-chiave con rami sottili
        for i, a in enumerate(attrs_all):
            if a in composite_key_of:
                out.append(f"  \\draw[thin] ({composite_key_of[a]}) -- ({e}_a{i});")
    # relazioni: posizione gia' calcolata da _graph_layout/_fallback_positions insieme alle
    # entita' (stesso algoritmo, un solo layout coerente invece di entita'+nudge separati).
    for r, d in rel.items():
        tra = [e for e in d["tra"] if e in pos]
        if len(tra) < 2 or r not in pos:
            continue
        best = pos[r]
        # rombi SENZA testo di default (richiesta utente: nome solo se l'esercizio lo chiede,
        # rombi piccoli = piu' facili da posizionare). Nome dentro solo con "label": true.
        rlabel = lbl(r) if d.get("label") else ""
        rstyle = "rel" if d.get("label") else "rel,aspect=1,minimum width=0.9cm"
        out.append(f"  \\node[{rstyle}] ({r}) at ({best[0]:.2f},{best[1]:.2f}) {{{rlabel}}};")
        c = d["card"]
        for e in tra:
            pts = epoints.get((r, e))
            if pts:
                # polilinea ortogonale (obstacle-avoiding) calcolata da Graphviz: solo H/V.
                coords = " -- ".join(f"({px:.2f},{py:.2f})" for px, py in pts)
                out.append(f"  \\draw[thick] {coords};")
                mx, my = pts[max(1, len(pts)-2)]
                out.append(f"  \\node[above,font=\\scriptsize] at ({mx:.2f},{my:.2f}) {{({c[e][0]},{c[e][1]})}};")
            else:
                # pos=0.8: etichetta cardinalita' vicino all'ENTITA' (non a meta' linea) -
                # convenzione Chen standard, mancava: finiva ambigua al centro dell'arco.
                # cardinalita' SEMPRE orizzontale (niente sloped: l'etichetta ruotata lungo
                # la linea era illeggibile/si sovrapponeva - richiesta esplicita utente)
                out.append(f"  \\draw[thick] ({r}) -- node[above,pos=0.72,font=\\tiny]{{({c[e][0]},{c[e][1]})}} ({e});")
        if d.get("attr"):
            draw_attrs(r, best[0], best[1], d["attr"], set(), set(), upward=False)
    # ISA: un solo nodo "spina" (triangolo, stile tikz-er2) tra il padre e i figli, invece di
    # una freccia per figlio che converge caoticamente sul padre (difetto visto confrontando
    # con 3 diagrammi reali del prof: loro disegnano SEMPRE la generalizzazione come padre--
    # [triangolo]--<diramazione a T verso ogni figlio>, mai frecce multiple dirette al padre).
    for hi, h in enumerate(spec.get("isa", [])):
        p = h["padre"]
        figli = [f for f in h["figli"] if f in pos]
        if p not in pos or not figli:
            continue
        px_, py_ = pos[p]
        fcx = sum(pos[f][0] for f in figli) / len(figli)
        fcy = sum(pos[f][1] for f in figli) / len(figli)
        # distanza FISSA dal padre (non punto medio): col layout neato padre e figli spesso
        # finiscono vicini, e il punto medio ricade dentro il box del padre, sovrapponendo il
        # triangolo al testo (bug trovato: "DIPEN[triangolo]TE"). Cosi' l'hub sta sempre fuori.
        dx, dy = fcx - px_, fcy - py_
        dlen = (dx*dx + dy*dy) ** 0.5 or 1.0
        HUB_DIST = E_HH + 0.9
        hub_x, hub_y = px_ + dx / dlen * HUB_DIST, py_ + dy / dlen * HUB_DIST
        hub = f"_isa{hi}"
        # niente triangolo (richiesta utente): hub = punto invisibile, restano solo le linee
        # con freccia dal ramo verso il padre (stile visto in alcuni compiti studenti).
        out.append(f"  \\coordinate ({hub}) at ({hub_x:.2f},{hub_y:.2f});")
        out.append(f"  \\draw[thick,-{{Triangle[open]}}] ({hub}) -- ({p});")
        # spina/bus stile prof: se i figli sono impilati in colonna (stessa x, layout
        # adiacenza), un unico tratto verticale condiviso + rami orizzontali (hub |- figlio).
        # Altrimenti (layout kamada/ortho) linea diretta come prima.
        same_col = len({round(pos[f][0], 1) for f in figli}) == 1
        for f in figli:
            if same_col and abs(pos[f][0] - hub_x) > 0.5:
                out.append(f"  \\draw[thick] ({hub}) |- ({f});")
            else:
                out.append(f"  \\draw[thick] ({hub}) -- ({f});")
    out.append(r"\end{tikzpicture}")
    # bounding box (cm) per dimensionare la PAGINA sul diagramma invece di rimpicciolirlo:
    # con adjustbox 'max width=\textwidth' il testo diventava minuscolo sui layout grandi
    # (neato spesso produce catene lunghe) - una pagina su misura non richiede alcuno shrink.
    xs = [p[0] for p in pos.values()] or [0]
    ys = [p[1] for p in pos.values()] or [0]
    # margine generoso: una stima risicata causa un salto pagina indesiderato (il contenuto
    # non entra per un pelo, LaTeX lo spinge alla pagina dopo, lasciando il titolo orfano
    # su una pagina quasi vuota - visto e fixato testando catena_alberghi).
    width_cm = max(20.0, (max(xs) - min(xs)) + 10.0)
    height_cm = max(15.0, (max(ys) - min(ys)) + 12.0)
    tikz.last_bbox = (width_cm, height_cm)
    return "\n".join(out)

# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tikz", action="store_true")
    ap.add_argument("--rel", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    errs = check(spec)
    if a.check or a.all:
        if errs:
            print("SPEC NON VALIDA:", file=sys.stderr)
            for e in errs: print("  -", e, file=sys.stderr)
            sys.exit(1)
        print("spec valida: %d entita, %d relazioni" % (len(spec["entita"]), len(spec.get("relazioni", {}))), file=sys.stderr)
    if a.tikz or a.all:
        print("% ===== DIAGRAMMA ER =====")
        print(tikz(spec))
    if a.rel or a.all:
        print("\n% ===== SCHEMA RELAZIONALE =====")
        print(rel_text(translate(spec)))
    if not (a.check or a.tikz or a.rel or a.all):
        if errs:
            for e in errs: print("  -", e, file=sys.stderr)
            sys.exit(1)
        print("OK")

if __name__ == "__main__":
    main()
