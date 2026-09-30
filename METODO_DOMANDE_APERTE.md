# Metodo per domande aperte (teoria, SQL, e pezzi mancanti)

Le domande a)/b) (teoria) e c)/d) (SQL) non hanno un motore deterministico:
qui sotto il metodo per come scriverle, non solo dove cercarle.

## 1. Non esiste un modulo automatico per le domande aperte, e non puo' esistere

I motori (`pt2_ripresa`, `pt2_schedule`, `pt2_costo`, `pt2_btree`) funzionano
perche' la domanda ha UN algoritmo fisso con UN risultato calcolabile. Una
domanda di teoria ("illustrare...") o una richiesta SQL in linguaggio naturale
non hanno questo: sono ragionamento, non calcolo. Per queste due categorie
l'unico aiuto possibile e' un **archivio di risposte gia' scritte e verificate**
(`riferimenti_teoria/`), non un motore che le genera da zero.

Prima di scrivere una risposta nuova: controlla se la domanda matcha qualcosa
in `riferimenti_teoria/Risposte_Teoria_ParteII.pdf`,
`riferimenti_teoria/DOMANDE_NEL_TEMPO.txt` o `riferimenti_teoria/BD_SCHEMI_ESAME.pdf`
(vedi RUNBOOK_TERMUX.md, Passo 0). Solo se non c'e' nulla, si scrive da zero
seguendo le regole sotto.

## 2. Come scrivere una risposta: coerente col prof, MAI copiata, piu' semplice

Obiettivo: stesso contenuto tecnico e stessa correttezza della fonte (slide o
soluzione del prof), ma con parole proprie e una forma piu' semplice - non un
riassunto piu' povero, una spiegazione piu' diretta.

**Regola pratica**: se una frase della fonte si puo' quasi ricopiare cambiando
2-3 parole, non va bene - vuol dire che non e' stata capita, solo riformulata
di superficie. Il test: chiudi la fonte e riscrivi il concetto sapendo SOLO
cosa fa, non come e' scritto li'.

Esempio di trasformazione (fonte -> risposta):

> Fonte (slide): "L'algoritmo di ripresa a caldo si articola in un'analisi del
> log a ritroso a partire dall'ultimo checkpoint per determinare l'insieme
> delle transazioni da annullare e da ripetere, seguita da una fase di undo
> e da una fase di redo."

> Risposta (stessa cosa, piu' semplice, non copiata): "Prima si legge il log
> all'indietro dal checkpoint per decidere chi va rifatto e chi disfatto (chi
> ha fatto commit va rifatto, chi no va disfatto). Poi si esegue: prima tutto
> l'UNDO (a ritroso), poi tutto il REDO (in avanti)."

Stesso contenuto tecnico esatto (analisi del log, checkpoint, chi rifare/disfare,
ordine undo poi redo), zero frasi copiate, piu' diretta.

**Non semplificare via un dettaglio tecnico vero** solo per accorciare (es. non
omettere "a ritroso" per l'UNDO - quello e' un dettaglio che nell'esame conta).
Semplice nella FORMA, completo nel CONTENUTO.

**Negli schemi: descrivere i sottocasi che non vengono in mente da soli.** Uno
schema visivo (B+-tree, ER, matrice VSR) mostra il caso disegnato, ma chi lo
legge deve anche sapere cosa fare nei casi limite che quello schema NON
mostra esplicitamente - es. "e se il nodo da cancellare e' la radice?", "e se
il fratello sinistro non esiste (sono il primo figlio)?". Un dubbio del
genere in sede d'esame, senza risposta pronta, costa piu' tempo che leggerlo
scritto in anticipo. Aggiungere una riga breve per il caso limite, non
disegnare uno schema apposta per ognuno.

**Rischio opposto da evitare: risposte o query troppo lunghe.** Una risposta
di teoria che elenca ogni dettaglio possibile diventa illeggibile in sede
d'esame (tempo limitato) - meglio corta e completa sui punti richiesti che
esaustiva su tutto lo scibile. Stessa cosa per le query SQL: una query che
funziona ma e' inutilmente contorta (troppe subquery annidate quando una
JOIN basterebbe, troppi CTE per un caso semplice) rischia piu' errori di
battitura e ci mette di piu' a scriverla a mano. Preferire sempre la
struttura piu' corta che resta corretta - non la piu' generale possibile.

## 3. Intuire i pezzi mancanti quando non c'e' altra foto

Una foto puo' essere tagliata, sfocata, o mancare una riga. Se non c'e' modo di
richiedere un'altra foto, il comportamento corretto NON e' fermarsi dicendo
"non leggibile" - e' ragionare dal contesto per completare, **dicendo chiaramente
che e' un'inferenza**, non un dato letto.

**Da dove si inferisce, in ordine di affidabilita':**
1. **Pattern strutturale dell'esercizio**: se il tipo di esercizio e' noto
   (ripresa, B+-tree, ottimizzazione...) la sua struttura e' fissa - un pezzo
   mancante spesso si deduce dal formato (es. se manca un valore VAL(...) ma
   il totale finale e' leggibile, si puo' risalire al valore mancante
   risolvendo l'equazione al contrario).
2. **Convenzioni gia' verificate** in `riferimenti_teoria/soluzioni_prof_originali/`
   - se manca una parola chiave del tipo "si usa merge diretto" o "profondita'
   indice = N", e il resto del contesto matcha un caso gia' visto, si puo'
   assumere la stessa convenzione (mai il contrario: mai inventare una
   convenzione nuova per comodita').
3. **Coerenza interna del resto della foto**: es. se in un log di ripresa la
   foglia finale ha 3 chiavi e il fan-out e' 5, la chiave mancante in mezzo si
   puo' dedurre dall'ordine (i B+-tree sono sempre ordinati).

**Come segnalarlo**: ogni pezzo dedotto (non letto direttamente) va marcato
esplicitamente, es. `[inferito dal pattern: valore probabile X, foto tagliata
qui]` - mai presentato come se fosse stato letto chiaro. Chi legge la risposta
deve poter distinguere cosa e' certo da cosa e' dedotto.

## Le due tecniche vere, leggere (stdlib, zero download)

Implementate e testate in `checker/pt2_fallback.py` (`python checker/pt2_fallback.py`
per l'autotest). Cercate online prima di scriverle: sono tecniche standard, non
inventate - **constraint propagation** (AI/CSP: dedurre un valore ignoto da un
vincolo noto, es. formula+totale) e **fuzzy matching / distanza di Levenshtein**
(correggere una parola sporca confrontandola col vocabolario gia' visto).

```
                    PEZZO ILLEGGIBILE NELLA FOTO
                              │
                 ┌────────────┴────────────┐
                 │                         │
            E' UN NUMERO               E' UNA PAROLA
         (dentro una formula)      (nome tabella, keyword...)
                 │                         │
                 ▼                         ▼
      CONSTRAINT PROPAGATION         FUZZY MATCHING
      conosci formula+totale?        confronta col vocabolario
      prova ogni valore plausibile   gia' visto nell'archivio
      del dominio, tieni solo chi    (riferimenti_teoria/,
      riproduce il totale            soluzioni_prof_originali/)
                 │                         │
        ┌────────┼────────┐        ┌───────┼───────┐
        ▼        ▼        ▼        ▼       ▼       ▼
    UN SOLO   PIU' DI  NESSUNO   SOPRA   SOTTO   NESSUNA
   candidato   UNO      torna    soglia  soglia  corrisp.
        │        │        │        │       │       │
        ▼        ▼        ▼        ▼       ▼       ▼
     DEDOTTO   dillo,   dillo,   usa la  dillo,  dillo,
     CON       elenca   non hai  migliore elenca  non
     CERTEZZA  i        soluzione (segna  le      forzare
     (segna    candidati          come    alter-  nulla
     come              inferito) native
     inferito)
```

**Regola in entrambi i casi**: se non c'e' UN solo esito chiaro, il codice lo
dice onestamente (`ambiguo`, `nessun_candidato_torna`, `nessuna_corrispondenza`)
- non sceglie a caso il primo candidato. Verificato nei test: i casi impossibili
e ambigui rispondono correttamente, non forzano una risposta falsa.

**Esempio reale gia' testato**: nell'esercizio Ottimizzazione di oggi, la
formula `NR_sel x (profondita + 20) = totale` con totale=14.375 e NR_sel=625
nota, dedotta profondita'=3 provando i valori 1-9 - un solo valore soddisfa
l'equazione, esattamente la profondita' vera dell'indice B+-tree di
quell'esercizio.

## Limite onesto: queste tecniche NON recuperano una foto completamente sfocata

Testato su un caso reale (2026-09-14, foto di un esame Parte 1): una foto con
forte sfocatura da movimento rende lo schema/testo di quella pagina
**illeggibile al 100%** - zero segnale nei pixel, non solo "poco chiaro".

Constraint propagation e fuzzy matching funzionano su **informazione
parziale** (una cifra sfocata dentro un numero per il resto leggibile, una
parola con 2-3 lettere sbagliate ma il resto giusto) - hanno bisogno di un
vincolo o di una somiglianza da cui partire. Su un blur totale non c'e' NIENTE
da cui partire: nessun algoritmo (nemmeno pesante) recupera testo che non e'
mai arrivato nel sensore della fotocamera.

**Comportamento corretto in questo caso**: dire chiaramente "pagina
illeggibile, serve un'altra foto" - MAI inventare nomi di entita'/attributi
plausibili per riempire il vuoto. Prima di arrendersi, un solo controllo ha
senso: se nel resto del set di foto c'e' un'altra immagine della STESSA
pagina (foto doppia, ripresa due volte), usare quella. Se non c'e' - fermarsi,
non indovinare.
