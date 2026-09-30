SELECT COUNT(DISTINCT X.turista)
FROM (SELECT P.turista, A.citta
      FROM PRENOTAZIONE P JOIN ATTRAZIONE A ON P.attrazione = A.codice
      WHERE EXTRACT(YEAR FROM P.data_prenotazione) = 2026
      EXCEPT
      SELECT P.turista, A.citta
      FROM PRENOTAZIONE P JOIN ATTRAZIONE A ON P.attrazione = A.codice
      WHERE EXTRACT(YEAR FROM P.data_prenotazione) = 2025) AS X;
