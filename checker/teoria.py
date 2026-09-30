"""Teoria II parte: riconosce il modello di una domanda e controlla una risposta.

Uso:
  python checker/teoria.py "testo domanda" [punti]            -> modello + punti da coprire + lunghezza obiettivo
  python checker/teoria.py "testo domanda" [punti] risp.txt   -> verifica risposta (copertura, lunghezza, anti-copia)

La banca (riferimenti_teoria/banca_teoria.json) NON contiene risposte: solo i punti
obbligatori. La prosa la scrive il modello ogni volta; qui si controlla che sia completa,
della lunghezza giusta e NON copiata parola per parola dalle fonti (riferimenti_teoria/fonti/*.txt).
Stdlib pura (gira su Termux).
"""
import json, os, re, sys, glob, unicodedata

QUI = os.path.dirname(os.path.abspath(__file__))
RIF = os.path.join(QUI, '..', 'riferimenti_teoria')
PAROLE_PER_PUNTO = (15, 90)   # ponytail: max da Domande_Tecnologie (mediana 238); min basso: la completezza la garantiscono i PUNTI, il min blocca solo le risposte da una riga (30/09: minimal complete a ~20-28/punto)
NGRAM, MAX_NGRAM_COPIATI = 8, 2


def norm(s):
    s = unicodedata.normalize('NFKD', s.replace('’', "'").replace('‘', "'"))
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()


def banca():
    return json.load(open(os.path.join(RIF, 'banca_teoria.json'), encoding='utf-8'))['modelli']


def riconosci(domanda):
    """-> (modello, varianti attive). Punteggio = n. chiavi trovate, poi lunghezza totale."""
    q = norm(domanda)
    best, best_score = None, (0, 0)
    for m in banca():
        if any(norm(e) in q for e in m.get('esclude', [])):
            continue
        hit = [k for k in m['chiavi'] if norm(k) in q]
        score = (len(hit), sum(len(k) for k in hit))
        if score > best_score:
            best, best_score = m, score
    if not best:
        return None, []
    return best, [v for v in best['varianti'] if norm(v) in q]


_VUOTE = set("illustrare illustri descrivere descriva presenti presentare studente indicare indichi "
              "inoltre quali quale dettaglio particolare seguenti punti esempio mostrando utilizzo "
              "struttura modulo ciascuna ciascuno essere della delle degli dalla dello nella nelle".split())


def cerca_slide(domanda, n=3):
    """Domanda MAI vista: dove rispondere? Nelle slide del prof (riferimenti_teoria/slide/, una pagina per
    \\f), non a memoria ne' su Wikipedia. Punteggio = radici (6 lettere) della domanda presenti nella pagina."""
    radici = {w[:6] for w in re.findall(r"[a-z+\-]{5,}", norm(domanda)) if w not in _VUOTE}
    ris = []
    for f in sorted(glob.glob(os.path.join(RIF, 'slide', '*.txt'))):
        for p, testo in enumerate(open(f, encoding='utf-8', errors='replace').read().split('\f'), 1):
            t = norm(testo)
            hit = {r for r in radici if r in t}
            if hit:
                righe = [l.strip() for l in testo.splitlines() if any(r in norm(l) for r in hit) and len(l.strip()) > 3]
                ris.append((len(hit), os.path.basename(f)[:-4], p, righe[:3]))
    ris.sort(key=lambda x: (-x[0], x[1].startswith('APPUNTI')))   # a pari punteggio prima le slide del prof
    return ris[:n]


def punti_richiesti(m, varianti):
    return m['punti'] + [p for v in varianti for p in m['varianti'][v]]


def _ngrams(testo):
    w = re.findall(r"\w+", norm(testo))
    return {tuple(w[i:i + NGRAM]) for i in range(len(w) - NGRAM + 1)}


def fonti_ngrams():
    s = set()
    for f in glob.glob(os.path.join(RIF, 'fonti', '*.txt')):
        s |= _ngrams(open(f, encoding='utf-8', errors='replace').read())
    return s


def verifica(domanda, risposta, punti_domanda=3, fonti=None):
    m, var = riconosci(domanda)
    if not m:
        return {'ok': False, 'errore': 'domanda non riconosciuta'}
    r = norm(risposta)
    mancanti = [p[0] for p in punti_richiesti(m, var) if not any(norm(s) in r for s in p)]
    n = len(re.findall(r"\w+", risposta))
    lo, hi = PAROLE_PER_PUNTO[0] * punti_domanda, PAROLE_PER_PUNTO[1] * punti_domanda
    copiati = len(_ngrams(risposta) & (fonti_ngrams() if fonti is None else fonti))
    return {'ok': not mancanti and lo <= n <= hi and copiati <= MAX_NGRAM_COPIATI,
            'modello': m['id'], 'varianti': var, 'mancanti': mancanti,
            'parole': n, 'range': (lo, hi), 'ngram_copiati': copiati}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    dom = sys.argv[1]
    pt = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    if len(sys.argv) > 3:
        v = verifica(dom, open(sys.argv[3], encoding='utf-8').read(), pt)
        print(json.dumps(v, ensure_ascii=False, indent=1))
        sys.exit(0 if v['ok'] else 1)
    m, var = riconosci(dom)
    if not m:
        print('NON RICONOSCIUTA -> NON inventare, NON Wikipedia: rispondi da queste pagine delle slide del prof')
        print('(APPUNTI_jeans = appunti tuoi, fonte secondaria). Poi aggiungi il modello a banca_teoria.json.')
        trovate = cerca_slide(dom)
        for k, f, p, righe in trovate:
            print(f'  [{k} parole] {f}  pag. {p}')
            for r in righe:
                print('      ' + r[:110])
        radici = {w[:6] for w in re.findall(r"[a-z+\-]{5,}", norm(dom)) if w not in _VUOTE}
        if not trovate or trovate[0][0] * 2 < len(radici):
            print('ATTENZIONE: le slide coprono meno della meta\' delle parole della domanda. O e\' fuori programma,')
            print('o manca una slide (es. Moodle "Transazioni e architettura di un DBMS"). Non inventare: dillo.')
        if trovate and all(f.startswith('APPUNTI') for _, f, _, _ in trovate):
            print('ATTENZIONE: trovato SOLO negli appunti, non nelle slide ufficiali: verifica prima di fidarti.')
        sys.exit(2)
    print(f"MODELLO: {m['id']} - {m['titolo']}   varianti: {var or '-'}")
    print(f"LUNGHEZZA: {PAROLE_PER_PUNTO[0]*pt}-{PAROLE_PER_PUNTO[1]*pt} parole ({pt} punti)")
    print('DEVE TOCCARE:')
    for p in punti_richiesti(m, var):
        print('  -', ' / '.join(p))
    print('Scrivi con parole tue: >%d sequenze di %d parole uguali alle fonti = bocciata.' % (MAX_NGRAM_COPIATI, NGRAM))
    print('DOVE STA NELLE SLIDE (controlla che la domanda non chieda altro rispetto ai punti):')
    for k, f, p, _ in cerca_slide(dom):
        print(f'  [{k} parole] {f}  pag. {p}')
