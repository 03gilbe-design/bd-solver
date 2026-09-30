CREATE VIEW PREN_ANNO AS (
  SELECT attrazione, EXTRACT(YEAR FROM data_prenotazione) AS anno, COUNT(*) AS num
  FROM PRENOTAZIONE
  GROUP BY attrazione, EXTRACT(YEAR FROM data_prenotazione));

SELECT A.nome
FROM ATTRAZIONE A JOIN PREN_ANNO V ON V.attrazione = A.codice
WHERE V.anno = 2025
  AND V.num > (SELECT COALESCE(MAX(V2.num), 0) FROM PREN_ANNO V2
               WHERE V2.attrazione = V.attrazione AND V2.anno < 2025);
