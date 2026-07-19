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

HEADER = r"""\documentclass[11pt]{article}\usepackage[a4paper,margin=2cm]{geometry}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{amsmath}\usepackage{tikz}
% font sans-serif (helvetica) come nei testi d'esame del prof (Calibri-like)
\usepackage[scaled=.95]{helvet}\renewcommand{\familydefault}{\sfdefault}
\usetikzlibrary{arrows.meta,positioning}\begin{document}
"""

def build_tex(spec):
    L = [HEADER]
    L.append("\\begin{center}\\Large\\textbf{" + pt2_render.esc(spec["titolo"]) + "}\\end{center}\n")
    if spec.get("sottotitolo"):
        L.append("\\small " + pt2_render.esc(spec["sottotitolo"]) + "\\par\\bigskip\n")
    for ex in spec["esercizi"]:
        if ex["tipo"] not in pt2_render.RENDERERS:
            continue
        L.append(pt2_render.render_esercizio(ex))
    L.append("\\end{document}\n")
    return "".join(L)

def main():
    if len(sys.argv) < 3:
        print("uso: solve_pt2.py spec.json out_dir"); sys.exit(1)
    spec_path, out_dir = sys.argv[1], sys.argv[2]
    spec = json.load(open(spec_path, encoding="utf8"))
    os.makedirs(out_dir, exist_ok=True)
    tex = build_tex(spec)
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
