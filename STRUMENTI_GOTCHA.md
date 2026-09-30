# Studiare lo strumento prima di usarlo — errori trovati il 30/09/2026

Regola: prima di fidarsi di uno strumento (pacchetto LaTeX, sqlite, parser, shell) si guarda
come funziona davvero (documentazione ufficiale o sorgente). Ogni riga qui sotto è un errore
reale di oggi, con la causa vera e la regola che lo previene.

## LaTeX
| Sintomo | Causa vera | Regola |
|---|---|---|
| `$\bowtie$`, `B$^+$` stampati letterali | `esc()` scappava anche le parti matematiche volute | `esc()` lascia passare i segmenti `$...$` |
| barra blu della soluzione sparita sull'ultimo pezzo a fine pagina | `framed` 0.96 (quella installata) spezza il riquadro e l'ultimo pezzo perde il `\FrameCommand`; non ha `\FrameFirst/Mid/Last` | niente `framed`: soluzione = colore + `\leftskip`, non si rompe mai |
| riga del log fuori dal margine | `\texttt` ha spazi fissi, non si allarga né stringe | log, schedule, formule dentro `\raggedright` |
| "in-iziale", "doc-u-mento" in colonna stretta | senza `babel` italiano TeX sillaba all'inglese | verticale: `\raggedright` + `\hyphenpenalty=10000` (babel italiano potrebbe mancare su Termux) |
| quadretti: righe fuori griglia | ogni `\small/\footnotesize` cambia l'interlinea; liste e `center` aggiungono spazi elastici | in `--quadretti` tutte le misure hanno interlinea 5 mm, liste senza spazi, figure alte un numero intero di quadretti |
| minimo chiavi B+-tree sbagliato per fan-out pari | formula `ceil(f/2)-1` ricopiata nel renderer | numeri SEMPRE da `pt2_btree._mins()` (una sola fonte) |

## Python / Windows
| Sintomo | Causa vera | Regola |
|---|---|---|
| `pdf_qa.py` crash `UnicodeDecodeError` | `subprocess(text=True)` usa cp1252 su Windows | `encoding="utf-8", errors="replace"` + `pdftotext -enc UTF-8` |
| zip rotto su Termux | `Compress-Archive` di PowerShell 5.1 scrive `\` nei percorsi | zip SEMPRE con `zipfile` di Python e `/` |
| comando bloccato "Remove-Item on system path" | il filtro di sicurezza legge male regex/`*` nella stessa riga | script in file `.py`, niente cancellazioni in righe con regex |

## SQL (sqlite come controllore di query PostgreSQL)
- sqlite non accetta `CREATE VIEW v AS ( ... )` (PostgreSQL sì): `sql_check` toglie le parentesi.
- `ILIKE`, `::tipo`, `EXTRACT(YEAR FROM x)` tradotti prima di preparare la query.
- sqlite valida le colonne di una VIEW solo quando la si usa: `sql_check` fa `SELECT * FROM view`.

## Materia (non solo strumenti)
- Selettività: le slide danno solo `A = v` (NR/VAL). Per `A <> v` il prof stesso, in
  `EsempioOttimizzazione.png`, tiene 110 righe su 150 (la maggioranza): il complemento NR - NR/VAL.
  Il suo esercizio "Ottimizzazione 2" invece usa NR/VAL per un `<>` → errore (vedi `audit_prof.py`).
- XML distingue maiuscole (`<prezzoOfferto>` ≠ `</PrezzoOfferto>`); `xsd:dateTime` è `2016-06-06T09:45:22` senza spazi.
- Ripresa: `C(T)` toglie T da UNDO (il prof in due esercizi lo lascia per una riga, poi lo toglie nel finale).
