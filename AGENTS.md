# Modulo AI — comporre e risolvere un esame BD parte 1 da foto (per Claude Code su Termux)

Sessione fredda: leggi TUTTO questo file prima di iniziare, non serve altro contesto.
**Claude Code legge direttamente le foto** (visione nativa, niente OCR/Tesseract) e ricostruisce
l'esame. La cartella `BD_Parte1_Solver` contiene un motore deterministico Python stdlib-puro
(nessun `pip install`, funziona su Termux) per la parte verificabile (progettazione+traduzione).

## Input
L'utente dice "ho foto in galleria" o passa una cartella. Una prova può essere sparsa su più
immagini, storte/parziali. Aspettati foto multiple, ordina per timestamp nel nome file.

## Procedura, in ordine

### 1. Leggi TUTTE le foto, ricostruisci il testo
Segnala parti illeggibili invece di inventarle.

**ATTENZIONE — un esame ha quasi sempre 2 facciate (fronte/retro).** Se il conteggio foto è
basso rispetto al testo visibile, o l'ultimo esercizio finisce a metà frase, **manca il retro**
— chiedi foto aggiuntive invece di consegnare una soluzione parziale spacciata per completa.
Verifica che l'ultimo esercizio letto abbia una fine logica (punteggio, domanda chiusa).

### 2. Identifica gli esercizi presenti
Un esame Belussi completo ha FINO A 5 tipi (raramente tutti insieme — leggi bene cosa c'è):

1. **Esercizio dato** (spesso primo, breve): superchiave, traduzione di un piccolo schema
   R1/R2 già fornito, oppure — **il contrario** — "dato lo schema relazionale seguente [...]
   riportare lo schema concettuale". Quest'ultimo è REVERSE ENGINEERING, vedi sezione dedicata.
2. **Progettazione** (testo lungo → schema concettuale ER) — deterministico
3. **Traduzione** ER → schema relazionale — deterministico
4. **Algebra relazionale** ottimizzata
5. **Calcolo relazionale**
6. **ER etichettato → schema documenti** (JSON, dal 2025)

Non forzare tutte le sezioni se l'esame non le ha: il template si adatta a quello che c'è
(vedi sotto, sezioni opzionali).

### 3. Progettazione + traduzione (esercizi 2-3): SEMPRE via codice deterministico
Non disegnare l'ER a mano, non scrivere lo schema relazionale a mano — produci solo lo **spec
JSON**, il codice fa il resto sempre corretto.

```bash
# scrivi out/<nome>.spec.json (formato completo documentato in cima a checker/er.py)
python solve.py out/<nome>.spec.json out
```

`solve.py` valida (`er.check`), genera il diagramma ER (TikZ, layout automatico) e la
traduzione relazionale, compila il PDF. Se il check dà errori, **correggi lo spec finché è
valido** — è il tuo controllo anti-errore, non ignorarlo né aggirarlo.

Applica le euristiche di `TRICKS.md` per leggere il testo → spec (cardinalità default quando
il testo tace, identificazione esterna, ternarie da "per ogni X per ogni Y per ogni Z", ISA
da liste di sottotipi, regola cardinalità minima).

### 3bis. Esercizio "dato lo schema relazionale, risali al concettuale" (REVERSE)
Se il testo ti dà tabelle con PK/FK e chiede lo schema concettuale (verso opposto del solito):
usa `checker/reverse_er.py` — motore euristico **verificato** contro trascrizioni ufficiali
reali (non solo dedotto). Regole (leggi il docstring del file per i dettagli):
- FK fuori dalla PK → relazione 1:N (nullable→(0,1), NOT NULL→(1,1))
- FK = **1 sola**, copre **parte** della PK → **identificazione esterna** (entità debole),
  cardinalità fissa: debole=(1,1), owner=(0,N)
- FK = 1 sola, copre **tutta** la PK → relazione 1:1/estensione, (1,1)-(0,1)
- FK = **2+**, insieme coprono la PK → relazione **N-aria pura**, cardinalità default
  **(0,N) su ogni lato**
- FK multi-colonna verso un target → quelle colonne SONO la PK vera del target (correggi
  l'assunzione "PK = primo attributo" se il testo non la specifica esplicitamente)

```python
import sys; sys.path.insert(0, "checker")
import reverse_er as rv
tables = {"R1": {"pk": [...], "fk": [(["col"], "R2")], "attrs": [...], "nullable": [...]}, ...}
notes, er = rv.infer_er(tables)   # notes = spiegazione leggibile, er = struttura
```
Poi trasforma `er["entita"]`/`er["relazioni"]` nello spec JSON standard e passa da `solve.py`
come sopra — anche il reverse-engineering finisce nel motore deterministico normale.

### 4. Sottolineato vs asterisco nello schema relazionale (regola esatta, verificata)
Quando scrivi/controlli manualmente uno schema relazionale (o leggi la soluzione ufficiale
per confronto), la convenzione è:

| Caso | Sottolineato (parte PK)? | Quando NOT NULL vs asterisco |
|---|---|---|
| FK sul lato "molti" di una 1:N normale | **NO** | asterisco solo se quel lato ha min=0 |
| Identificazione esterna (entità debole) | **SÌ** | — |
| ISA strategia "figli" (chiave ereditata dal padre) | **SÌ** | — |
| Tabella N:N / n-aria pura (tutte le FK che la compongono) | **SÌ** | attributi propri asterisco se opzionali |
| Relazione n-aria **assorbita** in un'entità (un lato ha max=1) | **NO** | asterisco se quel lato ha min=0 |

Il motore (`er.py`) applica già questa regola automaticamente nella traduzione — non serve
applicarla a mano se usi `solve.py`, ma serve per CONTROLLARE una soluzione o leggerne una.

### 5. Relazioni n-arie: tabella propria O assorbita, dipende dalla cardinalità
Se una relazione a 3+ entità ha **tutti i lati max=N** → genera tabella propria (PK = tutte
le FK). Se **esattamente un lato ha max=1** → si **assorbe** in quell'entità (FK verso le
altre + attributi propri, NON tabella separata) — esattamente come per le binarie 1:N. Il
motore lo fa già da solo in base alle cardinalità che scrivi nello spec: mettile giuste.

### 6. Esercizi 4-6 (algebra/calcolo/documenti)
**OBBLIGO, non discrezionale** (errore reale già commesso: albero fatto per UN esercizio e
formule piatte per gli altri 3 — GAPS.md punto 6): **OGNI esercizio di algebra relazionale,
senza eccezioni, passa da `checker/algebra_tree.py`** (albero π/σ/⋈/ρ/∪/∩/−), mai formule
LaTeX piatte scritte a mano:
```python
import sys; sys.path.insert(0, "checker")
import algebra_tree as at
tree = {"op":"pi","attrs":["Nome"],"child":{"op":"sigma","cond":"X>0","child":{"op":"table","name":"TAB"}}}
frammento = at.render(tree, caption="Descrizione query")
open("out/_algebra.tex","w",encoding="utf-8").write(frammento)
```
Controllo minimo automatico disponibile: `at.check_uses_only_schema(tree, known_tables)`
verifica che le tabelle citate esistano davvero nello schema tradotto (non la correttezza
della query, solo la coerenza dei nomi).

**Schema documenti (ER etichettato → collezioni JSON): usa `checker/doc_schema.py`**, MAI
a mano (errore reale: scritto a mano = "completamente sbagliato", GAPS.md punto 8):
```python
import sys; sys.path.insert(0, "checker")
import doc_schema as ds
docs = ds.build(spec, roots=["VISITA", "TURISTA"])   # roots = entita' marcate DOCxxx nel diagramma
open("out/_documenti.tex","w",encoding="utf-8").write(
    "\\begin{verbatim}\n" + ds.render_text(docs) + "\\end{verbatim}\n")
```
Regola implementata (verificata sul caso reale TURISTA/GRUPPO): entità con max=1 verso il
padre → annidata (lista se il padre ne ha molte); max=N o entità-radice → riferimento.

Scrivi le altre sezioni come frammenti LaTeX in `out/_calcolo.tex`, `out/_documenti.tex`,
`out/_es1.tex` (esercizio dato/reverse, PRIMA della progettazione): `render.py` li include
automaticamente nel PDF finale SE i file esistono, con numerazione dinamica — non serve
toccare il template.

### 6bis. Regole aggiuntive OBBLIGATORIE (da errori reali commessi)
- **Esercizio "traduci questo ER dato"**: chiama `er.py --all` (o `solve.py`), MAI solo
  `--rel` — la soluzione deve mostrare ANCHE il diagramma di partenza, non solo la
  traduzione (GAPS.md punto 7).
- **Teoria a punti**: se la domanda elenca sotto-punti espliciti (es. "sintassi, semantica,
  esempio d'uso"), struttura la risposta con un `\textbf{}` per ciascun punto, MAI un
  paragrafo unico.
- **Attributi multivalore** (es. "gli autori" di un libro): campo `"multi": ["autori"]`
  nell'entità dello spec — genera automaticamente la tabella `ENTITA_AUTORI(pk, autori)`.
  NON ometterli mai (errore reale: "autori" perso del tutto, GAPS.md punto 9).
- **Ruoli / stessa entità referenziata 2 volte** (capo/vice): due relazioni separate con
  campo `"colname"` diverso su ciascuna (es. `"colname": "cap"` e `"colname": "vice"`) —
  evita la collisione dei nomi colonna FK.
- **Cardinalità numeriche** (es. "almeno 2", "al massimo 2"): ammesse nello spec come
  interi (`[2,"N"]`, `[1,2]`). Ai fini della traduzione max>1 conta come "molti"; il
  vincolo numerico esatto va comunque scritto a parole nella soluzione.

### 7. Consegna
`out/soluzione.pdf`. Controlla con `checker/pdf_qa.py out/soluzione.pdf` prima di consegnare:
verifica font embedded (niente simboli mancanti □) e assenza di caratteri di replacement.

## Regola d'oro
Progettazione, traduzione, e reverse-engineering **passano SEMPRE dal codice deterministico**.
La parte AI legge le foto e modella lo spec; il codice garantisce cardinalità/identificatori/
sottolineature corrette e un diagramma leggibile — mai disegnare o scrivere schemi a mano.

## Se qualcosa non torna
- Diagramma affollato/incrocia troppo: è un limite noto del layout automatico su grafi molto
  densi (documentato in `DESIGN_NOTES.md`), non un bug da "aggiustare a mano" nel disegno —
  segnalalo com'è.
- Un caso di traduzione sembra sbagliato: prima controlla `TEORIA_CHECKLIST.md` e
  `GAPS.md` — probabilmente è già un limite noto e documentato (es. relazioni con RUOLI,
  stessa entità che partecipa 2 volte con nomi diversi tipo Capo/Vice, non ancora supportate).
- Non inventare regole: se il testo dell'esame è ambiguo su una cardinalità, applica
  `TRICKS.md`, e se resta ambiguo dillo esplicitamente nella soluzione invece di inventare.

## File della cartella
- `checker/er.py` — motore: check, traduzione, disegno TikZ
- `checker/reverse_er.py` — reverse engineering relazionale→concettuale
- `checker/algebra_tree.py` — alberi algebra relazionale
- `checker/render.py`, `solve.py` — orchestrazione spec→PDF
- `checker/pdf_qa.py` — controllo qualità PDF finale
- `checker/test_*.py`, `dataset/test_dataset.py` — suite test (girala se modifichi il motore:
  `python checker/test_er.py && python checker/test_algebra_tree.py && python checker/test_reverse_er.py && python dataset/test_dataset.py`)
- `TRICKS.md`, `TEORIA_CHECKLIST.md`, `GAPS.md`, `DESIGN_NOTES.md` — regole confermate, teoria,
  limiti noti, decisioni di design — leggili prima di "scoprire" un problema già noto

## PARTE 2 (III prova: Tecnologie + Lab) — motori disponibili
Struttura tipica III prova (fonte: 2024_06_23_III_prova_intermedia.pdf): teoria (transazioni/
hash/MongoDB) + 4 esercizi algoritmici. Motori deterministici:

- **Esecuzione concorrente (VSR/CSR/2PL)**: `checker/pt2_schedule.py` — VERIFICATO contro le
  4 soluzioni ufficiali (17_esR_VSR_CSR_soluzioni.pdf).
  `ps.classify("r1(x), w2(x), ...")` → "CSR"/"VSR"/"nonSR"; `ps.topological_orders(ops)` →
  seriali equivalenti; `ps.is_2pl(ops)`; `ps.reads_from/final_writes` per giustificare VSR.
  OBBLIGO: la risposta d'esame deve mostrare conflitti, grafo, e giustificazione — usa gli
  insiemi calcolati dal motore, non ricalcolarli a mano.
- **Ripresa a caldo**: `checker/pt2_ripresa.py` — VERIFICATO contro lesson_02_esercizio_
  ripresa_a_caldo_01.pdf. `pr.ripresa(log_string)` → 5 passi completi (CK, UNDO/REDO,
  azioni a ritroso e in avanti). Regola chiave: A(T) NON toglie T da UNDO. RICERCA
  ESAUSTIVA 2026-07-19: NESSUNA slide di teoria dedicata all'algoritmo di ripresa a caldo
  esiste nel corpus locale (controllati lesson_01_transazioni.pdf = overview ACID senza
  algoritmo, "2 - Esempio di transazione.pdf" = solo esempio SQL ben-formato, lesson_03.pdf
  = SQL lab, tutti irrilevanti). Il prof probabilmente la spiega solo a lezione. La
  verifica contro l'esercizio ufficiale (match esatto passo-passo) resta la miglior fonte
  disponibile — non e' un buco di ricerca, e' un limite reale del materiale scaricabile.
- **B+tree**: `checker/pt2_btree.py` — VERIFICATO contro 20_esR_b+tree.pdf (fan-out 5:
  costruzione, insert con split senza guardare fratelli, delete con merge/redistribuzione
  col fratello sinistro, propagazione fino a root) E contro Lezione_04_Strutture_Fisiche_
  BTree_Hash.pdf (teoria ufficiale, vincoli di riempimento). `bt.build(leaves, f)`,
  `bt.insert(t,k,f)`, `bt.delete(t,k,f)`, `bt.render_text(t)`. BUG REALE trovato e corretto
  2026-07-19: la formula min_keys = ceil(f/2)-1 era sbagliata per fan-out PARI (es. f=4: dava
  1 invece di 2 come da teoria ceil((f-1)/2)) — testato solo con fan-out dispari (5) dove le
  due formule coincidono per caso. Fix in `_mins()`, test aggiunto in test_pt2_btree.py.
- **Costo query (ottimizzazione)**: `checker/pt2_costo.py` — VERIFICATO contro la FONTE
  PRIMARIA (slide teoria "10 - Ottimizzazione di interrogazioni - Parte II.pdf", sezioni
  "Nested-Loop JOIN: costo" e "...con indice B+-tree: costo"), non solo esercizi isolati:
  costo_join = NP(R)+NR(R)*NP(S) [senza indice], NP(R)+NR(R)*(d+NR(S)/VAL(join,S)) [con
  indice]. Riscontro aggiuntivo esatto su lesson_12_03_esercitazione_ottimizzazione_
  soluzioni.pdf Ottimizzazione 2 (475*(3+20)=10925). `pc.solve(np_outer, nr_outer,
  val_sel_outer, np_inner, pagine_sel_inner, nr_sel_inner, val_join_inner, prof_indice=d,
  interna_selezionata=True)`. Il flag `interna_selezionata=False` è per quando la tabella
  interna NON ha filtro WHERE (nessuna selezione da scrivere, si usa NP(interna) pieno
  direttamente nel join — bug reale trovato e corretto il 2026-07-19 sull'esame 21/04/2022,
  gonfiava il costo di 4200 accessi fittizi). ATTENZIONE: Ottimizzazione 1 punto (2) nel
  PDF ufficiale ha refusi aritmetici nel numero finale — fidati della formula, non di quel
  numero.
- **2PL**: `is_2pl()` in `pt2_schedule.py` verificato anche contro un controesempio non
  banale della slide teoria "8 - Esecuzione concorrente Parte III.pdf" pag.14 (CSR ma NON
  2PL: `r1(x),w1(x),r2(x),w2(x),r3(y),w1(y)` — T1 rilascia lock su x per far passare T2 poi
  riacquisisce lock su y, violando le due fasi). Conflitti/CSR/2PL predetti dal motore
  coincidono esattamente con quelli del prof — vedi `test_pt2_schedule.py`.
- Test: `python checker/test_pt2_schedule.py && python checker/test_pt2_ripresa.py && python checker/test_pt2_btree.py && python checker/test_pt2_costo.py && python checker/test_pt2_audit_slide.py`
- `checker/test_pt2_audit_slide.py` — audit regola-per-regola: verifica che il codice segua
  le SLIDE di teoria (vincoli riempimento B+tree per f=3..7, split/merge come da slide,
  definizione conflitto, teorema 2PL⊂CSR col controesempio ufficiale, caso VSR-non-CSR,
  formule NLJ). Confronto VISIVO col disegno ufficiale del prof: `dataset_pt2/
  confronto_20esR_ufficiale.spec.json` genera lo stesso esercizio delle slide 20_esR —
  output verificato identico passo-passo (build/insert H/delete Z) al disegno del prof.

### Pipeline generica (spec JSON → PDF), come parte 1
- `checker/pt2_render.py` — funzioni render_ripresa/render_schedule/render_costo/render_btree:
  prendono un dict esercizio dello spec e producono LaTeX (con TikZ per grafo conflitti e
  albero B+, formula sempre PRIMA dei numeri, una nota di spiegazione per passo — rivisto dopo
  bocciatura UX di un agente agy sulla prima versione "output grezzo di terminale").
- `checker/solve_pt2.py spec.json out_dir` — genera soluzione.tex (+pdf se pdflatex nel PATH
  della shell corrente — subprocess NON eredita sempre il PATH di MiKTeX, in quel caso lancia
  pdflatex a mano nella out_dir).
- Formato spec: `dataset_pt2/*.spec.json` (esempi con tutti e 4 i tipi tipo/ripresa/schedule/
  costo/btree). Quinto tipo `"teoria"`: domanda discorsiva + campo `"risposta"` (lista di
  paragrafi; prefisso "- " = voce di elenco puntato). Le risposte NON vengono da un motore:
  vanno SCRITTE basandosi sulle slide (es. proprietà transazioni+moduli da
  lesson_01_transazioni.pdf pag.23). Esempio completo con teoria a/b/c + esercizi d/e/f/g:
  `dataset_pt2/2025_06_12_terza_prova.spec.json` (esame INTERO, 4 pagine). GOTCHA: niente
  caratteri unicode matematici (≤, ⁺, →) nelle risposte — spariscono in cmr; scriverli a
  parole o in `$...$`. GOTCHA CONFERMATO: `\bowtie` fuori da `$...$` fa scattare il recovery
  "Missing $ inserted" di LaTeX che passa in math-mode e MANGIA TUTTI GLI SPAZI della frase
  fino al prossimo comando — sempre `$\bowtie$`, mai `\bowtie` nudo in una descrizione. Altro
  gotcha: caratteri unicode tipo `⁺` (superscript plus) spariscono silenziosamente in cmr —
  usare sempre `$^+$`.
- Dataset test set (2 esami interi, PDF letti direttamente in visione, NON fidarsi di agy per
  i numeri esatti quando servono da ground truth):
  - `dataset_pt2/2025_06_12_terza_prova.spec.json` — esame reale 12/06/2025, tutti e 4 gli
    esercizi (d,e,f,g), stessa struttura del 23/06/2025.
  - `dataset_pt2/2022_04_21_intermedia_A.spec.json` — esame reale 21/04/2022, schedule+costo+
    btree (niente ripresa, quell'esame ha invece un esercizio XML/XSD fuori scope motori).
    ATTENZIONE: contiene un'assunzione NON verificata (nessuna soluzione ufficiale reperita
    per questo esame) — il testo non filtra la tabella interna (VISITA) con un WHERE, quindi
    il motore la tratta come "gia' selezionata per intero"; il modello del prof potrebbe
    differire su questo punto specifico. Segnalato esplicitamente nel PDF generato.
  Nessuno dei due esami ha soluzione ufficiale con numeri pubblicati per un confronto diretto:
  la fiducia nei risultati viene dal fatto che i 4 motori sono verificati singolarmente contro
  fogli-soluzione ufficiali separati (vedi sopra), non da un test end-to-end su questi 2 esami.
- Esempio PDF generato da questi motori: `out_pt2/gen_soluzione.py` (versione originale,
  esame 23/06/2025) oppure via pipeline generica `dataset_pt2/2025_06_23_recupero.spec.json`.
