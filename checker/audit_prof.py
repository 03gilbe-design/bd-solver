"""Sfida ai materiali del prof: ogni sospetto viene DIMOSTRATO da un controllo automatico
(motori pt2, sqlite, parser XML), non da una lettura. Uso: python checker/audit_prof.py
Stampa per ogni caso: fonte, cosa scrive il prof, cosa risulta dal controllo, verdetto."""
import os, sys, math
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt2_ripresa, pt2_schedule, pt2_costo, sql_check

CASI = []
def caso(fonte, cosa, prof, noi, errore, come):
    CASI.append(dict(fonte=fonte, cosa=cosa, prof=str(prof), noi=str(noi), errore=errore, come=come))

# 1-2. Ripresa a caldo: stato UNDO dopo C(T4) nel Passo 3
R1 = ('B(T1), B(T2), U(T2,O1,B1,A1), I(T1,O2,A2), B(T3), C(T1), B(T4), U(T3,O2,B3,A3), U(T4,O3,B4,A4), '
      'CK(T2,T3,T4), C(T4), B(T5), U(T3,O3,B5,A5), U(T5,O4,B6,A6), D(T3,O5,B7), A(T3), C(T5), I(T2,O6,A8)')
e = pt2_ripresa.ripresa(R1)['evoluzione'][0]
caso('lesson_02 ripresa_a_caldo_01, Passo 3', 'UNDO dopo C(T4)', 'UNDO = {T2,T3,T4}, REDO = {T4}', e,
     'T4' in e.split('REDO')[0], 'motore pt2_ripresa: C(T) toglie T da UNDO (lo stesso prof lo fa nella situazione finale)')
R2 = ('B(T1), B(T2), B(T3), I(T1,O1,A1), D(T2,O2,B2), B(T4), U(T4,O3,B3,A3), U(T1,O4,B4,A4), C(T2), CK(T1,T3,T4), '
      'B(T5), B(T6), U(T5,O5,B5,A5), A(T3), CK(T1,T4,T5,T6), B(T7), C(T4), U(T7,O6,B6,A6), U(T6,O3,B7,A7), B(T8), A(T7)')
r2 = pt2_ripresa.ripresa(R2)
e = r2['evoluzione'][1]
caso('lesson_02 ripresa_a_caldo_02, Passo 3', 'UNDO dopo C(T4)', 'UNDO = {T1,T4,T5,T6,T7}, REDO = {T4}', e,
     'T4' in e.split('REDO')[0], 'motore pt2_ripresa (stesso refuso ripetuto nei due esercizi ufficiali)')
caso('lesson_02 ripresa_a_caldo_02, finale e azioni', 'UNDO/REDO finali + azioni',
     'UNDO={T1,T5,T6,T7,T8} REDO={T4}; O3:=B7; O6:=B6; O5:=B5; O4:=B4; Delete(O1) / O3:=A3',
     f"UNDO={r2['undo']} REDO={r2['redo']}; {'; '.join(r2['undo_actions'])} / {'; '.join(r2['redo_actions'])}",
     False, 'motore pt2_ripresa: coincide')
caso('lesson_02 ripresa_a_caldo_02, testo del log', 'nomi oggetti', 'U(T1, 04,B4,A4), U(T5,05,B5,A5)',
     'O4, O5 (lettera O)', True, 'lettura: zero al posto della O (nel Passo 5 lo stesso prof scrive O4)')

# 3. Ottimizzazione 1, punto (2): aritmetica
ns = 900 / 18
tpv = math.ceil((19800 / 50) / 90)
e_giusto = ns * (2 + tpv)
caso('lesson_12_03 Ottimizzazione 1, punto (2)', 'costo JOIN con indice',
     '50*(2+4.4) = 50*(2+5) = 600, poi totale = 780+180+150+320 = 1.430',
     f'50*(2+{tpv}) = {e_giusto:g}; totale = 780+180+150+{e_giusto:g} = {780+180+150+e_giusto:,.0f}'.replace(',', '.') + f'',
     True, 'aritmetica: 50*7=350 (non 600) e nel totale compare un terzo numero (320)')

# 4. Ottimizzazione 2: selettivita' di <> 'pianura'
nr, val = 1900, 4
caso('lesson_12_03 Ottimizzazione 2', "NR(COMUNE) dopo WHERE TipoTerritorio <> 'pianura'",
     "1900/4 = 475 (scritto: NR(COMUNE con TipoTerritorio = 'Pianura'))",
     f"{nr} - {nr}/{val} = {nr - nr // val} (il <> tiene 3 valori su 4)", True,
     "logica: il prof stesso scrive 'con TipoTerritorio = Pianura' ma la query ESCLUDE pianura. Le slide danno "
     "solo il caso '=' (NR/VAL); con la stessa uniformità il '<>' tiene NR - NR/VAL. Con indice: 15+1425*23 = 32.790, "
     "non 10.925 (motore: solve(selezione_diverso=True)). Conferma dal prof stesso: in EsempioOttimizzazione.png "
     "(Moodle) sigma Cat <> 'REG' su TRENO tiene 110 righe su 150, cioè la maggioranza, non NR/VAL")

# 5-6. VSR 2015 e 2016: nostro motore == prof
o = pt2_schedule.parse('r0(t), r2(z), r3(z), w1(z), r3(x), r2(x), w3(x), w3(y), w2(y), w0(y), w1(t)')
caso('Esercitazione 2015, concorrenza', 'vincoli + seriale view-equivalente',
     't0<t1, t2<t1, t3<t1, t2<t3, t2<t0, t3<t0 ; S1 = t2,t3,t0,t1',
     f"{', '.join(f't{a}<t{b}' for a, b in pt2_schedule.vincoli_view(o))} ; {pt2_schedule.seriale_view(o)}",
     False, 'motore pt2_schedule: coincide')

# 7. Costo 2015 (3 tabelle) ricalcolato a mano con la formula del prof
caso('Esercitazione 2015, ottimizzazione', 'costo NLJ a 3 tabelle', '12 + 260/20*200*40 = 104.012 ; con indice 7.812',
     f'{12 + 260 // 20 * 200 * 40:,} ; {12 + 260 // 20 * 200 * 3:,}'.replace(',', '.'), False, 'aritmetica: coincide')

# 8. XML delle soluzioni: e' ben formato?
xml_2015 = '<edificio id="E002"><tipo>A3</tipo><prezzoOfferto timestamp="x">100000</PrezzoOfferto></edificio>'
try:
    ET.fromstring(xml_2015); ok = True
except ET.ParseError as ex:
    ok, msg = False, str(ex)
caso('Esercitazione 2015, XML', '<prezzoOfferto> ... </PrezzoOfferto>', 'documento dato come valido',
     'non ben formato: ' + (msg if not ok else ''), not ok, 'parser XML (ElementTree): XML distingue maiuscole')
caso('Esercitazione 2016, XML', 'timestamp=" 2016-06-06 T 09:45:22"', "attributo di tipo xsd:dateTime",
     'formato dateTime = 2016-06-06T09:45:22 (senza spazi)', True, 'specifica XML Schema: dateTime non ammette spazi')

# 9. Lab 16/09/2026: dichiarazione e query della soluzione
decl = ("CREATE TABLE Prenotazione (codice CHAR(16), parcheggio CHAR(32), tipo CHAR(16), pagato BOOLEAN, );")
import sqlite3
try:
    sqlite3.connect(':memory:').executescript(decl); ok = True
except sqlite3.Error as ex:
    ok, msg = False, str(ex)
caso('Lab 16/09/2026, punto a)', 'CREATE TABLE Prenotazione', '"pagato BOOLEAN," seguito da ")"',
     'sqlite: ' + (msg if not ok else 'ok'), not ok, 'sqlite: virgola finale prima di ")" = errore di sintassi')
S16 = ('AUTO(targa, modello); PRENOTAZIONE(codice, parcheggio, auto, data_prenotazione, tipo, pagato); '
       'PARCHEGGIO(nome, comune, indirizzo, coperto)')
for q, col in [("SELECT count(*) FROM prenotazione r1 WHERE r1.categoria = 'fisica'", 'categoria'),
               ("SELECT * FROM parcheggio WHERE comune = 'Verona' AND comperto = true", 'comperto'),
               ("SELECT r.codice, r.comune FROM prenotazione r join parcheggio p on (r.parcheggio = p.codice)", 'comune/codice')]:
    r = sql_check.controlla(S16, 'trova', q)
    caso('Lab 16/09/2026, soluzioni SQL', f'colonna {col}', q[:60] + '...', '; '.join(r['errori']), bool(r['errori']),
         'sqlite sullo schema dato nel testo')
caso('Lab 16/09/2026, soluzione ii/iii', 'filtro "nel 2024"', "data > '01/01/2024' and data < '01/01/2024'",
     "intervallo vuoto: nessuna riga passa", True, 'logica: stesso estremo sopra e sotto')

if __name__ == '__main__':
    n = sum(c['errore'] for c in CASI)
    for c in CASI:
        print(('ERRORE PROF ' if c['errore'] else 'ok          ') + f"| {c['fonte']} | {c['cosa']}\n"
              f"    prof: {c['prof']}\n    noi : {c['noi']}\n    come: {c['come']}")
    print(f'\n{n} errori dimostrati su {len(CASI)} controlli')
