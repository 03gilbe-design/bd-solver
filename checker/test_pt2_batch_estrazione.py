"""Test BATCH deterministico: estrae automaticamente (regex, pt2_extract.py,
NO OCR/LLM) gli schedule da tutti i .txt pdftotext-nativi in TXT_DIR e li fa
girare sul motore pt2_schedule, verificando solo che non crashino e
stampando risultato — non e' un confronto con soluzioni (non tutte
disponibili), e' un test di ROBUSTEZZA su input reali mai visti a mano."""
import os
import sys
import pt2_extract as ex
import pt2_schedule as ps

TXT_DIR = os.environ.get("TXT_DIR", "")
if not TXT_DIR or not os.path.isdir(TXT_DIR):
    print("SKIP: imposta TXT_DIR alla cartella con i .txt estratti da pdftotext")
    sys.exit(0)

tested = 0
for fn in sorted(os.listdir(TXT_DIR)):
    if not fn.endswith(".txt"):
        continue
    text = open(os.path.join(TXT_DIR, fn), encoding="utf8", errors="replace").read()
    data = ex.extract(text)
    for sched in data.get("schedule_candidati", []):
        try:
            ops = ps.parse(sched)
            if not ops:
                continue
            cls = ps.classify(sched)
            is2pl = ps.is_2pl(ops)
            tested += 1
            print(f"{fn}: [{sched[:50]}...] -> {cls}, 2PL={is2pl}")
        except Exception as e:
            print(f"{fn}: ERRORE su schedule -> {e}")
            raise

print(f"\n{tested} schedule estratti automaticamente ed eseguiti senza errori")
