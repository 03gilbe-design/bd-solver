"""Test teoria: riconoscimento modello su domande reali + verifica risposte.
TRAIN = esami fino al 15/06/2026 (su cui e' tarata la banca) -> deve essere 100%.
TEST  = ultimo esame (14/09/2026 foto + lab 16/09/2026), MAI usato per tarare -> misurato a parte.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teoria import riconosci, verifica

TEST_SET = {'2026_09_14_foto', '2026_09_16_lab'}
D = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'dataset_pt2', 'domande_teoria.json'), encoding='utf-8'))

t0 = time.time()
for split in ('train', 'test'):
    casi = [d for d in D if (d['esame'] in TEST_SET) == (split == 'test')]
    errori = [(d['esame'], d['lettera'], riconosci(d['q'])[0] and riconosci(d['q'])[0]['id'], d['atteso'])
              for d in casi if (riconosci(d['q'])[0] or {}).get('id') != d['atteso']]
    for e in errori:
        print('  SBAGLIATO', e)
    print(f'{split.upper()}: {len(casi) - len(errori)}/{len(casi)} riconosciute')
    if split == 'train':
        assert not errori, 'train deve essere 100%'

# verifica risposta: una buona passa, una copiata e una monca no
dom = 'Illustrare le proprieta delle transazioni indicando quali moduli di un DBMS garantiscono ciascuna di esse.'
buona = ("Una transazione e' un'unita' logica di lavoro: termina con commit, rendendo definitive le modifiche, "
         "oppure con rollback, che le disfa del tutto. Le garanzie richieste sono quattro. Atomicita': niente "
         "effetti parziali, o tutto o niente. Consistenza: al termine nessun vincolo di integrita' risulta violato. "
         "Isolamento: il risultato non dipende da altre transazioni eseguite in parallelo. Persistenza: cio' che e' "
         "confermato sopravvive anche a un guasto. Chi le assicura: il gestore dei metodi d'accesso controlla i "
         "vincoli (consistenza); il gestore dell'esecuzione concorrente regola l'interleaving (isolamento e, "
         "insieme all'affidabilita', atomicita'); il gestore dell'affidabilita' usa log, undo e redo per atomicita' "
         "e persistenza.")
v = verifica(dom, buona, 3)
assert v['ok'], v
assert not verifica(dom, 'Atomicita, consistenza, isolamento, persistenza.', 3)['ok']
fp = os.path.join(os.path.dirname(__file__), '..', 'riferimenti_teoria', 'fonti', 'Domande_Tecnologie.txt')
if os.path.exists(fp):   # le fonti (materiale altrui) restano in locale, non su GitHub
    fonte = open(fp, encoding='utf-8').read()
    copiata = fonte[fonte.find('Le propriet'):][:1400]
    assert verifica(dom, copiata, 3)['ngram_copiati'] > 2, 'anti-copia non scatta'
else:
    print('SKIP anti-copia: manca riferimenti_teoria/fonti/ (solo in locale)')
print(f'VERIFICA RISPOSTE OK   ({time.time() - t0:.2f}s totali)')
