# BD Parte 1 — Solver esami progettazione (UniVR, Belussi)

Pipeline: **foto esame → spec ER (JSON) → PDF LaTeX** con diagramma ER + schema relazionale, stile prof.
Gira su **Termux** (parte deterministica = Python stdlib puro, niente pip).

## Idea in una riga
Claude legge le foto (visione, **NO OCR**) e produce solo lo **spec** strutturato; il **codice
deterministico** valida, disegna il diagramma ER (sempre corretto) e traduce nel relazionale.
Così si eliminano i due difetti tipici dei PDF generati a mano: diagrammi storti e **simboli mancanti (□)**.

## Flusso
1. **Foto → spec** (Claude, a runtime): vedi `AGENTS.md`. Applica le euristiche di `TRICKS.md`.
2. **spec → PDF** (deterministico):
   ```
   python solve.py out/mio.spec.json out       # check + tex + pdf (pdflatex se presente)
   python checker/pdf_qa.py out/soluzione.pdf   # QA: font embedded, niente □, token presenti
   ```

## Cosa copre la traduzione (parte deterministica)
N:N → tabella · 1:N → FK sul lato "1" · 1:1 → FK sul lato totale · **identificazione esterna**
(id importato, validato (1,1)) · **generalizzazioni ISA** (strategia `figli` o `padre`) ·
attributi **opzionali** (`opt` → nullable) · **relazioni n-arie** (ternarie disegnate + tradotte).

## Prova che funziona (test)
- `python checker/test_er.py` — unit: N:N, 1:N, 1:1, nullable, ISA figli/padre, id esterno, errori validazione.
- `python dataset/test_dataset.py` — casi **reali**: `aeroporto` (verificato contro la **soluzione ufficiale**
  del prof, 1-17_A) e `supermercato` (N:N + ternaria). Confronta proprietà strutturali (tabelle, chiavi,
  nullable, FK), **non i nomi esatti** → non overfittato.
- QA sul PDF: `pdf_qa.py` **boccia** il PDF "generato" precedente (font Symbol/ZapfDingbats non-embedded → □)
  e **promuove** i PDF di questo tool (tutti i font embedded).

## File
- `checker/er.py` — motore: check + tikz (binarie e n-arie, anti-collisione) + traduzione
- `checker/render.py` — spec → .tex · `solve.py` — spec → PDF · `checker/pdf_qa.py` — QA PDF
- `dataset/*.spec.json` + `*.expected.json` + `test_dataset.py` — dataset esami reali
- `corpus_esami/` — 16 prove I parte reali (riferimento, per non overfittare)
- `AGENTS.md` — istruzioni per Claude Code (modulo AI, foto→soluzione)
- `TRICKS.md` — euristiche di progettazione confermate dagli appunti
- `RUNBOOK_TERMUX.md` — come girare su Termux · `DESIGN_NOTES.md` — perché custom vs tool esistenti

## Tipi di esercizio in un esame Belussi (parte 1)
1. Progettazione (testo→ER) ✅ deterministico · 2. Traduzione ER→relazionale ✅ deterministico ·
3. Algebra relazionale · 4. Calcolo relazionale · 5. ER etichettato→schema documenti JSON (dal 2025).
I tipi 3-5 li risolve Claude; il codice valida dove può (attributi esistenti, chiavi coerenti).

## Limiti noti / upgrade path (vedi DESIGN_NOTES.md)
- Attributi non disegnati nel diagramma (lo schema relazionale li elenca tutti con le chiavi).
- Per fedeltà pixel al prof: emettere macro `tikz-er2`. Per diagrammi grandi: layout via Graphviz `neato`.
- ISA n-livello e relazioni ricorsive: traduzione ok, layout da rifinire.
