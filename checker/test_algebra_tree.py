"""Self-test algebra_tree.py. Run: python test_algebra_tree.py"""
import algebra_tree as at

tree = {"op": "pi", "attrs": ["Nome", "Cognome"],
        "child": {"op": "join", "cond": None,
                   "left": {"op": "sigma", "cond": "Ritardo>0", "child": {"op": "table", "name": "VOLO"}},
                   "right": {"op": "table", "name": "PILOTA"}}}

out = at.render(tree, caption="Piloti dei voli in ritardo")
assert r"\begin{forest}" in out and r"\end{forest}" in out
assert r"$\pi_{Nome,Cognome}$" in out
assert r"$\sigma_{Ritardo>0}$" in out
assert "VOLO" in out and "PILOTA" in out

errs = at.check_uses_only_schema(tree, known_tables={"VOLO", "PILOTA"})
assert errs == [], errs
errs2 = at.check_uses_only_schema(tree, known_tables={"VOLO"})
assert any("PILOTA" in e for e in errs2), errs2

print("TUTTI I TEST OK")
