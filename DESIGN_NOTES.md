# Perché un generatore custom e non un tool GitHub esistente

Domanda giusta: esistono tool per disegnare ER. Ecco il panorama e la scelta.

## Tool esistenti
| Tool | Cosa fa | Adatto? |
|---|---|---|
| **tikz-er2**, **latex-erd** (NatoliChris), **tex-er-diagram** (bryanmylee) | Macro LaTeX per disegnare ER in **notazione Chen con (min,max)** — *stessa notazione del prof Belussi* | Notazione ✅ ma richiedono di **piazzare i nodi a mano**; nessun auto-layout, nessuna traduzione al relazionale |
| **Mermaid** `erDiagram`, **PlantUML** | ER in markdown, render su GitHub | ❌ usano **crow's-foot**, non (min,max) → NON è lo stile d'esame |
| **eralchemy / erdantic** | ER da modelli/DB → Graphviz | ❌ partono da schema DB, non da testo; notazione non-Chen |
| **Graphviz** (dot/neato) | **Auto-layout** di grafi senza sovrapposizioni | ✅ per il *layout*, ma è la sola parte layout, non la notazione |

## Cosa manca a tutti
Nessuno fa la catena richiesta: **testo esame → spec → (validazione cardinalità/id) → traduzione relazionale + diagramma**. I tool LaTeX disegnano soltanto; Graphviz posiziona soltanto.

## Scelta attuale
`er.py` fa lo strato mancante (spec + check + traduzione + layout stdlib) ed emette TikZ Chen.
Motivi: (1) gira su **Termux con solo stdlib**, (2) include la **traduzione** che è metà dell'esercizio,
(3) il layout anti-collisione basta per diagrammi d'esame (≤ ~10 entità).

## Aggiornamento 2: passato a networkx (Kamada-Kawai) + repulsione, layout BFS abbandonato
Il BFS-grid (aggiornamento 1 sotto) non bastava: troppi incroci su grafi con >6 entità,
segnalato a ragione come "fa cagare". `networkx` risultava già installato (`pip show`), quindi
sostituito con un layout vero: `kamada_kawai_layout` (deterministico, minimizza la distanza
grafo↔euclidea → molti meno incroci a lunga distanza) su un grafo che include entità E rombi
relazione come nodi dello stesso grafo. Kamada-Kawai da solo trattava i nodi come punti e li
ammassava (peggio del grid su cluster densi): aggiunta `_relax()`, una repulsione iterativa
deterministica (no random, ordine fisso) che allontana coppie di nodi più vicine della somma
dei loro raggi (box + ventaglio attributi + lunghezza nome, quest'ultima dimenticata alla prima
versione → rombi con nomi lunghi tipo `PRENOTA_AULA_CORSO_EDIZ` si sovrapponevano ai vicini).
Fallback su BFS-grid se `networkx` non è installato (Termux senza pip). Risultato: niente più
box/etichette impilati; restano alcuni incroci di linee su grafi molto densi (limite noto,
minimizzare incroci a zero è NP-hard in generale).

## Aggiornamento 1: Graphviz non installato, primo fix (superato) senza dipendenze esterne
Verificato: **niente Graphviz su questa macchina** (`dot`/`neato` assenti, nessun pacchetto
Windows a disposizione senza installazione). Nel frattempo migliorato il layout esistente:
`_bfs_order()` in `er.py` ordina le entità per **adiacenza** (BFS sul grafo delle relazioni)
invece che per ordine di inserimento nello spec → entità collegate finiscono vicine nella
griglia, molte meno linee lunghe che attraversano righe intere e si incrociano. Non risolve
tutto (grafi molto densi restano affollati, vedi `catalogo_casi` con 8 entità/6 relazioni
deliberatamente denso), ma su un esame normale (5-9 entità) il miglioramento è visibile.
Se serve di più: installare Graphviz (`winget install Graphviz`) e usare `neato -Tplain`
come backend opzionale, con fallback al BFS-nudge attuale se assente (Termux-safe).

## Aggiornamento 3: confronto visivo con 3 esempi REALI del prof + valutazione tex-er-diagram
Guardati (immagini, non solo testo) i diagrammi ufficiali di aeroporto, catena_alberghi,
scuola_sci. Pattern costante e diverso dal mio:
1. **ISA come spina unica** con diramazioni a T verso i sottotipi (etichetta `(t,e)`
   totale/esclusiva) — io disegno una freccia separata per figlio, sbagliato.
2. **Rombo INLINE tra le due entità** che collega (stesso asse), non isolato in una riga
   propria — il mio grafo Graphviz diretto (`relazione -> entità`) forza 2 righe separate.
3. **Attributi su qualunque lato libero** (sopra/sotto/di lato), non fisso.
Nessuna di queste tre e' stata implementata (solo diagnosticata) - richiedono cambi
strutturali a `_graphviz_layout`/`tikz()` non tentati per rischio di regressione a fine sessione.

Valutato `tex-er-diagram` (bryanmylee) come alternativa: supporta posizionamento esplicito
(compatibile con coordinate Graphviz), MA **nessun supporto ISA/generalizzazione** nella doc
pubblica (blocco duro, serve per le gerarchie multi-sottotipo di questi esami) e sintassi
cardinalità non documentata chiaramente. Non adottato: richiederebbe leggere `er-diagram.sty`
sorgente per verificare prima di impegnarsi, rimandato.

## Aggiornamento 4: ISA come nodo-spina (ispirato da tikz-er2, non vendorizzato)
Implementato il pattern #1 di Aggiornamento 3: un solo nodo triangolare "isa" (stile preso da
`tikz-er2`, reimplementato inline in ~4 righe di tikzstyle — non serve importare il pacchetto,
`isa/.style={isosceles triangle,...}` è tutto ciò che serve) tra padre e figli, posizionato al
punto medio fra il padre e il centroide dei figli. Sostituisce le N frecce separate che
convergevano caoticamente sul padre. Verificato visivamente su aeroporto (2 figli) e
catena_alberghi (6 figli): pulito in entrambi, corrisponde allo stile reale del prof (visto in
3 diagrammi ufficiali: aeroporto, catena_alberghi, scuola_sci — tutti usano la spina, mai
frecce multiple). `tex-er-diagram` scartato (niente ISA); `tikz-er2` non vendorizzato per
intero (bastava lo stile isa, non serve la dipendenza) dopo aver letto il sorgente (~67 righe,
solo tikzstyle, nessuna macro proprietaria).
Ancora aperti (Aggiornamento 3, punti 2-3): rombo inline tra le entità (richiede grafo non
diretto invece di `relazione -> entità`), attributi multi-lato.

## Aggiornamento 10: layout ad adiacenza (idea utente) — buono su catene, peggio su hub densi
Proposta utente: entità con relazione = celle di griglia ADIACENTI (stessa riga/colonna),
non sparse da un algoritmo fisico; ternarie a T. Implementato `_adjacency_layout()`: BFS su
griglia intera, ogni vicino nuovo prova le 4 direzioni (E/S/O/N) poi spirale se tutte
occupate. Stile Chen invariato. Risultato onesto (confrontato visivamente):
- **Meglio** su strutture a catena (aeroporto, catalogo_casi): entità collegate vicine,
  poche linee lunghe, pulito.
- **Peggio** su hub densi (catena_alberghi: DIPENDENTE con 6 figli ISA + più relazioni):
  troppi vicini per un hub, la spirale li sparge lontano, più incroci di kamada_kawai.
Default ora `_adjacency_layout`. Kamada_kawai resta disponibile (`ER_LAYOUT=kamada`) per
i casi hub-densi dove va meglio. Tutte e 3 le varianti (ADIACENZA/DIAGONALE/ORTOGONALE)
salvate in Downloads per confronto diretto - nessuna è oggettivamente migliore su tutti i casi.

## Aggiornamento 9: attributi distribuiti su piu' lati (N/S/E/W)
Segnalato piu' volte: entita' con molti attributi (PASSEGGERO, 9) li ammassava tutti in
un'unica fila sopra il box, illeggibili. `draw_attrs()` ora distribuisce: ≤4 attributi un
solo lato (comportamento originale), 5-8 meta' sopra meta' sotto, >8 anche a est/ovest.
Verificato su PASSEGGERO: 4 sopra + 5 sotto, non piu' una fila sola. Resta una piccola
sovrapposizione locale fra un'etichetta e una cardinalita' vicina - non perfetto, ma
misurabilmente meglio (prima: 9 in fila, illeggibile; ora: 2 righe da 4-5).

## Aggiornamento 8: torna a kamada_kawai (diagonale) come default, ortho tenuto come opzione
L'utente ha visto entrambe le versioni (diagonale-kamada_kawai vs ortogonale-neato) via PDF
affiancati in Downloads e ha giudicato l'ortogonale "fa schifo" (angoli retti caotici) contro
il diagonale "sensato" nonostante le linee oblique. Default riportato a kamada_kawai+relax.
L'ortogonale non è cancellato: `ER_LAYOUT=ortho python solve.py ...` lo riattiva (utile se in
futuro si migliora l'euristica di piegamento). Entrambe le versioni di ogni esame salvate in
Downloads con suffisso `_DIAGONALE`/`_ORTOGONALE` per confronto diretto.

## Aggiornamento 7: testo minuscolo risolto — classe 'standalone' + includepdf
Con diagrammi grandi (catene lunghe da neato) il testo diventava minuscolo: adjustbox
scala SEMPRE per stare in A4, qualunque sia la dimensione naturale del diagramma. Cercato
online la soluzione standard: la classe LaTeX `standalone` dimensiona la pagina ESATTAMENTE
sul contenuto (zero shrink). Primo tentativo (`\pdfpagewidth`/`\pdfpageheight` a mano +
aggiornamento manuale di `\textwidth`/`\textheight` a meta' documento) ha prodotto
regressioni peggiori (pagine bianche, contenuto perso) - abbandonato, codice lasciato
commentato come riferimento. Soluzione che funziona: **compilare il diagramma come
documento standalone A SE'** (`checker/render.py:compile_er_standalone`), poi includerlo
nel documento principale con `\includepdf[pages=-,fitpaper=true]{_er_standalone.pdf}`
(pacchetto `pdfpages`) — pdfpages gestisce nativamente pagine di dimensione diversa dal
resto del documento, senza toccare `\textwidth`/`\textheight` a mano. Verificato: 3 pagine
pulite (titolo A4, diagramma su pagina custom a grandezza naturale, schema relazionale A4),
nessuna pagina orfana/bianca, testo leggibile senza zoom. Fallback: se pdflatex non
compila lo standalone (raro), torna al vecchio adjustbox-shrink (funzionante, solo più
piccolo). Richiede `pdflatex` disponibile due volte nel flusso (standalone + documento
principale) — accettabile, il primo compile è piccolo e veloce.

## Aggiornamento 5: rombo inline (risolto) — neato al posto di dot
Diagnosticato perché "tutto in una riga": `dot` è un layout **a livelli rigidi**, e il mio
grafo è bipartito (rombi collegano solo entità, mai altri rombi) → `dot` separa SEMPRE in
esattamente 2 righe, qualunque sia la direzione delle frecce (provato `digraph`→`graph`
non diretto: nessun cambiamento, il problema non era la direzione ma l'algoritmo a livelli
stesso). Passato a **neato** (force-directed, non a livelli): ora i rombi finiscono
naturalmente **inline tra le due entità che collegano**, come nei diagrammi reali del prof
(verificato: aeroporto e catena_alberghi ora mostrano catene entità-rombo-entità invece di
2 righe). Tolto anche il landscape forzato (sbagliato per l'aspect ratio più verticale di
neato). Bug trovato e fixato nello stesso giro: il nodo-spina ISA (Aggiornamento 4) usava il
punto medio padre/figli per la posizione, che con neato (nodi connessi più vicini) finiva
spesso DENTRO il box del padre, sovrapponendo il triangolo al testo (letteralmente
"DIPEN▽TE"). Fix: distanza fissa dal padre lungo la direzione verso i figli, non punto medio.
Verificato via crop ad alta risoluzione prima e dopo il fix.

## Upgrade path (se serve fedeltà pixel al prof o diagrammi grandi)
1. **Notazione**: far emettere a `er.py` macro **`tikz-er2`** invece di rettangoli/rombi grezzi
   → attributi come ●/○, doppie linee per partecipazione totale, identico al prof.
   Costo: dipendenza dal pacchetto `tikz-er2.sty` (MiKTeX lo auto-installa; texlive Termux ce l'ha).
2. **Layout**: backend opzionale **Graphviz `neato -Tplain`** per le posizioni, con fallback al
   nudge stdlib se `dot` non c'è → non rompe Termux.

Entrambi sono innesti localizzati (solo la funzione `tikz()`), non un rewrite.
