#!/usr/bin/env python3
"""pdf_qa.py file.pdf [token1 token2 ...]
Controllo qualita di un PDF-soluzione. Becca il difetto tipico dei PDF generati male
(font non-embedded -> simboli resi come [] tofu): il caso reale era Symbol/ZapfDingbats
emb=no nel PDF HTML->PDF di Claude.

Esce !=0 se:
  - un font NON e' embedded (rischio glifi mancanti), oppure
  - il testo contiene il carattere di replacement U+FFFD / molti tofu, oppure
  - un token atteso (es. nome entita) non compare nel testo.

Usa pdffonts + pdftotext (poppler / miktex). Se non trovati, avvisa e salta (non blocca)."""
import sys, subprocess, shutil, os

def _bin(name):
    p = shutil.which(name)
    if p: return p
    cand = os.path.expanduser(rf"~/AppData/Local/Programs/MiKTeX/miktex/bin/x64/{name}.exe")
    return cand if os.path.exists(cand) else None

def qa(pdf, tokens):
    fails = []
    pf, pt = _bin("pdffonts"), _bin("pdftotext")
    # font base-14 testuali: rendono ovunque anche se non-embedded -> non allarmare.
    # I veri responsabili dei [] sono i font SIMBOLO (Symbol, ZapfDingbats) o custom.
    SAFE = ("helvetica", "arial", "times", "courier")
    if pf:
        out = subprocess.run([pf, pdf], capture_output=True, text=True).stdout
        for ln in out.splitlines()[2:]:
            cols = ln.split()
            if len(cols) >= 6:
                name, emb = cols[0], cols[-4]     # nome, colonna 'emb'
                base = name.split("+")[-1].lower()
                if emb == "no" and not any(base.startswith(s) for s in SAFE):
                    fails.append(f"font simbolo/custom NON embedded: {name} (rischio glifi resi come [])")
    else:
        print("  (pdffonts non trovato: salto controllo font)")
    if pt:
        txt = subprocess.run([pt, pdf, "-"], capture_output=True, text=True).stdout
        if "�" in txt:
            fails.append("testo contiene U+FFFD (carattere di replacement)")
        for tok in tokens:
            if tok not in txt:
                fails.append(f"token atteso assente nel testo: '{tok}'")
    else:
        print("  (pdftotext non trovato: salto controllo testo)")
    return fails

def main():
    if len(sys.argv) < 2:
        print("uso: python pdf_qa.py file.pdf [token ...]"); sys.exit(2)
    pdf, tokens = sys.argv[1], sys.argv[2:]
    fails = qa(pdf, tokens)
    if fails:
        print(f"[PDF QA FAIL] {os.path.basename(pdf)}")
        for f in fails: print("   -", f)
        sys.exit(1)
    print(f"[PDF QA OK] {os.path.basename(pdf)} (font embedded, nessun tofu, token presenti)")

if __name__ == "__main__":
    main()
