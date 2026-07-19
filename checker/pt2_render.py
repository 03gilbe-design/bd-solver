#!/usr/bin/env python3
"""pt2_render.py — genera blocchi LaTeX per ciascun tipo di esercizio parte 2,
a partire dai motori deterministici pt2_*. Usato da solve_pt2.py (spec generico,
come render.py/solve.py fanno per parte 1).

Ogni funzione render_X(ex) prende un dict esercizio dello spec JSON e ritorna
una stringa LaTeX (titolo + contenuto + spiegazioni + eventuale disegno TikZ)."""
import math
import pt2_ripresa, pt2_schedule, pt2_costo, pt2_btree

def esc(s):
    return str(s).replace("_", "\\_").replace("{", "\\{").replace("}", "\\}")

def par(s):
    return esc(s) + "\\par\\smallskip\n"

def note(s):
    return "{\\footnotesize\\textit{" + s + "}}\\par\\smallskip\n"

def _titolo(ex):
    """Titolo esercizio nello stile dei testi d'esame del prof:
    'd) (4) Gestore dell'affidabilita'' — id, punti tra parentesi, nome sottolineato."""
    pid = ex.get("id", "")
    pt = f"({ex['punti']}) " if ex.get("punti") else ""
    return ("\\bigskip\\par\\noindent\\textbf{" + esc(pid) + ") " + pt +
            "\\underline{" + esc(ex.get("titolo", "")) + "}}\\par\\medskip\n")


def render_ripresa(ex):
    L = [_titolo(ex)]
    log = ex["log"]
    L.append("{\\footnotesize\\texttt{" + esc(log) + " guasto}}\\par\\medskip\n")
    r = pt2_ripresa.ripresa(log)
    notes = [
        "Si cerca l'ultimo CK nel log: le transazioni elencate al suo interno sono quelle attive in quel momento.",
        "Per definizione, appena dopo il CK tutte le transazioni attive vanno in UNDO; REDO parte vuoto.",
        "Si scorre il log dal CK in poi: un C(T) sposta T da UNDO a REDO; un B(T) nuovo aggiunge T a UNDO. Un A(T) NON sposta T: resta in UNDO.",
        "Le operazioni delle transazioni in UNDO si annullano scorrendo il log ALL'INDIETRO: U ripristina Before, I diventa cancellazione, D diventa inserimento.",
        "Le operazioni delle transazioni in REDO si rieseguono scorrendo il log IN AVANTI dall'inizio, applicando il valore After.",
    ]
    for s, n in zip(r["steps"], notes):
        L.append(par(s.replace("{}", "0/")).replace("0/", "$\\emptyset$"))
        L.append(note(n))
    return "".join(L)


def _graph_tikz(nodes, edges):
    R = 3.2
    n = len(nodes)
    pos = {t: (R * math.cos(2 * math.pi * i / n + math.pi / 2),
               R * math.sin(2 * math.pi * i / n + math.pi / 2)) for i, t in enumerate(nodes)}
    out = ["\\begin{center}\\begin{tikzpicture}[node/.style={circle,draw,minimum size=8mm,font=\\small}]"]
    for t in nodes:
        x, y = pos[t]
        out.append(f"\\node[node] (T{t}) at ({x:.2f},{y:.2f}) {{$T_{{{t}}}$}};")
    for a, b in edges:
        out.append(f"\\draw[-{{Stealth}},thick] (T{a}) -- (T{b});")
    out.append("\\end{tikzpicture}\\end{center}")
    return "\n".join(out)


def render_schedule(ex):
    L = [_titolo(ex)]
    S = ex["schedule"]
    L.append("\\texttt{S: " + esc(S) + "}\\par\\medskip\n")
    ops = pt2_schedule.parse(S)
    conf = pt2_schedule.conflicts(ops)
    fmt = lambda op: f"{op[0]}{op[1]}({op[2]})"
    L.append("\\textbf{Conflitti:} " + ", ".join(f"({fmt(a)},{fmt(b)})" for a, b in conf) + "\\par\\smallskip\n")
    L.append(note("Due azioni sono in conflitto se sono di transazioni diverse, agiscono sullo stesso oggetto, e almeno una e' una scrittura."))
    edges = sorted(pt2_schedule.conflict_graph(ops))
    nodes = sorted(set(t for _, t, _ in ops))
    L.append("\\textbf{Grafo dei conflitti:}\\par\n")
    L.append(_graph_tikz(nodes, edges))
    L.append(note("CSR sse il grafo dei conflitti non ha cicli: un ordinamento topologico da' uno schedule seriale equivalente."))
    cls = pt2_schedule.classify(S)
    L.append(f"\\textbf{{Esito: S \\`e {cls}}}" + (" (CSR implica anche VSR)" if cls == "CSR" else "") + ".\\par\n")
    tops = pt2_schedule.topological_orders(ops)
    if tops:
        L.append("\\textbf{Seriali equivalenti:} " + "; ".join(",".join(f"T{t}" for t in o) for o in tops) + "\\par\n")
    is2pl = pt2_schedule.is_2pl(ops)
    L.append("\\textbf{2PL:} " + ("s\\`i, \\`e 2PL." if is2pl else "no, NON \\`e 2PL.") + "\\par\n")
    return "".join(L)


def render_costo(ex):
    L = [_titolo(ex)]
    p = ex["parametri"]
    rc = pt2_costo.solve(**p)
    if "descrizione" in ex:
        L.append(par(ex["descrizione"]))
    L.append(note("Formula NLJ senza indice: costo = scan(interna) + scrittura(selezione interna) + scan(esterna) + $NR_{\\text{sel esterna}} \\times NP_{\\text{sel interna}}$."))
    for s in rc["steps"]:
        L.append(par(s))
    L.append("\\textbf{Totale" + (f" punto (1)" if "steps_indice" in rc else "") + ": " +
              f"{rc['totale']:,}".replace(",", ".") + " accessi}\\par\\medskip\n")
    if "steps_indice" in rc:
        d = p.get("prof_indice")
        L.append(note(f"Formula con indice B$^+$-tree di profondit\\`a {d}: si sostituisce $NP_{{\\text{{sel interna}}}}$ con $d+\\lceil NR_{{\\text{{sel interna}}}}/VAL(\\text{{join}})\\rceil$."))
        L.append(par(rc["steps_indice"][-1]))
        L.append("\\textbf{Totale punto (2) con indice: " +
                  f"{rc['totale_indice']:,}".replace(",", ".") + " accessi}\\par\n")
    return "".join(L)


def _btree_tikz(root, caption):
    """Disegno come nelle slide del prof: albero a cono (ogni padre CENTRATO sopra
    i suoi figli), frecce padre->figlio, catena di frecce tra foglie consecutive."""
    GAP = 0.5          # spazio orizzontale tra nodi foglia
    ROWH = 1.6         # distanza verticale tra livelli

    def width(n):
        keys = n if pt2_btree.is_leaf(n) else pt2_btree.keys_of(n)
        return 0.55 * max(len(keys), 1) + 0.35

    nodes = []          # (id, x_centro, y, testo)
    edges = []          # (id_padre, id_figlio)
    leaf_ids = []
    cursor = [0.0]      # x del prossimo bordo sinistro di foglia

    def place(n, depth):
        nid = len(nodes)
        nodes.append(None)                        # placeholder, x dopo
        if pt2_btree.is_leaf(n):
            x = cursor[0] + width(n) / 2
            cursor[0] += width(n) + GAP
            leaf_ids.append(nid)
            nodes[nid] = (nid, x, -depth * ROWH, ",".join(str(k) for k in n))
            return x
        child_xs = []
        for c in n["ch"]:
            cid_before = len(nodes)
            child_xs.append(place(c, depth + 1))
            edges.append((nid, cid_before))
        x = (child_xs[0] + child_xs[-1]) / 2      # padre centrato sui figli -> cono
        nodes[nid] = (nid, x, -depth * ROWH,
                       ",".join(str(k) for k in pt2_btree.keys_of(n)))
        return x

    place(root, 0)
    out = [f"\\textbf{{{caption}}}\\par",
           "\\begin{center}\\begin{tikzpicture}[font=\\footnotesize,",
           "node/.style={draw,minimum height=6mm,inner sep=3pt}]"]
    for nid, x, y, txt in nodes:
        out.append(f"\\node[node] (n{nid}) at ({x:.2f},{y:.2f}) {{{txt}}};")
    for p, c in edges:
        out.append(f"\\draw[-{{Stealth}}] (n{p}.south) -- (n{c}.north);")
    for a, b in zip(leaf_ids, leaf_ids[1:]):      # catena foglie come nel disegno del prof
        out.append(f"\\draw[-{{Stealth}},densely dashed] (n{a}.east) -- (n{b}.west);")
    out.append("\\end{tikzpicture}\\end{center}")
    return "\n".join(out)


def render_btree(ex):
    L = [_titolo(ex)]
    f = ex["fanout"]
    L.append(note(f"Vincoli fan-out {f}: foglie {math.ceil(f/2)-1}--{f-1} chiavi, nodi interni {math.ceil(f/2)}--{f} puntatori (root esente dal minimo). Le chiavi dei nodi interni sono il minimo valore del sotto-albero a destra."))
    t = pt2_btree.build(ex["foglie"], f)
    L.append(_btree_tikz(t, "a) costruzione"))
    for i, op in enumerate(ex.get("operazioni", [])):
        letter = chr(ord("b") + i)
        if op["op"] == "insert":
            t = pt2_btree.insert(t, op["key"], f)
            L.append(note(f"Inserimento di {op['key']}: se la foglia raggiunta supera {f-1} chiavi, SPLIT senza guardare i fratelli (propagato in alto se serve)."))
        elif op["op"] == "delete":
            t = pt2_btree.delete(t, op["key"], f)
            L.append(note(f"Cancellazione di {op['key']}: se la foglia scende sotto {math.ceil(f/2)-1} chiavi, MERGE/redistribuzione col fratello sinistro (propagato in alto se serve)."))
        L.append(_btree_tikz(t, f"{letter}) dopo {op['op']} {op['key']}"))
    return "".join(L)


def render_teoria(ex):
    """Domanda di teoria: testo domanda + risposta discorsiva scritta nello spec
    (campo 'risposta': lista di paragrafi, o stringhe che iniziano con '- ' per elenchi).
    Le risposte NON vengono da un motore: vanno scritte basandosi sulle slide."""
    L = [_titolo(ex)]
    if ex.get("domanda"):
        L.append("\\textit{" + esc(ex["domanda"]) + "}\\par\\medskip\n")
    items = []
    def flush_items():
        if items:
            L.append("\\begin{itemize}" +
                     "".join("\\item " + esc(i) + "\n" for i in items) +
                     "\\end{itemize}\n")
            items.clear()
    for p in ex.get("risposta", []):
        if p.startswith("- "):
            items.append(p[2:])
        else:
            flush_items()
            L.append(esc(p) + "\\par\\smallskip\n")
    flush_items()
    return "".join(L)


RENDERERS = {"ripresa": render_ripresa, "schedule": render_schedule,
             "costo": render_costo, "btree": render_btree, "teoria": render_teoria}

def render_esercizio(ex):
    return RENDERERS[ex["tipo"]](ex)
