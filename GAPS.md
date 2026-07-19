# Casi NON coperti dal motore — scoperti testando l'esame reale 1-17_A (aeroporto)

Trovati modellando l'esame aeroporto **per intero** (9/11 entità coperte) e confrontando con la
soluzione ufficiale del prof. Onestà prima di tutto: questi sono buchi reali, non ipotetici.

## 1. Relazioni con RUOLI (stesso target entità più volte) — NON supportato
Esempio reale (1-17_A): `EQUIPAGGIO(Aeromobile, Data, Cap, Vice)` — sia `Cap` che `Vice` sono
**matricole di PILOTA**, cioè la stessa entità PILOTA partecipa **due volte** alla stessa relazione
con ruoli diversi (capitano / vice).

**Perché rompe `er.py`**: `_add_fk()` nomina le colonne FK come `{target.lower()}_{pk}` — se
la stessa entità target compare due volte (via due relazioni distinte CAP e VICE, o via due
partecipazioni nella stessa relazione), il nome colonna **collide** (`pilota_matricola` due volte).

**Fix necessario**: aggiungere un campo opzionale `"ruolo"` alla relazione nello spec, usato come
prefisso della colonna FK invece del nome-entità target. Non ancora implementato — priorità alta,
è un pattern comune negli esami (capo/vice, mittente/destinatario, genitore/figlio nella stessa entità).

## 2. Entità debole con identificazione via DUE relazioni (id composto multi-esterno)
`EQUIPAGGIO` è identificato da `(Aeromobile, Data)` dove Aeromobile è l'id esterno via la
relazione con AEROMOBILE. Il motore supporta un id esterno per entità (`_pk_attrs` prende
`ids[0]` e risolve le parti), quindi **questo caso specifico funzionerebbe** — non è il problema;
il problema è il punto 1 (i ruoli CAP/VICE), non l'identificazione.

## Impatto sulla copertura
Esame aeroporto: 11 tabelle nella soluzione prof, **9 modellate e verificate identiche** in
struttura (chiavi, nullable, FK). Le 2 mancanti (EQUIPAGGIO, ASSISTENZA) richiedono il fix del
punto 1. `ASSISTENZA` in realtà non ha il problema ruoli (è N:N semplice con ASSISTENTE_VOLO),
il vero blocco è EQUIPAGGIO che referenzia PILOTA due volte con ruolo.

## 3. Soluzioni ER come immagine/scansione, non testo
Esami 2025 (`BD_IProvaIntermediaC/D-12dicembre2025-conSolER.pdf`) hanno pagine con lo schema
ER ufficiale **disegnato/scansionato**, non testo estraibile in modo affidabile con `pdftotext`.
`scan_corpus.py` (confronto automatico) non può verificarli allo stesso modo di 1-17_A (dove la
soluzione è testo). Per questi serve lettura visiva (screenshot pagina + confronto a occhio),
non lo scan automatico.

## 4. Nome colonna FK impreciso verso entità ISA con strategia 'accorpa_nei_figli'
Quando un'entità identifica esternamente un'entità che è figlia ISA fusa col padre (nuova
strategia `accorpa_nei_figli`, vedi sotto), il nome colonna generato usa il vecchio schema
`entita_dipendente_matricola` invece di `entita_matricola` (il nome reale dopo la fusione).
Causa: `_pk_attrs` è risolto PRIMA che la traduzione ISA fonda le tabelle. Strutturalmente
corretto (stessa entità target, stessa colonna concettuale), solo il nome è sporco. Non
bloccante per i test strutturali (confrontano per nome entità, non nome colonna esatto), ma
andrebbe pulito se si genera DDL SQL vero.

## 5. Layout: spirale allontana entità collegate su grafi densi
`_adjacency_layout` (checker/er.py riga ~458): quando le 4 celle di griglia adiacenti a
un'entità sono già occupate, il codice cerca spazio libero in **spirale verso l'esterno**
(raggio crescente). Su un grafo denso (visto su `biblioteche_16lug.spec.json`, 11 entità +
gerarchia ISA) questo può piazzare un'entità **lontana** dalla sua vicina "naturale" solo
perché quella cella era già occupata da un'altra entità non collegata — bug reale, non solo
estetico: rompe la leggibilità del diagramma su esami con molte entità.
**Fix necessario**: preferire celle vicine al centroide di TUTTI i vicini già piazzati
(non solo le 4 adiacenti dirette), o aumentare il raggio di ricerca gradualmente E verificare
la vicinanza media prima di accettare, invece di prendere la prima cella libera trovata.

## 6. algebra_tree.py usato in modo incoerente (non un bug — abitudine da correggere)
Verificato su un esame reale (biblioteche_16lug): ho chiamato `algebra_tree.py` per generare
l'albero di UN solo sotto-esercizio (c.1) tramite `python -c "..."` al volo, poi per gli altri
3 (c.2, 3.a, 3.b) sono tornato a scrivere formule LaTeX piatte a mano. **Non è un limite del
tool** — supporta tutto il necessario (join condizionali, selezione, tabelle). La causa vera:
non ho mai salvato uno script riutilizzabile, ogni chiamata era one-off e "facile da saltare"
per il successivo esercizio. **Fix**: AGENTS.md dovrebbe dire esplicitamente "ogni esercizio di
algebra relazionale, senza eccezioni, passa da algebra_tree.py" — non lasciarlo a discrezione.

## 7. Esercizio "traduzione ER dato → relazionale": manca il diagramma del punto di partenza
Quando l'esame fornisce già uno schema ER (non chiede di progettarlo, solo di tradurlo), ho
generato SOLO lo schema relazionale (`er.py --rel`) saltando il disegno dello schema ER dato
(`er.py --tikz`). Risultato: la soluzione mostra la traduzione ma non lo schema di partenza,
incompleta per un correttore che deve verificare che la lettura dello schema fosse corretta.
**Fix**: per questo tipo di esercizio, chiamare sempre `--all` (check+tikz+rel), non solo `--rel`.

## 8. Schema documenti (JSON da ER etichettato): nessun motore, mai avuto uno
Esercizio "genera lo schema delle collezioni di documenti da uno schema ER etichettato" (tipo
TURISTA/GRUPPO, esami dal 2025) non ha MAI avuto un tool dedicato nel progetto — sempre scritto
a mano da zero ogni volta, senza nessuna verifica automatica. Su biblioteche_16lug è risultato
"completamente sbagliato" (segnalazione utente) sia lo schema che le etichette (a). Gap di
progetto, non solo di quella sessione — manca dal giorno 1 (mai in TODO esplicito prima d'ora).
**Fix necessario**: costruire un motore minimo che, dato uno spec ER con marcatore "radice
documento" su alcune entità, generi automaticamente la struttura annidata/riferimento in base
alle cardinalità (regola: verso il padre max=1 → annidabile, altrimenti → riferimento) — la
stessa euristica usata "a mano" stavolta, ma resa deterministica e testabile.

## 9. Confronto con sessione parallela Termux sullo stesso esame (16 luglio) — divergenze reali
Un'altra sessione Claude Code (su Termux, stesso pomeriggio, salvata in
`termux_session_16lug/`) ha risolto lo STESSO esame in modo indipendente, con approccio
diverso (Graphviz `.dot`+PNG invece di TikZ). Confronto:

**Bug mio confermato**: ho **omesso completamente l'attributo "autori"** di LIBRO dal mio
spec (multivalore, il motore non lo supporta nativamente) — la sessione Termux l'ha gestito
correttamente con tabella dedicata `AUTORE_LIBRO(ISBN, Autore)`. **Fix necessario**: il
motore deve supportare attributi multivalore (genera tabella `ENTITA_ATTR(pk_entita, valore)`
automaticamente), invece di lasciare che vengano dimenticati in spec scritti a mano.

**Divergenze di lettura foto (non chiaro chi ha ragione, serve foto migliore)**:
- Relazione BIBLIOTECA_SPECIALISTICA↔DIPARTIMENTO: io 1:N diretta (1 dipartimento per
  biblioteca), Termux N:N con tabella GESTIONE (più dipartimenti per biblioteca) — il testo
  fotografato non specifica la cardinalità lato dipartimento con chiarezza sufficiente.
- Schema ER preliminare (b): chiave di A e topologia della relazione Q lette in modo
  strutturalmente diverso dalle due sessioni — conferma indipendente che quella foto
  specifica era ambigua (non solo mio errore di lettura).
- Sessione Termux ha (probabile errore loro): "ResponsabileAteneo" duplicato sia su
  BIBLIOTECA_CENTRALE che su DIPARTIMENTO — il testo lo assegna solo alla gestione centrale.

**File salvati per riferimento**: `termux_session_16lug/bd_soluzioni.md` (soluzioni testuali),
`*.dot`/`*.png` (diagrammi Graphviz), `genera_pdf.py`/`RICOSTRUISCI.sh` (script usati) — utile
per capire un secondo approccio di generazione diagrammi (Graphviz diretto, non TikZ) da
valutare se più robusto del mio su layout complessi.

## 10. Sessione Termux: il kit NON è stato usato affatto
Analisi di `termux_session_16lug/RICOSTRUISCI.sh` e `genera_pdf.py`: la sessione Claude Code
su Termux ha risolto l'esame **reinventando tutto da zero** — diagrammi Graphviz `.dot`
scritti a mano, PDF con fpdf2, ZERO uso di `er.py`/`solve.py`/`doc_schema.py`/AGENTS.md.
Risultato comunque decente (font ok al pdf_qa, alberi algebra presenti), ma: nessuna
validazione dello spec, nessun test, cardinalità non verificate, e il lavoro del kit
duplicato male. Causa probabile: lo zip non era scompattato nella cartella di lavoro o
Claude non è stato istruito a partire da AGENTS.md.
**Fix operativo (per l'utente, non codice)**: su Termux, PRIMA di dare le foto, dire
esplicitamente: "unzippa BD_Parte1_Solver.zip, leggi AGENTS.md e segui SOLO quella
procedura". Senza istruzione esplicita, Claude a freddo reinventa.

## TODO (aggiornato dopo il giro di fix)
- [x] `"colname"` opzionale in `_add_fk` per prefissare le colonne FK (ruoli capo/vice)
- [ ] Ri-testare EQUIPAGGIO/ASSISTENZA con colname → target 11/11 sull'esame aeroporto
- [x] Fix layout spirale (punto 5): ora sceglie la cella libera più vicina al CENTROIDE dei vicini già piazzati
- [x] AGENTS.md: algebra_tree.py OBBLIGATORIO per ogni esercizio di algebra (sez. 6)
- [x] AGENTS.md: "traduci ER dato" → sempre `--all`/solve.py, mai solo `--rel` (sez. 6bis)
- [x] Motore schema documenti: `checker/doc_schema.py` + test su caso reale TURISTA/GRUPPO — annidamento/riferimento deterministico
- [x] Attributi multivalore: campo `"multi"` → tabella `ENTITA_ATTR` automatica (verificato: LIBRO_AUTORI ora generato)
- [x] Cardinalità numeriche (2,N)/(1,2) ammesse nello spec; max>1 = "molti" in traduzione
- [ ] Punto 4 (nome colonna FK sporco con accorpa_nei_figli) — non ancora fixato
- [ ] Verificare divergenze di lettura foto (punto 9) con foto migliori delle 2 pagine ambigue
