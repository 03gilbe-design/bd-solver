"""sql_prova: due formulazioni equivalenti -> UGUALI; una sbagliata -> controesempio.
Casi dagli esami veri (14/09/2026 = 15/06/2026, domande c e d)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sql_prova import confronta

S = "INSEGNAMENTO(codice, titolo, CFU); LEZIONE(insegnamento, aula, data, durata); AULA(codice, nome, numero_posti)"
# c) insegnamenti MAI tenuti in aule con nome che inizia per A: NOT EXISTS (chat 14/09) vs NOT IN (agente B)
c_chat = """SELECT I.titolo, I.CFU FROM INSEGNAMENTO I WHERE NOT EXISTS (
  SELECT 1 FROM LEZIONE L, AULA A WHERE L.insegnamento = I.codice AND L.aula = A.codice AND A.nome LIKE 'A%')"""
c_b = """SELECT I.titolo, I.CFU FROM INSEGNAMENTO I WHERE I.codice NOT IN (
  SELECT L.insegnamento FROM LEZIONE L JOIN AULA A ON L.aula = A.codice WHERE A.nome LIKE 'A%')"""
r = confronta(S, c_chat, c_b)
assert r["uguali"], r
# errore tipico: EXISTS senza NOT -> deve essere trovato
r = confronta(S, c_chat, c_chat.replace("NOT EXISTS", "EXISTS"))
assert not r["uguali"]

# d) aule con il massimo di ore di Basi di Dati nel 2026: WITH (chat) vs VIEW (stile prof) vs >= ALL
d_with = """WITH OreAula AS (SELECT L.aula, SUM(L.durata) AS ore FROM LEZIONE L, INSEGNAMENTO I
  WHERE L.insegnamento = I.codice AND I.titolo = 'Basi di Dati' AND L.data BETWEEN '2026-01-01' AND '2026-12-31'
  GROUP BY L.aula)
SELECT A.nome, A.numero_posti FROM AULA A, OreAula O WHERE A.codice = O.aula AND O.ore = (SELECT MAX(ore) FROM OreAula)"""
# seconda formulazione indipendente: GROUP BY + HAVING = MAX (sqlite non ha ">= ALL")
d_max = """SELECT A.nome, A.numero_posti FROM AULA A JOIN LEZIONE L ON L.aula = A.codice
  JOIN INSEGNAMENTO I ON L.insegnamento = I.codice
  WHERE I.titolo = 'Basi di Dati' AND L.data >= '2026-01-01' AND L.data <= '2026-12-31'
  GROUP BY A.codice, A.nome, A.numero_posti
  HAVING SUM(L.durata) = (SELECT MAX(t) FROM (SELECT SUM(L2.durata) AS t FROM LEZIONE L2 JOIN INSEGNAMENTO I2
     ON L2.insegnamento = I2.codice WHERE I2.titolo = 'Basi di Dati' AND L2.data >= '2026-01-01'
     AND L2.data <= '2026-12-31' GROUP BY L2.aula))"""
r = confronta(S, d_with, d_max)
assert r["uguali"], r
# errore tipico: anno dimenticato -> trovato
r = confronta(S, d_with, d_max.replace("L.data >= '2026-01-01' AND L.data <= '2026-12-31'", "1=1"))
assert not r["uguali"]
print("TUTTI I TEST OK")
