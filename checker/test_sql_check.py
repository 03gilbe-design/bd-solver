"""Test sql_check. TRAIN = query chat 14/09/2026 (c,d). TEST = lab 16/09/2026 (soluzioni prof CON refusi reali)."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sql_check import controlla

t0 = time.time()
S14 = 'INSEGNAMENTO(codice, titolo, CFU); LEZIONE(insegnamento, aula, data, durata); AULA(codice, nome, numero_posti)'
c = """SELECT I.titolo, I.CFU
FROM INSEGNAMENTO I
WHERE NOT EXISTS (
  SELECT 1 FROM LEZIONE L, AULA A
  WHERE L.insegnamento = I.codice AND L.aula = A.codice AND A.nome LIKE 'A%')"""
d = """WITH OreAula AS (
  SELECT L.aula, SUM(L.durata) AS ore_totali
  FROM LEZIONE L, INSEGNAMENTO I
  WHERE L.insegnamento = I.codice AND I.titolo = 'Basi di Dati'
    AND L.data BETWEEN '2026-01-01' AND '2026-12-31'
  GROUP BY L.aula)
SELECT A.nome, A.numero_posti
FROM AULA A, OreAula O
WHERE A.codice = O.aula AND O.ore_totali = (SELECT MAX(ore_totali) FROM OreAula)"""
dc = 'insegnamenti le cui lezioni non sono mai state svolte in un aula con nome che inizia per A'
dd = 'aule che nel 2026 hanno ospitato il maggior numero di ore di basi di dati'
assert controlla(S14, dc, c)['ok'], controlla(S14, dc, c)
assert 'WITH' in ' '.join(controlla(S14, dd, d)['avvisi'])  # chat 14/09 usava WITH: il prof no
d = d.replace('WITH OreAula AS (', 'CREATE VIEW OreAula AS').replace('GROUP BY L.aula)', 'GROUP BY L.aula;')
assert controlla(S14, dd, d)['ok'], controlla(S14, dd, d)
# negativi costruiti: NOT dimenticato, colonna sbagliata
assert not controlla(S14, dc, c.replace('NOT EXISTS', 'EXISTS'))['ok']
assert not controlla(S14, dd, d.replace('numero_posti', 'posti'))['ok']
print('TRAIN (chat 14/09): 2/2 ok, 2/2 errori costruiti bocciati')

# TEST SET: lab 16/09/2026, testo della soluzione del prof COPIATO com'e' (refusi inclusi)
S16 = ('AUTO(targa, num_telaio, modello, colore, km, cilindrata, posti, proprietario); '
       'PRENOTAZIONE(codice, parcheggio, posto, auto, data_prenotazione, data_ora_inizio, data_ora_fine, tipo, pagato); '
       'PARCHEGGIO(nome, comune, indirizzo, coperto)')
prof = {
 'i': ("parcheggi con piu prenotazioni online che prenotazioni fisiche. Per ciascun parcheggio riportare il nome",
       """SELECT r.parcheggio FROM prenotazione r WHERE r.tipo <> 'fisica' GROUP BY r.parcheggio
HAVING COUNT(*) > ( SELECT count(*) FROM prenotazione r1 WHERE r1.categoria = 'fisica' AND r1.parcheggio = r.parcheggio )""",
       'categoria'),
 'iii': ("quanti parcheggi di Verona hanno numero di prenotazioni superiore al numero medio di Padova",
         """CREATE VIEW nprenotazioni AS ( SELECT r.codice, r.comune, COUNT(*) as num
FROM prenotazione r join parcheggio p on (r.parcheggio = p.codice)
WHERE data_prenotazione > '01/01/2024' and data_prenotazione < '01/01/2024' GROUP BY r.codice, r.comune );
SELECT count(*) FROM nprenotazioni n WHERE n.comune = 'Verona'
AND n.num > ( SELECT AVG( n1.num ) FROM nprenotazioni n1 WHERE n1.comune = 'Padova' )""", 'comune'),
 'iv': ("tutti i parcheggi coperti del comune di Verona",
        "SELECT * FROM parcheggio WHERE comune = 'Verona' AND comperto = true", 'comperto'),
}
corrette = {
 'i': """SELECT p.nome, p.comune, p.indirizzo FROM parcheggio p JOIN prenotazione r ON r.parcheggio = p.nome
WHERE r.tipo <> 'fisica' GROUP BY p.nome, p.comune, p.indirizzo
HAVING COUNT(*) > (SELECT COUNT(*) FROM prenotazione r1 WHERE r1.tipo = 'fisica' AND r1.parcheggio = p.nome)""",
 'iii': """CREATE VIEW npren AS SELECT p.nome, p.comune, COUNT(*) AS num
FROM prenotazione r JOIN parcheggio p ON r.parcheggio = p.nome
WHERE EXTRACT(YEAR FROM r.data_prenotazione) = 2024 GROUP BY p.nome, p.comune;
SELECT COUNT(*) FROM npren n WHERE n.comune = 'Verona'
AND n.num > (SELECT AVG(n1.num) FROM npren n1 WHERE n1.comune = 'Padova')""",
 'iv': "SELECT * FROM parcheggio WHERE comune = 'Verona' AND coperto = true",
}
beccati = 0
for k, (dom, q, refuso) in prof.items():
    r = controlla(S16, dom, q)
    assert not r['ok'] and refuso in ' '.join(r['errori']), (k, r)
    beccati += 1
    rc = controlla(S16, dom, corrette[k])
    assert rc['ok'], (k, rc)
print(f'TEST (lab 16/09): refusi prof beccati {beccati}/3, versioni corrette promosse 3/3   ({time.time()-t0:.2f}s)')

# "per tutti" vero (2017): senza doppia negazione deve avvisare, con doppia NOT EXISTS no
S17 = 'AULA(nome, capienza); DOCENTE(cf, ruolo); LEZIONE(docente, aula, semestre)'
du = 'aule dove nel 1 semestre hanno svolto lezione tutti i docenti con ruolo ordinario'
sbagliata = "SELECT a.nome, a.capienza FROM aula a JOIN lezione l ON l.aula = a.nome JOIN docente d ON d.cf = l.docente WHERE d.ruolo = 'ordinario'"
giusta = """SELECT a.nome, a.capienza FROM aula a WHERE NOT EXISTS (
  SELECT * FROM docente d WHERE d.ruolo = 'ordinario' AND NOT EXISTS (
    SELECT * FROM lezione l WHERE l.docente = d.cf AND l.aula = a.nome AND l.semestre = 1))"""
assert 'universale' in ' '.join(controlla(S17, du, sbagliata)['avvisi'])
assert controlla(S17, du, giusta)['ok'], controlla(S17, du, giusta)
print('UNIVERSALE: doppia negazione richiesta e riconosciuta')
