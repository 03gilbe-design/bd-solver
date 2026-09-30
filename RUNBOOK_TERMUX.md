# Far girare il solver su Termux (Android)

La parte deterministica (`checker/*.py`, `solve.py`) è **Python stdlib puro** — nessun `pip install`.
Su Termux gira liscia. Il PDF (pdflatex) è opzionale.

## Pezzi mancanti/foto poco chiare: vedi `METODO_DOMANDE_APERTE.md`
Contiene il metodo per teoria/SQL (coerente col prof, mai copiato) e le 2
tecniche leggere per dedurre un pezzo illeggibile (constraint propagation per
numeri, fuzzy matching per parole) - implementate e testate in
`checker/pt2_fallback.py`.

## Setup minimo (una volta)
```bash
pkg update && pkg install python git
git clone https://github.com/03gilbe-design/bd-solver.git  # repo vero, allineato al locale
cd BD_Parte1_Solver
python checker/test_er.py       # deve stampare "TUTTI I TEST OK"
python dataset/test_dataset.py  # deve stampare "TUTTI I ... CASI OK"
```

## PDF su Termux — SCONSIGLIATO installare texlive sul telefono
`pkg install texlive` è ~1-2 GB e pesante: su Termux tende a far crashare l'app
(RAM/storage sotto stress). **Default: NON installarlo.** `solve.py` senza texlive
si ferma ai file `.tex` (leggeri, pochi KB) — compilali altrove: Overleaf, o
manda il `.tex` a un PC (pclento/pcveloce) via SSH per la compilazione, tenendo
il telefono solo per la parte leggera (estrazione + solve → `.tex`).
Se proprio serve il PDF sul telefono, prova prima con poca RAM libera chiusa
(altre app), e aspettati che possa comunque crashare - non è affidabile.

**Secondo motivo, confermato 2026-09-14**: anche quando la compilazione su
Termux NON crasha, `pdf_qa.py` ha trovato un font Type3 non incorporato
(rischio glifi mancanti/tofu su altri dispositivi) - stessa pipeline, stesso
`solve.py`, stesso `pdflatex`, ma la distribuzione texlive di Termux e'
piu' minimale di MiKTeX (qui su Windows, testato in locale: nessun problema,
`[PDF QA OK]`). Non e' un bug del codice - e' la differenza fra
distribuzioni texlive. Se il PDF viene compilato su Termux, controllare
SEMPRE con `pdf_qa.py` prima di considerarlo definitivo.

## PASSO 0 — teoria e SQL: controlla PRIMA `riferimenti_teoria/`
Le domande a)/b) (teoria) e c)/d) (SQL) NON hanno un motore - ma spesso sono
GIA' state risolte: 11 gruppi di domande ricorrenti sono gia' mappati.
`riferimenti_teoria/Risposte_Teoria_ParteII.pdf` - 12 risposte di teoria gia'
scritte e verificate (ACID, ripresa, B+-tree, indice primario/secondario/
hashing, VSR/CSR, 2PL, architettura DBMS, ottimizzazione, XML).
`riferimenti_teoria/DOMANDE_NEL_TEMPO.txt` - quali domande tornano uguali
negli anni, con la lista esatta delle parole che le riconoscono.
`riferimenti_teoria/BD_SCHEMI_ESAME.pdf` - pattern SQL (NOT EXISTS per "mai",
doppia negazione per "tutti", COUNT+LEFT JOIN, EXCEPT, self-join, ecc) e VSR/CSR.
`riferimenti_teoria/SQL_ESAMI.txt` + `COMANDI_SQL.txt` - 182 richieste SQL
raggruppate per pattern, con query gia' risolte.
`riferimenti_teoria/soluzioni_prof_originali/` - i PDF ORIGINALI del prof (non
riassunti), gia' verificati parola per parola contro il solver oggi:
2 esercizi di ripresa a caldo risolti, 1 di ottimizzazione (costo query) con
aritmetica completa, 1 di B+-tree, 2 esercitazioni con soluzioni (2015/2016),
1 slide teorica sulle strutture di accesso. Questi sono la fonte primaria -
se serve controllare la convenzione esatta del prof (es. split/merge B+-tree,
formula NP-esterna-una-volta), guardare qui prima di indovinare.
**Se la domanda fotografata matcha uno di questi, copia la risposta - non
riscriverla da zero.** E' successo gia' oggi: a) ACID e b) indice primario di
un esame reale coincidevano parola per parola con quanto gia' scritto qui.

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

**Nota su "test in chat":** dare un file da leggere (es. una foto d'esame) non è di
default un test — è lavoro normale, lo risolvi e basta. Diventa un test SOLO se
l'utente lo dice esplicitamente ("facciamo un test", "verifica che..."). Senza
quella richiesta esplicita, tratta l'input come un esercizio vero da risolvere.

## Se Termux non basta (fallback SSH)
Stessi comandi su `pclento` o `pcveloce` via SSH (vedi memory worker). Preferenza utente: Termux.

## File pipeline (tutti stdlib)
- `checker/er.py` — check + tikz ER (binarie e n-arie) + traduzione relazionale (N:N, 1:N, 1:1, id esterno, ISA, opt)
- `checker/render.py` — spec → .tex
- `solve.py` — spec → .tex → PDF (pdflatex se presente)
- `checker/pdf_qa.py` — QA PDF: font embedded, niente tofu (), token attesi presenti
- `checker/test_er.py`, `dataset/test_dataset.py` — test
