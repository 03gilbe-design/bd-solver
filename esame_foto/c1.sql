SELECT COUNT(DISTINCT P.turista)
FROM PRENOTAZIONE P JOIN ATTRAZIONE A ON P.attrazione = A.codice
WHERE EXTRACT(YEAR FROM P.data_prenotazione) = 2026
  AND NOT EXISTS (SELECT *
                  FROM PRENOTAZIONE P2 JOIN ATTRAZIONE A2 ON P2.attrazione = A2.codice
                  WHERE P2.turista = P.turista AND A2.citta = A.citta
                    AND EXTRACT(YEAR FROM P2.data_prenotazione) = 2025);
