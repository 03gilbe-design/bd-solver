# BD Solver — esami Basi di Dati (UniVR)

Repo unica per **entrambe le parti** dell'esame:
- **Parte 1** (progettazione, prof. Belussi): foto esame → spec ER (JSON) → PDF LaTeX con diagramma ER
  + schema relazionale, stile prof.
- **Parte 2** (tecnologie, prof.ssa Migliorini): spec JSON (schedule/log/parametri) → PDF LaTeX con
  esecuzione concorrente (VSR/CSR/2PL), ripresa a caldo, B+-tree, costo query — motori in `checker/pt2_*.py`.

Entrambe girano su **Termux** (parte deterministica = Python stdlib puro, niente pip).

---

## Parte 1 — Progettazione ER

### Idea in una riga
Claude legge le foto (visione, **NO OCR**) e produce solo lo **spec** strutturato; il **codice
deterministico** valida, disegna il diagramma ER (sempre corretto) e traduce nel relazionale.
Così si eliminano i due difetti tipici dei PDF generati a mano: diagrammi storti e **simboli mancanti (□)**.

### Flusso
1. **Foto → spec** (Claude, a runtime): vedi `AGENTS.md`. Applica le euristiche di `TRICKS.md`.
2. **spec → PDF** (deterministico):
   ```
   python solve.py out/mio.spec.json out       # check + tex + pdf (pdflatex se presente)
   python checker/pdf_qa.py out/soluzione.pdf   # QA: font embedded, niente □, token presenti
   ```

### Cosa copre la traduzione (parte deterministica)
N:N → tabella · 1:N → FK sul lato "1" · 1:1 → FK sul lato totale · **identificazione esterna**
(id importato, validato (1,1)) · **generalizzazioni ISA** (strategia `figli` o `padre`) ·
attributi **opzionali** (`opt` → nullable) · **relazioni n-arie** (ternarie disegnate + tradotte).

### Prova che funziona (test)
- `python checker/test_er.py` — unit: N:N, 1:N, 1:1, nullable, ISA figli/padre, id esterno, errori validazione.
- `python dataset/test_dataset.py` — casi **reali**: `aeroporto` (verificato contro la **soluzione ufficiale**
  del prof, 1-17_A) e `supermercato` (N:N + ternaria). Confronta proprietà strutturali (tabelle, chiavi,
  nullable, FK), **non i nomi esatti** → non overfittato.
- QA sul PDF: `pdf_qa.py` **boccia** il PDF "generato" precedente (font Symbol/ZapfDingbats non-embedded → □)
  e **promuove** i PDF di questo tool (tutti i font embedded).

### Tipi di esercizio in un esame Belussi
1. Progettazione (testo→ER) ✅ deterministico · 2. Traduzione ER→relazionale ✅ deterministico ·
3. Algebra relazionale · 4. Calcolo relazionale · 5. ER etichettato→schema documenti JSON (dal 2025).
I tipi 3-5 li risolve Claude; il codice valida dove può (attributi esistenti, chiavi coerenti).

---

## Parte 2 — Tecnologie (VSR/CSR/2PL, ripresa a caldo, B+-tree, costo query)

### Motori deterministici (`checker/pt2_*.py`)
- **`pt2_schedule.py`** — conflitti, grafo, CSR/VSR/nonSR, ordini seriali equivalenti, test 2PL.
- **`pt2_ripresa.py`** — ripresa a caldo: 5 passi (CK → UNDO/REDO → azioni a ritroso/in avanti).
- **`pt2_btree.py`** — B+-tree: build/insert(split)/delete(merge/redistribuzione), fan-out generico.
- **`pt2_costo.py`** — costo Nested Loop Join (con/senza indice B+-tree), casi selezione interna/esterna.
- **`pt2_extract.py`** — estrazione **deterministica** (regex, NO OCR/LLM) di schedule/log/parametri da
  testo `pdftotext`, per stress-test automatico su esami reali.

### Pipeline spec → PDF
```
python checker/solve_pt2.py dataset_pt2/mio_esame.spec.json out_dir
```
Spec JSON con esercizi di tipo `ripresa`/`schedule`/`costo`/`btree`/`teoria` (vedi `AGENTS.md` sezione
PARTE 2 per il formato completo). Render TikZ a cono con frecce, stile testo d'esame del prof
(font sans-serif, titoli sottolineati).

### Prova che funziona (test)
Tutti in `checker/`, uno per motore + audit + confronto con **soluzioni ufficiali**:
```
python checker/test_pt2_schedule.py
python checker/test_pt2_ripresa.py
python checker/test_pt2_btree.py
python checker/test_pt2_costo.py
python checker/test_pt2_audit_slide.py        # ogni motore confrontato regola-per-regola con le SLIDE di teoria
python checker/test_pt2_esercitazione2015.py  # 3/3 match esatto vs PDF soluzioni ufficiali (ground truth)
python checker/test_pt2_esercitazione2016.py  # 3/3 match esatto vs PDF soluzioni ufficiali (ground truth)
```
- **Bug reale trovato e fissato** confrontando con Esercitazione_2015: scelta fratello sx/dx nel merge
  B+-tree per un nodo di mezzo ora preferisce il lato che dà un vero merge (come fa il prof).
- **Bug reale trovato e fissato** confrontando con Esercitazione_2016 (fan-out pari): formula min-chiavi
  foglia sbagliata per fan-out pari, ora `ceil((f-1)/2)` come da teoria.
- **Limite noto, non nascosto**: `pt2_costo.py` gestisce solo join a 2 tabelle (Esercitazione_2015 ha un
  join a 3 tabelle, non ancora implementato — vedi commento nel file).

### Estrazione automatica su corpus reale
`test_pt2_batch_estrazione.py` scandisce testo `pdftotext -layout` (nessuna OCR: PDF testo-nativi) di
**53 esami reali**, estrae schedule/parametri via regex e li esegue sui motori:
```
TXT_DIR=/percorso/txt python checker/test_pt2_batch_estrazione.py
```
Risultato più recente: **14 schedule + 2 calcoli costo** estratti automaticamente ed eseguiti senza
errori, inclusi esami mai controllati a mano (verifica di robustezza, non di correttezza — dove non
c'è soluzione ufficiale il risultato va comunque riletto).

---

## File principali
- `checker/er.py`, `render.py`, `solve.py`, `pdf_qa.py` — motore/pipeline/QA parte 1
- `checker/pt2_*.py`, `solve_pt2.py` — motori/pipeline parte 2
- `dataset/`, `dataset_pt2/` — spec + expected + test, entrambe le parti
- `corpus_esami/` — prove reali parte 1 (riferimento, per non overfittare)
- `AGENTS.md` — istruzioni per Claude Code (entrambe le parti, protocollo foto→soluzione)
- `TRICKS.md`, `TEORIA_CHECKLIST.md`, `GAPS.md`, `DESIGN_NOTES.md` — euristiche/limiti/decisioni
- `RUNBOOK_TERMUX.md` — come girare su Termux

## Limiti noti / upgrade path (vedi DESIGN_NOTES.md e GAPS.md)
- Parte 1: attributi non disegnati nel diagramma (lo schema relazionale li elenca tutti con le chiavi);
  ISA n-livello e relazioni ricorsive con layout da rifinire.
- Parte 2: `pt2_costo.py` solo join a 2 tabelle; nessuna teoria ufficiale locale per l'algoritmo di
  ripresa a caldo (verificato solo contro esercizi risolti, non contro slide dedicate).
