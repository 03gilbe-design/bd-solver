# Far girare il solver su Termux (Android)

La parte deterministica (`checker/*.py`, `solve.py`) è **Python stdlib puro** — nessun `pip install`.
Su Termux gira liscia. Il PDF (pdflatex) è opzionale.

## Setup minimo (una volta)
```bash
pkg update && pkg install python git
git clone <repo>  # oppure copia la cartella BD_Parte1_Solver in ~/
cd BD_Parte1_Solver
python checker/test_er.py       # deve stampare "TUTTI I TEST OK"
python dataset/test_dataset.py  # deve stampare "TUTTI I ... CASI OK"
```

## PDF su Termux (opzionale)
`pkg install texlive` (grosso, ~1-2 GB) porta `pdflatex`. Poi `solve.py` genera il PDF.
Senza texlive, `solve.py` si ferma ai file `.tex` (compilabili altrove / su Overleaf).
Per il QA del PDF serve poppler: `pkg install poppler` (dà `pdffonts`, `pdftotext`, `pdftocairo`).

## Uso con Claude Code su Termux
1. Metti le foto dell'esame in una cartella, es. `~/esame_foto/`.
2. Avvia Claude Code nella cartella `BD_Parte1_Solver`, passagli `~/esame_foto/`.
3. Claude segue `AGENTS.md`: legge le foto (visione, NO OCR), ricompone l'esame, scrive
   `out/<nome>.spec.json`, poi lancia:
   ```bash
   python solve.py out/<nome>.spec.json out
   python checker/pdf_qa.py out/soluzione.pdf   # controllo qualita (font/tofu)
   ```
4. Il diagramma ER e lo schema relazionale escono corretti dal codice, non disegnati a mano.

## Se Termux non basta (fallback SSH)
Stessi comandi su `pclento` o `pcveloce` via SSH (vedi memory worker). Preferenza utente: Termux.

## File pipeline (tutti stdlib)
- `checker/er.py` — check + tikz ER (binarie e n-arie) + traduzione relazionale (N:N, 1:N, 1:1, id esterno, ISA, opt)
- `checker/render.py` — spec → .tex
- `solve.py` — spec → .tex → PDF (pdflatex se presente)
- `checker/pdf_qa.py` — QA PDF: font embedded, niente tofu (), token attesi presenti
- `checker/test_er.py`, `dataset/test_dataset.py` — test
