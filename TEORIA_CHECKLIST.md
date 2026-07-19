# Checklist teoria progettazione ER — estratta dalle soluzioni reali (non slide: non trovate nel download tree)

Nessuna slide-teoria dedicata alla progettazione ER è stata trovata in `BasiDati/01_Slide_Prof`
(solo esami e lab SQL/transazioni/strutture-accesso). La teoria di progettazione la ricavo quindi
dalle **soluzioni ufficiali** del prof, che la applicano esplicitamente. Fonte primaria: 1-17_A.

## Regole di cardinalità
- [x] min=0 → partecipazione opzionale, min=1 → obbligatoria (implementato: `card=(min,max)`, check valida min∈{0,1})
- [x] max=1 → "al più uno", max=N → "arbitrariamente molti" (check valida max∈{1,"N"})
- [ ] cardinalità di default quando il testo tace (TRICKS.md: euristica, non ancora automatizzata nel check)

## Identificazione
- [x] interna: uno o più attributi propri (`id: [[...]]`)
- [x] esterna: include la chiave di un'entità collegata via relazione **(1,1)** sul lato debole
      (implementato + validato: `check()` rifiuta id esterno con relazione non-(1,1))
- [ ] identificazione esterna **multipla** (entità che importa chiavi da 2+ relazioni diverse) — non testato

## Generalizzazioni (ISA) — 3 strategie osservate nelle soluzioni reali
- [x] **accorpamento nel padre**: attributi dei figli migrano nel padre (nullable) + discriminante
      `tipo` (implementato: `strategia="padre"`). Esempio prof: "generalizzazioni su VOLO e su
      PASSEGGERO accorpate nel padre" (voli con/senza scalo, passeggeri singoli/gruppo — non
      modellato nel dettaglio, ma la STRATEGIA di traduzione è la stessa).
- [x] **sostituita con relazioni** (= tabelle figlie separate con FK al padre, strategia "figli"
      nel mio spec). Esempio prof: "generalizzazione su dipendenti rimpiazzata con relazioni"
      → PILOTA(Matricola,...), ASSISTENTE_VOLO(Matricola,...) con FK verso DIPENDENTE. Verificato
      identico nel dataset test (aeroporto).
- [x] **accorpa_nei_figli**: il PADRE sparisce, ogni figlio assorbe i SUOI attributi (no FK).
      Esempio prof (1-18_A, scuola sci): "Accorpo la generalizzazione con radice in DIPENDENTE
      nelle entità figlie" → MAESTRO_SCI(Matricola,CodiceFis,Nome,Cognome,DataNas,DataTitolo),
      niente tabella DIPENDENTE. Verificato identico nel dataset (scuola_sci).
- [x] **partizione totale/parziale, esclusiva/sovrapposta**: CONFERMATO che sono 4 casi
      distinti reali (fonte: Downloads\Telegram Desktop\lezione.pdf, slide teoria vera del
      prof: "(totale,esclusiva) (parziale,esclusiva) (totale,sovrapposta) (parziale,sovrapposta)").
      Il motore (er.py) NON li distingue ancora (tratta tutte le ISA uguale) — gap reale
      confermato, non più solo sospettato. TODO: aggiungere questi 2 flag allo spec ISA.
- [x] **reverse engineering (relazionale→concettuale)**: pattern confermati dalla stessa fonte
      (lezione.pdf): FK fuori PK→1:N, N FK sulla PK→relazione N-aria, FK nullable in PK
      propria→1:1 opzionale. Implementato in `checker/reverse_er.py`, testato su questi
      pattern esatti + sul caso reale 2023 (R1-R4).

## Relazioni con RUOLI — gap noto (vedi GAPS.md)
- [ ] stessa entità partecipante 2+ volte alla stessa relazione (o a relazioni diverse) con ruoli
      diversi (es. CAP/VICE entrambi PILOTA in EQUIPAGGIO). **NON supportato**, collisione nomi FK.

## Relazioni n-arie
- [x] disegnate (rombo al centroide + arco per entità) e tradotte (tabella con PK = tutte le chiavi
      partecipanti + attributi propri). Verificato nel dataset (supermercato: PRODOTTO×PUNTO_VENDITA×ANNO).

## Attributi
- [x] opzionali → nullable (`opt: [...]`, disegnati con linea tratteggiata nel diagramma)
- [ ] attributi composti (es. "Indirizzo" = via+civico+città) — non supportati, si assume atomici
- [ ] attributi multivalore — non supportati

## Uso
Ogni riga NON spuntata è un caso da coprire prima di dichiarare il motore "affidabile su tutto".
Aggiornare spuntando quando si trova un esempio reale che lo conferma E il motore lo riproduce.
