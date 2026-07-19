#!/usr/bin/env python3
"""algebra_tree.py — rende un'espressione di algebra relazionale come ALBERO (non formula
lineare), usando il pacchetto LaTeX 'forest'. Deterministico: l'utente/Claude scrive la
struttura ad albero in JSON, il codice genera sempre lo stesso disegno corretto.

Formato nodo:
  {"op":"pi", "attrs":["Nome","Cognome"], "child": {...}}          proiezione
  {"op":"sigma", "cond":"Ritardo>0", "child": {...}}                selezione
  {"op":"join", "cond":"...", "left": {...}, "right": {...}}        join (naturale se cond None)
  {"op":"rename", "map":"W<-C", "child": {...}}                     ridenominazione
  {"op":"union"|"diff"|"intersect", "left": {...}, "right": {...}}  binari insiemistici
  {"op":"table", "name":"VOLO"}                                     foglia = relazione base
"""
SYMBOL = {"pi": r"\pi", "sigma": r"\sigma", "join": r"\bowtie", "rename": r"\rho",
          "union": r"\cup", "diff": r"\setminus", "intersect": r"\cap"}

def _esc(s):
    """escapa underscore SOLO dentro identificatori, mai nel markup LaTeX circostante."""
    return s.replace("_", r"\_")

def _label(node):
    op = node["op"]
    if op == "table":
        return _esc(node["name"])
    if op == "pi":
        return f"${SYMBOL['pi']}_{{{_esc(','.join(node['attrs']))}}}$"
    if op == "sigma":
        return f"${SYMBOL['sigma']}_{{{_esc(node['cond'])}}}$"
    if op == "rename":
        return f"${SYMBOL['rename']}_{{{_esc(node['map'])}}}$"
    if op == "join":
        return f"${SYMBOL['join']}_{{{_esc(node['cond'])}}}$" if node.get("cond") else f"${SYMBOL['join']}$"
    if op in ("union", "diff", "intersect"):
        return f"${SYMBOL[op]}$"
    raise ValueError(f"op sconosciuto: {op}")

def _forest_node(node):
    lbl = _label(node)
    op = node["op"]
    if op == "table":
        return f"[{{{lbl}}}]"
    if op in ("pi", "sigma", "rename"):
        return f"[{{{lbl}}} {_forest_node(node['child'])}]"
    if op in ("join", "union", "diff", "intersect"):
        return f"[{{{lbl}}} {_forest_node(node['left'])} {_forest_node(node['right'])}]"
    raise ValueError(f"op sconosciuto: {op}")

def render(node, caption=None):
    """Ritorna un frammento .tex con l'albero (richiede \\usepackage{forest} nel preambolo)."""
    tree = _forest_node(node)
    out = []
    if caption:
        out.append(f"\\textbf{{{caption}}}\\par\\smallskip")
    out.append(r"\begin{center}\begin{forest}")
    out.append(r"for tree={draw,rounded corners,minimum height=0.7cm,l sep=10mm,s sep=6mm,font=\small}")
    out.append(tree)
    out.append(r"\end{forest}\end{center}")
    return "\n".join(out)

def check_uses_only_schema(node, known_tables):
    """Validazione minima: le tabelle citate nelle foglie devono esistere nello schema
    (coerenza con la traduzione relazionale prodotta da er.py, non correttezza semantica)."""
    errs = []
    def walk(n):
        if n["op"] == "table":
            if n["name"] not in known_tables:
                errs.append(f"tabella '{n['name']}' citata nell'algebra non esiste nello schema relazionale")
        for k in ("child", "left", "right"):
            if k in n:
                walk(n[k])
    walk(node)
    return errs
