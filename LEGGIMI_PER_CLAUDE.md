**PER L'ESAME: apri AGENTS.md, blocco 'INIZIA QUI' (5 passi, un comando: `python esame.py spec.json`).**

# Passaggio a Claude (chat) — Basi di Dati parte 2 (Tec+Lab, Migliorini) — stato 30/09/2026

Leggi prima `AGENTS.md` (sezioni PARTE 2, TEORIA, SQL, Stile PROF, Sfida al prof) e `STRUMENTI_GOTCHA.md`.

## Cosa fa
Foto esame -> tu scrivi lo spec JSON (`dataset_pt2/*.spec.json` come esempio) -> `python checker/solve_pt2.py spec.json out [opzioni]`.
Opzioni: `--minimal` (niente note, teoria da `risposta_minimal`), `--verticale` (colonna nera), `--colori`
(estratto colorato per verificarlo), `--quadretti` (A4 5 mm: domande stampate, soluzione "a mano" in
MAIUSCOLO, 1 carattere = 1 quadretto, I/punteggiatura/spazio = mezzo, riga vuota dopo ogni riga, accenti sopra).

## Controlli (tutti stdlib, girano su Termux)
- teoria: `checker/teoria.py "domanda" punti risposta.txt` (punti obbligatori, lunghezza, anti-copia)
- SQL: `checker/sql_check.py "T(a,b); U(c)" "domanda" query.sql` (sqlite + pattern + costrutti del prof)
- passaggi: `checker/passaggi_check.py soluzione.txt` (sulla versione NON a quadretti)
- test: `python checker/test_*.py` -> 16/16 verdi il 30/09
- audit prof: `checker/audit_prof.py` -> 12 errori dimostrati su 15: il prof sbaglia, non piegare i motori ai suoi numeri

## Cosa voleva jeans (regole)
- stile prof: passaggi e "poiché...", non risultati nudi; VSR+CSR+2PL sempre giustificati (dal 2022)
- niente risposte copiate parola per parola; SQL solo costrutti del prof (VIEW, non WITH)
- guardare SEMPRE il PDF renderizzato (titoli compresi) prima di dire "fatto"; accenti veri

## Aperto / da fare
- tratto penna "realistico" per --quadretti (ora Helvetica ~0,55 mm): chiedere un esempio
- B+-tree largo (6 foglie) in --quadretti passa a separatori a linea
- test SQL con `esercitazione_26_05_2026` (lab 20/09/2024 risolto a mano in aula), mai usato
- forum Moodle "Discussione esercizi tecnologie" non scaricato

## PDF di esempio (cartella esempi/ di questo zip)
COMPLETO, MINIMAL, VERTICALE_colori_minimal, QUADRETTI_colori_minimal (esame 12/06/2025) + CONFRONTO_E_SFIDA_PROF.
