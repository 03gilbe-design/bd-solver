"""Verifica che er.py riproduca lo schema relazionale atteso di esami REALI.
Confronta PROPRIETA strutturali (tabelle, chiavi, nullable, FK-target), non i nomi
esatti del prof -> test non overfittato. Run: python test_dataset.py"""
import json, os, sys, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "checker"))
import er

def props(tables):
    out = {}
    for t in tables:
        out[t["name"]] = {
            "pk": sorted(c for c, pk, _ in t["cols"] if pk),
            "nullable": sorted(c for c, _, n in t["cols"] if n),
            "fk_verso": sorted(ref for _, ref in t["fk"]),
        }
    return out

def check_case(spec_path):
    exp_path = spec_path.replace(".spec.json", ".expected.json")
    spec = json.load(open(spec_path, encoding="utf-8"))
    exp = json.load(open(exp_path, encoding="utf-8"))["tabelle"]
    errs = er.check(spec)
    assert errs == [], f"{spec_path}: spec non valida: {errs}"
    got = props(er.translate(spec))
    fails = []
    # stesse tabelle
    if set(got) != set(exp):
        fails.append(f"tabelle: attese {sorted(exp)} ottenute {sorted(got)}")
    for name, e in exp.items():
        g = got.get(name)
        if not g:
            continue
        if g["pk"] != sorted(e["pk"]):
            fails.append(f"{name}.pk: atteso {sorted(e['pk'])} ottenuto {g['pk']}")
        if g["nullable"] != sorted(e["nullable"]):
            fails.append(f"{name}.nullable: atteso {sorted(e['nullable'])} ottenuto {g['nullable']}")
        if g["fk_verso"] != sorted(e["fk_verso"]):
            fails.append(f"{name}.fk_verso: atteso {sorted(e['fk_verso'])} ottenuto {g['fk_verso']}")
    return fails

def main():
    d = os.path.dirname(__file__)
    SKIP = ("catalogo", "progressione", "biblioteche_16lug", "esB_ABCE")  # demo/senza expected verificato
    specs = sorted(s for s in glob.glob(os.path.join(d, "*.spec.json"))
                   if not any(k in os.path.basename(s) for k in SKIP))
    assert specs, "nessun caso .spec.json nel dataset"
    total = 0
    for s in specs:
        fails = check_case(s)
        name = os.path.basename(s).replace(".spec.json", "")
        if fails:
            print(f"[FAIL] {name}")
            for f in fails: print("   -", f)
            total += len(fails)
        else:
            print(f"[OK]   {name}")
    if total:
        print(f"\n{total} discrepanze"); sys.exit(1)
    print(f"\nTUTTI I {len(specs)} CASI OK")

if __name__ == "__main__":
    main()
