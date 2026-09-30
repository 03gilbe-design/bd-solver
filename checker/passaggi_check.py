"""Controlla che la soluzione MOSTRI I PASSAGGI come le soluzioni ufficiali del prof (Esercitazione 2016),
non solo il risultato. Uso: python checker/passaggi_check.py soluzione.tex|.txt
Per ogni tipo di esercizio presente: passi obbligatori nell'ordine del prof + niente papiri (max parole).
"""
import re, sys, json

# tipo: (riconosci, [passi in ordine: (nome, regex)], max parole sezione)
TIPI = {
 'ripresa': (r'ripresa|affidabilit', [('checkpoint', r'\bck\b|checkpoint'), ('insiemi UNDO/REDO', r'undo[\s\S]*redo'),
             ('UNDO a ritroso', r'undo[\s\S]{0,80}(ritroso|indietro)'), ('REDO in avanti', r'redo[\s\S]{0,80}avanti')], 350),
 'concorrenza': (r'concorrent|schedule', [('insieme conflitti', r'conflitt'), ('grafo', r'grafo'),
                 ('verdetto (CSR/VSR/nonSR)', r'esito|csr|vsr|nonsr|serializzabil')], 400),
 'costo': (r'ottimizz|costo', [('formula', r'formula|np\s*\(|nr\s*\(|np_|nr_|\bnp\b'), ('numeri', r'\d+\s*[x\*×]\s*\d+'),
           ('totale', r'totale')], 350),
 'btree': (r'b\+|b-tree|btree', [('costruzione', r'costruzion|a\)'), ('albero dopo ogni operazione', r'dopo\s+(l[\'’]?)?(insert|inserimento|delete|cancellazione)')], 300),
}


def sezioni(testo):
    """Divide per esercizio (a)..h) o intestazioni)."""
    parti = re.split(r'(?m)^\s*([a-h])\)\s*(?=[\(\[]\d)', testo)
    return [parti[i] + ') ' + parti[i + 1] for i in range(1, len(parti) - 1, 2)] or [testo]


def controlla(testo):
    t = re.sub(r'\\[a-zA-Z]+\*?|[{}$]', ' ', testo).lower()
    rep = []
    for sez in sezioni(t):
        testa = sez[:120]
        for tipo, (rx, passi, maxp) in TIPI.items():
            if re.search(rx, testa):
                pos, mancanti = 0, []
                for nome, prx in passi:
                    m = re.search(prx, sez[pos:])
                    if m:
                        pos += m.start()
                    else:
                        mancanti.append(nome)
                n = len(re.findall(r'\w+', sez))
                rep.append({'esercizio': sez[:2], 'tipo': tipo, 'passi_mancanti': mancanti, 'parole': n,
                            'troppo_lungo': n > maxp})
                break
    return {'ok': bool(rep) and all(not r['passi_mancanti'] and not r['troppo_lungo'] for r in rep), 'esercizi': rep}


if __name__ == '__main__':
    r = controlla(open(sys.argv[1], encoding='utf-8', errors='replace').read())
    print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.exit(0 if r['ok'] else 1)
