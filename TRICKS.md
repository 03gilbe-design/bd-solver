# Trick di progettazione ER — confermati dagli appunti (foto 06-30-07 / 06-30-10)

Regole che Claude DEVE applicare nella fase "testo → schema ER". Confermate dagli appunti manoscritti.

## Identificazione esterna (entità debole)
- Se un'entità **non riesce a identificarsi da sola** (non ha un attributo chiave proprio), prende
  parte della chiave da un'entità collegata → **identificatore esterno**.
- La relazione identificante, **sul lato dell'entità debole, è SEMPRE (1,1)**.
- Cardinalità ammesse per la relazione identificante (lato debole → owner):
  - `(1,1)` ✅ sempre
  - `(1,N)` ❌ da sola non identifica
- Nel relazionale: la PK dell'entità debole = (chiave locale + chiave importata dall'owner).

## Cardinalità minima (regola testata avversarialmente, da chat precedente)
- **min=1 su un ramo SOLO se il testo garantisce esplicitamente che OGNI istanza esistente
  partecipa già alla relazione in questo momento** — vale anche senza parole tipo "ogni"/"sempre",
  va dedotto dal significato. Es. "non è possibile registrare X senza Y" = garanzia → min=1.
- **Se una nuova istanza può esistere prima che la relazione esista → min=0.** Caso tipico:
  un'entità che si registra "subito" ma la relazione (es. check-in, assegnazione) avviene dopo.

## Cardinalità di default (quando il testo TACE)
- Partecipazione non obbligatoria → **(0,N)** o **(0,1)**.
- "È obbligatorio avere la relazione?" → se NO: minimo 0.
- Regola prof: se il testo non dice nulla, assumere **(0,N)** sul lato molti e **(1,1)** / **(0,1)** sull'altro.

## Attributo statico vs evento ricorrente
- **"Si memorizza / si indica"** → attributo statico dell'entità.
- **"Ogni anno il sistema fa / per ogni X si stabiliscono i Y"** → evento/relazione ricorrente:
  valutare se serve una **relazione** (spesso con dimensione temporale) e se si creano **duplicati**.

## Livello di dettaglio → arietà della relazione
- "Per ogni X **e** per ogni Y ... si stabilisce Z" → relazione **binaria** X–Y.
- "Per ogni X **per ogni** Y **per ogni** Z" → relazione **ternaria** (reificazione con entità in mezzo,
  archi (1,1) verso le entità partecipanti). Es. PRODOTTO —(1,1)— [R] —(1,1)— REPARTO con ANNO.
- Contro-esempio segnato ❌: PUNTO_VENDITA—ANNO con istanze (2025,10,1)(2025,10,2) = grana sbagliata.
- **Guarda il dettaglio più piccolo**: "ogni quanto voglio mettere un dato?" decide dove sta l'attributo.

## Chiavi primarie = conta le entità
- Ogni chiave primaria **contraddistingue un'istanza** di entità.
- Il **numero di chiavi primarie distinte** in una riga di dataset **indica il numero di entità** coinvolte
  (utile per riconoscere le relazioni n-arie: 3 chiavi in una riga → ternaria).

## Uso nel sistema
Queste regole vivono nel prompt della fase design (`AGENTS.md`). La **traduzione** ER→relazionale
resta deterministica in `er.py` (che valida: ogni entità un identificatore, id esterno con lato (1,1)).
