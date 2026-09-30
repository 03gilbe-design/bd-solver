"""ricostruisci: foto con buchi -> esame d'archivio riconosciuto e pezzi letti dall'originale;
CK(??) determinato dal log; transazione illeggibile -> candidati (mai scelta a caso).
Archivio sintetico in una cartella temporanea (i testi d'esame veri non sono nel repo)."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ricostruisci import cerca_archivio, completa_log

d = tempfile.mkdtemp()
open(os.path.join(d, "esame_giugno.txt"), "w", encoding="utf-8").write(
    "DUMP; B(T1), B(T2), B(T3), I(T1,O1,A1), U(T1,O4,B4,A4), C(T3), CK(T1,T2), B(T5),\n"
    "WHERE P.Regione <> 'Lombardia'\nNP(MEDICO) = 12, NP(VISITA) = 2000, NP(PAZIENTE) = 130\n")
open(os.path.join(d, "altro_esame.txt"), "w", encoding="utf-8").write(
    "S: r1(x), w2(y), r3(z)\nNP(COLLEGIO) = 200, NR(COLLEGIO) = 1600\nWHERE CL.Regione = 'Veneto'\n")

foto = ("DUMP; B(T1), B(T2), B(T3), I(T1,O1,A1), U(T1,O4,B4,A4), C(T3), CK(??), B(T5),\n"
        "WHERE P.Regione ?? 'Lombardia'\nNP(MEDICO) = 12, NP(VISITA) = ??, NP(PAZIENTE) = 130\n")
r = cerca_archivio(foto, cartella=d)
assert r["esame"] == "esame_giugno", r
orig = [x[1] for x in r["ricostruite"] if x[3]]
assert any("CK(T1,T2)" in o for o in orig) and any("<>" in o for o in orig) and any("2000" in o for o in orig), orig

log = completa_log("B(T1), B(T2), B(T3), C(T3), CK(??), B(T4), C(??)")
assert log[0][1] == "CK(T1,T2)" and "determinato" in log[0][2], log
assert "candidati ['T1', 'T2', 'T4']" in log[1][2], log          # non determinabile: elenca, non sceglie
assert "UNICA" in completa_log("B(T1), C(??)")[0][2]              # una sola attiva: determinata
print("TUTTI I TEST OK")
