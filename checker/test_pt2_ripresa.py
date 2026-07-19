"""Test pt2_ripresa contro la soluzione UFFICIALE lesson_02_esercizio_ripresa_a_caldo_01:
UNDO={T2,T3}, REDO={T4,T5};
azioni UNDO (a ritroso): Delete(O6); Insert(O5); O3:=B5; O2:=B3; O1:=B1
azioni REDO (in avanti): O3:=A4; O4:=A6"""
import pt2_ripresa as pr

LOG = ("B(T1), B(T2), U(T2,O1,B1,A1), I(T1,O2,A2), B(T3), C(T1), B(T4), "
       "U(T3,O2,B3,A3), U(T4,O3,B4,A4), CK(T2,T3,T4), C(T4), B(T5), "
       "U(T3,O3,B5,A5), U(T5,O4,B6,A6), D(T3,O5,B7), A(T3), C(T5), I(T2,O6,A8)")

r = pr.ripresa(LOG)
assert r["undo"] == ["T2", "T3"], r["undo"]
assert r["redo"] == ["T4", "T5"], r["redo"]
assert r["undo_actions"] == ["Delete(O6)", "Insert(O5)", "O3 := B5", "O2 := B3", "O1 := B1"], r["undo_actions"]
assert r["redo_actions"] == ["O3 := A4", "O4 := A6"], r["redo_actions"]

for s in r["steps"]:
    print(s)
print("TUTTI I TEST OK")
