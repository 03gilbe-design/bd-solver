#!/usr/bin/env python3
"""solve_pt2.py spec.json out_dir — genera soluzione.tex(+pdf se pdflatex disponibile)
per un esame III prova (parte 2), a partire da uno spec JSON generico.

Spec format:
{
  "titolo": "Recupero III prova 23 giugno 2025",
  "esercizi": [
    {"tipo": "ripresa", "id": "d", "titolo": "Gestore dell'affidabilita'", "punti": 4,
     "log": "B(T1), B(T2), ..."},
    {"tipo": "schedule", "id": "e", "titolo": "Esecuzione concorrente", "punti": 6,
     "schedule": "r2(y), w3(z), ..."},
    {"tipo": "costo", "id": "f", "titolo": "Ottimizzazione", "punti": 5,
     "descrizione": "Ordine join: A join B (NLJ, 1 pagina di buffer).",
     "parametri": {"np_outer":..., "nr_outer":..., "val_sel_outer":...,
                    "np_inner":..., "pagine_sel_inner":..., "nr_sel_inner":...,
                    "val_join_inner":..., "prof_indice": 3}},
    {"tipo": "btree", "id": "g", "titolo": "B+-tree", "punti": 5,
     "fanout": 5, "foglie": [["A","D","F","G"], ...],
     "operazioni": [{"op":"insert","key":"B"}, {"op":"delete","key":"Z"}]}
  ]
}
Tipi non riconosciuti (es. teoria pura senza formula) vanno semplicemente omessi dallo
spec: questo script risolve solo cio' che ha un motore deterministico dietro."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt2_render

PAGINA_A4 = r"""\documentclass[11pt]{article}\usepackage[a4paper,margin=2cm]{geometry}"""
# --verticale: colonna stretta da scorrere (telefono/schermo lontano), sfondo nero, caratteri grandi
PAGINA_VERTICALE = r"""\documentclass[12pt]{article}
\usepackage[paperwidth=13cm,paperheight=34cm,margin=0.8cm]{geometry}
% colonna stretta: a sinistra e senza sillabare (senza babel italiano TeX sillabava all'inglese: "in-iziale")
\AtBeginDocument{\raggedright\hyphenpenalty=10000\exhyphenpenalty=10000%
\pagecolor{black}\color{white}\large\definecolor{sol}{RGB}{110,200,255}%
\definecolor{opB}{RGB}{90,220,120}\definecolor{opC}{RGB}{120,180,255}\definecolor{opA}{RGB}{255,110,110}%
\definecolor{opCK}{RGB}{255,185,60}\definecolor{t1}{RGB}{255,110,110}\definecolor{t2}{RGB}{120,180,255}%
\definecolor{t3}{RGB}{90,220,120}\definecolor{t4}{RGB}{230,130,255}\definecolor{t0}{RGB}{190,190,190}}"""
# --quadretti: A4 a quadretti da 5 mm. Margini = 3 quadretti, area testo = 36x53 quadretti:
# ogni riga di testo sta SU una linea della griglia (interlinea fissa 5 mm per TUTTE le misure di
# carattere), grafi/alberi occupano un numero intero di quadretti; a fine pagina TeX sposta intero
# cio' che non ci sta e la pagina nuova riparte allineata (textheight = topskip + 52 righe).
PAGINA_QUADRETTI = r"""\documentclass[10pt]{article}
\usepackage[a4paper,top=15mm,left=15mm,textwidth=180mm,textheight=265mm,headheight=0pt,headsep=0pt,footskip=8mm]{geometry}"""
QUADRETTI = r"""
\definecolor{griglia}{RGB}{185,200,225}
\AddToHook{shipout/background}{\put(0,0){\setlength\unitlength{5mm}\color{griglia}\linethickness{0.2pt}%
\multiput(0,0)(0,-1){60}{\line(1,0){42}}\multiput(0,0)(1,0){43}{\line(0,-1){60}}}}
\makeatletter
\renewcommand\normalsize{\fontsize{10}{5mm}\selectfont}\renewcommand\small{\fontsize{9}{5mm}\selectfont}
\renewcommand\footnotesize{\fontsize{8.5}{5mm}\selectfont}\renewcommand\scriptsize{\fontsize{7}{5mm}\selectfont}
\renewcommand\large{\fontsize{11}{5mm}\selectfont}\renewcommand\Large{\fontsize{12}{5mm}\selectfont}
\def\@listi{\leftmargin\leftmargini\topsep\z@\parsep\z@\itemsep\z@\partopsep\z@}\let\@listI\@listi
\makeatother
\setlength\topskip{5mm}\setlength\parskip{0pt}\setlength\lineskiplimit{-\maxdimen}
\setlength\smallskipamount{0pt}\setlength\medskipamount{5mm}\setlength\bigskipamount{5mm}
\renewenvironment{center}{\par\centering}{\par}
% figura = box alto un numero INTERO di quadretti, appoggiato sulla riga di base precedente
\renewcommand\figura[1]{\par\ifdim\prevdepth>0pt\vskip-\prevdepth\fi\nointerlineskip
\sbox\fitbox{\fitw{#1}}%
\vbox to \numexpr(\dimexpr\ht\fitbox+\dp\fitbox+2.5mm-1sp\relax)/\dimexpr5mm\relax\dimexpr5mm\relax
{\vss\hbox to\linewidth{\usebox\fitbox\hss}\vss}\prevdepth=0pt}
% figure allineate al bordo della griglia (il centraggio lo fa il disegno, in quadretti interi);
% rientri = multipli di 5 mm, cosi' ogni inizio riga sta su una linea verticale della griglia
\setlength\parindent{5mm}\setlength\leftmargini{10mm}\renewcommand\quad{\hspace*{5mm}}
\renewenvironment{soluzione}{\par\color{sol}\setlength{\leftskip}{5mm}%
\noindent{\scriptsize\textbf{SOLUZIONE}}\par}{\par}
% quaderno: 1 carattere = 1 quadretto (box largo 5 mm), 1 riga = 1 riga della griglia
% la maiuscola RIEMPIE il quadretto: altezza maiuscole (0.718 em in Helvetica) = 4.9 mm -> 19.4 pt;
% lettere piu' larghe di 4.4 mm (M, W) strette in orizzontale; accentate (È) rimpicciolite per stare dentro.
% \qs = mezzo quadretto (I, 1, punteggiatura, spazio)
\newsavebox\qb
% accenti SOPRA il quadretto (nella riga vuota), come a mano: la lettera resta alta quanto il quadretto
\newcommand\qfit[2]{\sbox\qb{\fontsize{19.4}{5mm}\selectfont #2}\makebox[#1][c]{%
\ifdim\wd\qb>\dimexpr#1-0.6mm\relax\resizebox{\dimexpr#1-0.6mm\relax}{\height}{\usebox\qb}\else\usebox\qb\fi}}
\newcommand\q[1]{\qfit{5mm}{#1}}\newcommand\qs[1]{\qfit{2.5mm}{#1}}
\newcommand\qline[1]{\par\noindent\hbox to\linewidth{#1\hss}\par}
"""

HEADER = r"""
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{amsmath}\usepackage{tikz}
% font sans-serif (helvetica) come nei testi d'esame del prof (Calibri-like)
\usepackage[scaled=.95]{helvet}\renewcommand{\familydefault}{\sfdefault}
\usetikzlibrary{arrows.meta,positioning}
\setlength\emergencystretch{2em}
% risposta distinta dal testo d'esame: testo blu "penna" rientrato + etichetta, stesso font.
% ponytail: niente framed/barra - framed perdeva la barra sull'ultimo pezzo a fine pagina (30/09);
% leftskip non si rompe mai e non serve nessun pacchetto extra su Termux.
\usepackage{xcolor}\definecolor{sol}{RGB}{20,60,150}
% --colori: B verde, C blu, A rosso, CK arancio; schedule colorato per transazione t0..t7
\definecolor{opB}{RGB}{0,140,60}\definecolor{opC}{RGB}{0,90,200}\definecolor{opA}{RGB}{200,30,30}
\definecolor{opCK}{RGB}{210,110,0}\definecolor{t0}{RGB}{110,110,110}\definecolor{t1}{RGB}{200,30,30}
\definecolor{t2}{RGB}{0,90,200}\definecolor{t3}{RGB}{0,140,60}\definecolor{t4}{RGB}{160,0,160}
\definecolor{t5}{RGB}{210,110,0}\definecolor{t6}{RGB}{0,140,150}\definecolor{t7}{RGB}{120,80,0}
\newenvironment{soluzione}{\par\color{sol}\setlength{\leftskip}{12pt}%
\noindent{\scriptsize\textbf{SOLUZIONE}}\par\smallskip}{\par}
% grafi/alberi: se piu' larghi della colonna si rimpiccioliscono (serve in --verticale)
\usepackage{graphicx}\newsavebox\fitbox
\newcommand\fitw[1]{\sbox\fitbox{#1}\ifdim\wd\fitbox>\linewidth\resizebox{\linewidth}{!}{\usebox\fitbox}\else\usebox\fitbox\fi}
\newcommand\figura[1]{\begin{center}\fitw{#1}\end{center}}
"""

def build_tex(spec, verticale=False, quadretti=False):
    L = [PAGINA_QUADRETTI if quadretti else PAGINA_VERTICALE if verticale else PAGINA_A4, HEADER,
         QUADRETTI if quadretti else "", "\\begin{document}\n"]
    # quadretti: il testo d'ESAME resta stampato normale (sulle righe); solo la SOLUZIONE, cioe' quello
    # che si scrive a mano, va nel quaderno: 1 carattere = 1 quadretto, in maiuscolo (richiesta jeans 30/09)
    def q(s):
        i = s.find("\\begin{soluzione}")
        return s if not quadretti or i < 0 else s[:i] + pt2_render.quaderno(s[i:])
    L.append("\\begin{center}\\Large\\textbf{" + pt2_render.esc(spec["titolo"]) + "}\\end{center}\n")
    if spec.get("sottotitolo"):
        L.append("\\small " + pt2_render.esc(spec["sottotitolo"]) + "\\par\\bigskip\n")
    for ex in spec["esercizi"]:
        if ex["tipo"] not in pt2_render.RENDERERS:
            continue
        L.append(q(pt2_render.render_esercizio(ex)))
        if pt2_render.MINIMAL and ex["tipo"] == "teoria" and not ex.get("risposta_minimal"):
            n = len(" ".join(ex.get("risposta", [])).split())
            lim = 35 * ex.get("punti", 3)   # = minimo di teoria.py: piu' corta possibile ma con tutti i punti
            if n > lim:
                print(f"AVVISO minimal: teoria {ex.get('id')}) {n} parole (> {lim}): aggiungi 'risposta_minimal' "
                      "allo spec (tutti i punti di teoria.py, ~35 parole/punto)")
    L.append("\\end{document}\n")
    return "".join(L)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pt2_render.MINIMAL = "--minimal" in sys.argv
    pt2_render.COLORI = "--colori" in sys.argv
    verticale, quadretti = "--verticale" in sys.argv, "--quadretti" in sys.argv
    pt2_render.QUADRETTI = quadretti
    nero = "--nero" in sys.argv          # penna nera "reale" invece del blu
    if len(args) < 2:
        print("uso: solve_pt2.py spec.json out_dir [--minimal] [--verticale|--quadretti] [--colori]"); sys.exit(1)
    spec_path, out_dir = args[0], args[1]
    spec = json.load(open(spec_path, encoding="utf8"))
    os.makedirs(out_dir, exist_ok=True)
    tex = build_tex(spec, verticale, quadretti)
    if nero:
        tex = tex.replace("\\begin{document}", "\\definecolor{sol}{RGB}{25,25,30}\\begin{document}", 1)
    tex_path = os.path.join(out_dir, "soluzione.tex")
    open(tex_path, "w", encoding="utf8").write(tex)
    print(f"scritto {tex_path}")
    try:
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "soluzione.tex"],
                        cwd=out_dir, check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"compilato {os.path.join(out_dir, 'soluzione.pdf')}")
    except Exception as e:
        print(f"pdflatex non disponibile o fallito ({e}); solo .tex scritto")

if __name__ == "__main__":
    main()
