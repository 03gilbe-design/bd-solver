#!/usr/bin/env python3
"""solve.py spec.json [out_dir]  -- pipeline deterministica: valida -> tex -> PDF.
Pure stdlib (gira su Termux). Se pdflatex manca, si ferma ai .tex e lo dice.

Uso tipico su Termux con Claude Code:
  1. Claude legge le foto dell'esame (visione, NO OCR) e scrive out/<nome>.spec.json
  2. python solve.py out/<nome>.spec.json out
"""
import sys, os, subprocess, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "checker"))
import er, render, json

def main():
    if len(sys.argv) < 2:
        print("uso: python solve.py spec.json [out_dir]"); sys.exit(2)
    spec_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "out"
    spec = json.load(open(spec_path, encoding="utf-8"))
    errs = er.check(spec)
    if errs:
        print("SPEC NON VALIDA (correggi prima di procedere):")
        for e in errs: print("  -", e)
        sys.exit(1)
    print("[1/3] spec valida:", len(spec["entita"]), "entita,",
          len(spec.get("relazioni", {})), "relazioni,",
          len(spec.get("isa", [])), "gerarchie")
    render.main_from(spec, out_dir) if hasattr(render, "main_from") else _render(spec_path, out_dir)
    print("[2/3] generati .tex in", out_dir)
    pdflatex = shutil.which("pdflatex") or _miktex_pdflatex()
    if not pdflatex:
        print("[3/3] pdflatex non trovato: PDF saltato. Compila i .tex altrove, oppure")
        print("      su Termux:  pkg install texlive  (poi rilancia)")
        return
    r = subprocess.run([pdflatex, "-interaction=nonstopmode", "-halt-on-error",
                        "soluzione.tex"], cwd=out_dir, capture_output=True, text=True)
    pdf = os.path.join(out_dir, "soluzione.pdf")
    if os.path.exists(pdf):
        print("[3/3] PDF:", pdf)
    else:
        print("[3/3] errore pdflatex:"); print(r.stdout[-800:])
        sys.exit(1)

def _render(spec_path, out_dir):
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "checker", "render.py"),
                    spec_path, out_dir], check=True)

def _miktex_pdflatex():
    p = os.path.expanduser(r"~/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe")
    return p if os.path.exists(p) else None

if __name__ == "__main__":
    main()
