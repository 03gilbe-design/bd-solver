"""Giustificazioni stile prof (30/09/2026), confrontate con soluzioni ufficiali."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt2_schedule as s, pt2_ripresa as r

# Esercitazione 2016 (soluzione prof): vincoli t2<t1, t3<t1, t3<t4, t4<t1, t4<t2 ; seriale t3,t4,t2,t1 -> VSR
o = s.parse('r4(t), w2(t), r1(t), r4(y), r3(y), w4(y), w4(z), w3(z), w1(t), w2(x), w1(z)')
assert set(s.vincoli_view(o)) == {(2, 1), (3, 1), (3, 4), (4, 1), (4, 2)}, s.vincoli_view(o)
assert s.seriale_view(o) == (3, 4, 2, 1)
assert s.ciclo(o) and 'CSR' in s.perche_non_2pl(o)

# slide "8 - Esecuzione concorrente Parte III" pag.14: CSR ma NON 2PL, colpa di w1(y) dopo il rilascio su x
o = s.parse('r1(x),w1(x),r2(x),w2(x),r3(y),w1(y)')
assert s.ciclo(o) is None and 'w1(y)' in s.perche_non_2pl(o)

# 12/06/2025: nonSR, vincoli contraddittori T2<T3 e T3<T2
o = s.parse('r1(t), w2(z), r1(x), r3(z), r1(y), w2(t), r3(y), w3(x), w2(y), r3(t), r2(x)')
v = s.vincoli_view(o)
assert (2, 3) in v and (3, 2) in v and s.seriale_view(o) is None

# ripresa ufficiale 01: dopo B(T5) UNDO={T2,T3,T5}; finale UNDO={T2,T3} REDO={T4,T5}
res = r.ripresa('B(T1), B(T2), U(T2,O1,B1,A1), I(T1,O2,A2), B(T3), C(T1), B(T4), U(T3,O2,B3,A3), '
                'U(T4,O3,B4,A4), CK(T2,T3,T4), C(T4), B(T5), U(T3,O3,B5,A5), U(T5,O4,B6,A6), D(T3,O5,B7), '
                'A(T3), C(T5), I(T2,O6,A8)')
assert res['evoluzione'][1].startswith('B(T5): UNDO = {T2, T3, T5}'), res['evoluzione']
assert res['undo'] == ['T2', 'T3'] and res['redo'] == ['T4', 'T5']
print('GIUSTIFICAZIONI OK: 2016 vincoli+seriale identici al prof, slide 2PL, nonSR 12/06, ripresa 01')
