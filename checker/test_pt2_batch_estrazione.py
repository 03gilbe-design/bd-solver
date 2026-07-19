"""Test BATCH deterministico: estrae automaticamente (regex, pt2_extract.py,
NO OCR/LLM) schedule e parametri costo da tutti i .txt pdftotext-nativi in
TXT_DIR e li fa girare sui motori, verificando solo che non crashino —
non e' un confronto con soluzioni (non tutte disponibili), e' un test di
ROBUSTEZZA su input reali mai visti a mano.

La parte costo usa una euristica grezza (tabella del primo VAL(attr,tab)
trovato = esterna, l'altra = interna, nessuna selezione sull'interna): non
e' un solutore automatico affidabile, serve solo a stressare pt2_costo.solve()
su combinazioni di numeri mai provate."""
import os
import sys
import pt2_extract as ex
import pt2_schedule as ps
import pt2_costo as pc

TXT_DIR = os.environ.get("TXT_DIR", "")
if not TXT_DIR or not os.path.isdir(TXT_DIR):
    print("SKIP: imposta TXT_DIR alla cartella con i .txt estratti da pdftotext")
    sys.exit(0)

tested_sched = tested_costo = 0
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
            tested_sched += 1
            print(f"{fn}: [{sched[:50]}...] -> {cls}, 2PL={is2pl}")
        except Exception as e:
            print(f"{fn}: ERRORE su schedule -> {e}")
            raise

    np_, nr_, val_ = data.get("NP", {}), data.get("NR", {}), data.get("VAL", {})
    if len(np_) == 2 and len(nr_) == 2 and val_:
        first_val_key = next(iter(val_))
        _, tab_outer = first_val_key.split(",")
        val_sel = val_[first_val_key]
        if tab_outer in np_ and tab_outer in nr_:
            tab_inner = next(t for t in np_ if t != tab_outer)
            try:
                r = pc.solve(np_outer=np_[tab_outer], nr_outer=nr_[tab_outer], val_sel_outer=val_sel,
                             np_inner=np_[tab_inner], pagine_sel_inner=np_[tab_inner],
                             nr_sel_inner=nr_.get(tab_inner, 0), val_join_inner=1,
                             interna_selezionata=False)
                tested_costo += 1
                print(f"{fn}: costo NLJ {tab_outer}x{tab_inner} = {r['totale']} accessi (stress-test, non verificato)")
            except Exception as e:
                print(f"{fn}: ERRORE su costo -> {e}")
                raise

print(f"\n{tested_sched} schedule + {tested_costo} calcoli costo estratti automaticamente ed eseguiti senza errori")
