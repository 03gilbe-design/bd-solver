"""Test passaggi_check: soluzione con passi (stile prof) passa, solo-risultato no, papiro no."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from passaggi_check import controlla
buona = """e) (6) Esecuzione concorrente
Conflitti: (w2(x),r1(x)), (w2(y),r3(y)). Grafo dei conflitti: T2->T1, T2->T3, aciclico. S e' CSR.
g) (5) Ottimizzazione costo
Formula NLJ: NP(esterna) + NR(sel) x NP(interna). 625 x 2000 = 1250000. Totale: 1.250.230"""
assert controlla(buona)['ok'], controlla(buona)
assert not controlla("e) (6) Esecuzione concorrente\nS e' CSR.")['ok']
assert not controlla("g) (5) Ottimizzazione costo\nTotale 1250230")['ok']
assert not controlla(buona.replace('aciclico.', 'aciclico. ' + 'bla ' * 500))['ok']
print('PASSAGGI OK: con passi passa, solo risultato bocciato, papiro bocciato')
