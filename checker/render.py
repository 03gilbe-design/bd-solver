#!/usr/bin/env python3
"""render.py spec.json out_dir  -> genera _er.tex, _rel.tex, soluzione.tex nella out_dir.
Poi compilare con: pdflatex -output-directory=out_dir soluzione.tex"""
import sys, os, re, json, subprocess, shutil
sys.path.insert(0, os.path.dirname(__file__))
import er

STANDALONE_HEADER = r"""\documentclass[border=8pt]{standalone}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric,arrows.meta,positioning}
% font sans-serif (helvetica) invece del serif LaTeX di default - richiesta utente,
% stesso trattamento gia' applicato ai PDF parte 2
\usepackage[scaled=.95]{helvet}\renewcommand{\familydefault}{\sfdefault}
\begin{document}
"""
STANDALONE_FOOTER = r"\end{document}" + "\n"

def _find_pdflatex():
    return shutil.which("pdflatex") or (
        os.path.expanduser(r"~/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe")
        if os.path.exists(os.path.expanduser(r"~/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe"))
        else None)

def compile_er_standalone(er_code, out_dir):
    """Compila il diagramma ER come documento 'standalone' A SE' (pagina dimensionata
    esattamente sul contenuto, zero shrink, testo a grandezza naturale - la classe standalone
    e' fatta apposta per questo, trovato cercando online la soluzione al problema 'testo
    minuscolo sui diagrammi grandi'; i tentativi con \\pdfpagewidth+\\textwidth a mano
    rompevano il documento, vedi DESIGN_NOTES.md Aggiornamento 6-7).
    Ritorna True se compilato, False altrimenti (fallback: adjustbox nel documento principale)."""
    pdflatex = _find_pdflatex()
    if not pdflatex:
        return False
    tex_path = os.path.join(out_dir, "_er_standalone.tex")
    open(tex_path, "w", encoding="utf-8").write(STANDALONE_HEADER + er_code + "\n" + STANDALONE_FOOTER)
    try:
        r = subprocess.run([pdflatex, "-interaction=nonstopmode", "-halt-on-error",
                            "_er_standalone.tex"], cwd=out_dir, capture_output=True, text=True, timeout=30)
    except Exception:
        return False
    return os.path.exists(os.path.join(out_dir, "_er_standalone.pdf"))

FK_COLORS = ["red!70!black", "blue!70!black", "green!55!black", "orange!85!black",
             "violet", "teal", "magenta!80!black", "brown"]

def rel_to_latex(txt):
    """Vincoli FK COLORATI (richiesta utente, stile prof: nelle soluzioni ufficiali i
    collegamenti FK sono evidenziati con frecce/riquadri colorati, un colore per vincolo)."""
    out = []
    fk_i = 0
    for ln in txt.splitlines():
        if ln.startswith("%"):
            continue
        if not ln.strip():
            out.append(r"\par\medskip"); continue
        ln = ln.replace("_", r"\_")   # escapa gli underscore VERI nei nomi
        # ora converte i marcatori chiave \x01..\x02 in underline
        ln = re.sub("\x01(.+?)\x02", lambda m: r"\underline{" + m.group(1) + "}", ln)
        ln = ln.replace("*", r"$^{*}$")
        if "->" in ln:
            color = FK_COLORS[fk_i % len(FK_COLORS)]
            fk_i += 1
            ln = ln.replace("->", r"$\rightarrow$")
            out.append(r"\textcolor{" + color + "}{" + ln + r"}\par")
        else:
            ln = ln.replace("->", r"$\rightarrow$")
            out.append(ln + r"\par")
    return "\n".join(out)

HEADER = r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=2cm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric,arrows.meta,positioning}
\usepackage{amsmath}
\usepackage{adjustbox}
\usepackage{forest}
\usepackage{pdflscape}
\usepackage{pdfpages}
% font sans-serif (helvetica) invece del serif LaTeX di default - richiesta utente
\usepackage[scaled=.95]{helvet}\renewcommand{\familydefault}{\sfdefault}
\begin{document}
\begin{center}\Large\textbf{Basi di Dati --- Soluzione esame}\end{center}
"""
FOOTER = r"\end{document}" + "\n"

# _es1.tex: esercizio 1 del testo originale (es. superchiave + traduzione schema dato) -
# esiste SEMPRE nel testo esame PRIMA dell'esercizio di progettazione. Se manca, l'esame
# generato e' INCOMPLETO anche se sezioni 1-2 (progettazione) sono perfette: errore reale
# fatto una volta (esame_completo_5sezioni conteneva solo la progettazione, spacciata per
# "esame completo"). Controllare sempre che il testo letto dalle foto abbia un esercizio 1
# prima di quello di progettazione.
PRE_SECTION = ("_es1.tex", "1. Esercizio dato (schema fornito nel testo)")

# Sezioni 3-5 (algebra/calcolo relazionale, ER etichettato->documenti) NON hanno motore
# deterministico: le scrive Claude come frammento LaTeX in out_dir/_algebra.tex etc.
# Se il file esiste al momento del render, la sezione viene inclusa nel PDF finale;
# altrimenti viene saltata silenziosamente (esame senza quell'esercizio).
OPTIONAL_SECTIONS = [
    ("_algebra.tex",   "Algebra relazionale ottimizzata"),
    ("_calcolo.tex",   "Calcolo relazionale"),
    ("_documenti.tex", "Schema dei documenti (da ER etichettato)"),
]

def build_template(out_dir, standalone_ok=False):
    """Numerazione dinamica: se _es1.tex esiste, progettazione diventa sezione 2-3, altrimenti
    1-2. Cosi' l'esame generato riflette solo cio' che e' STATO davvero risolto, senza saltare
    numeri o fingere sezioni assenti.
    standalone_ok=True: _er_standalone.pdf e' stato compilato (classe 'standalone', pagina
    dimensionata esattamente sul diagramma, ZERO shrink, testo a grandezza naturale) -
    incluso con \\includepdf (pdfpages) come pagina a se'. Fallback (standalone_ok=False):
    adjustbox con shrink-to-fit su A4 (testo piu' piccolo su diagrammi grandi, ma sempre
    funzionante). Vedi DESIGN_NOTES.md Aggiornamento 6-7 per il percorso di ricerca."""
    parts = [HEADER]
    n = 1
    if os.path.exists(os.path.join(out_dir, PRE_SECTION[0])):
        parts.append(f"\\section*{{{n}. Esercizio dato (schema fornito nel testo)}}\n\\input{{{PRE_SECTION[0]}}}\n")
        n += 1
    parts.append(f"\\section*{{{n}. Schema concettuale (ER)}}\n")
    if standalone_ok:
        parts.append(r"\includepdf[pages=-,fitpaper=true]{_er_standalone.pdf}" "\n")
    else:
        parts.append(r"\begin{center}\begin{adjustbox}{max width=\textwidth,max totalheight=0.92\textheight}\input{_er.tex}\end{adjustbox}\end{center}" "\n")
    n += 1
    parts.append(f"\\section*{{{n}. Schema relazionale}}\n{{\\ttfamily\\small\\input{{_rel.tex}}}}\n")
    n += 1
    for fname, title in OPTIONAL_SECTIONS:
        if os.path.exists(os.path.join(out_dir, fname)):
            parts.append(f"\\section*{{{n}. {title}}}\n\\input{{{fname}}}\n")
            n += 1
    parts.append(FOOTER)
    return "".join(parts)

def main():
    spec_path, out_dir = sys.argv[1], sys.argv[2]
    spec = json.load(open(spec_path, encoding="utf-8"))
    errs = er.check(spec)
    if errs:
        print("SPEC NON VALIDA:", *errs, sep="\n  - ", file=sys.stderr); sys.exit(1)
    os.makedirs(out_dir, exist_ok=True)
    er_code = er.tikz(spec)
    open(os.path.join(out_dir, "_er.tex"), "w", encoding="utf-8").write(er_code)
    standalone_ok = compile_er_standalone(er_code, out_dir)
    rel = er.rel_text(er.translate(spec))
    open(os.path.join(out_dir, "_rel.tex"), "w", encoding="utf-8").write(rel_to_latex(rel))
    open(os.path.join(out_dir, "soluzione.tex"), "w", encoding="utf-8").write(build_template(out_dir, standalone_ok))
    extra = [f for f, _ in OPTIONAL_SECTIONS if os.path.exists(os.path.join(out_dir, f))]
    print("generati _er.tex, _rel.tex, soluzione.tex in", out_dir,
          f"(+ {len(extra)} sezioni extra: {extra})" if extra else "(solo sezioni 1-2, nessun _algebra/_calcolo/_documenti.tex trovato)")

if __name__ == "__main__":
    main()
