CREATE VIEW PREN_ANNO2 AS (
  SELECT attrazione, EXTRACT(YEAR FROM data_prenotazione) AS anno, COUNT(*) AS num
  FROM PRENOTAZIONE
  GROUP BY attrazione, EXTRACT(YEAR FROM data_prenotazione));

SELECT A.nome
FROM ATTRAZIONE A JOIN PREN_ANNO2 V ON V.attrazione = A.codice
WHERE V.anno = 2025
  AND NOT EXISTS (SELECT * FROM PREN_ANNO2 V2
                  WHERE V2.attrazione = V.attrazione AND V2.anno < 2025
                    AND V2.num >= V.num);
