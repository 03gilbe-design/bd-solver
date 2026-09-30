"""Controllo deterministico di una query SQL d'esame (parte non deterministica: la scrive il modello).

Uso: python checker/sql_check.py "AULA(codice,nome,posti); LEZIONE(aula,data)" "testo domanda" query.sql

1. La query viene preparata su sqlite con lo schema dato (tabelle vuote): colonne/tabelle
   inesistenti o sintassi rotta -> errore. Qualche sintassi PostgreSQL viene tradotta prima.
2. Pattern dalla domanda -> costrutto atteso (es. "mai" -> NOT EXISTS/NOT IN/EXCEPT).
3. Lunghezza stile prof: max 15 righe, niente spiegazione obbligatoria.
Stdlib pura (gira su Termux).
"""
import re, sqlite3, sys, json

MAX_RIGHE = 15
# (regex sulla domanda, regex che la query deve contenere, nome pattern)
PATTERN = [
    (r"\bmai\b|\bnon (sono|è|e') (mai )?stat|\bnessun", r"not\s+exists|not\s+in|except|left\s+join[\s\S]*is\s+null", 'negazione'),
    (r"\b(hanno|ha|abbiano|abbia|sono stat[ie]|in cui)\b[^.]{0,60}\btutt[ie] (i|le|gli)\b",r"not\s+exists[\s\S]*not\s+exists|count\([\s\S]*=\s*\(\s*select\s+count|except", 'universale'),
    (r"maggior numero|numero massimo|pi[uù] alt|massim|il maggior", r"\bmax\s*\(|>=\s*all|order\s+by[\s\S]*limit", 'massimo'),
    (r"minor numero|minim", r"\bmin\s*\(|<=\s*all|order\s+by[\s\S]*limit", 'minimo'),
    (r"almeno due|almeno 2|pi[uù] di un[oa]? ", r"having\s+count|count\s*\([^)]*\)\s*>=?\s*[12]|<>|!=", 'almeno_due'),
    (r"\bmedi[oa]\b", r"\bavg\s*\(", 'media'),
    (r"per ciascun|per ogni", r"group\s+by|exists|\(\s*select", 'per_ciascuno'),
    (r"\bquant[ie]\b|\bnumero (di|delle|dei)\b", r"count\s*\(|sum\s*\(", 'conteggio'),
]


def schema_sql(schema):
    """'T(a,b); U(c)' oppure CREATE TABLE gia' scritti -> script sqlite."""
    if re.search(r'(?i)create\s+table', schema):
        return schema
    out = []
    for m in re.finditer(r'(\w+)\s*\(([^)]*)\)', schema):
        cols = [c.strip().strip('*_ ') for c in m.group(2).split(',') if c.strip()]
        out.append(f'CREATE TABLE {m.group(1)} ({", ".join(cols)});')
    return '\n'.join(out)


def pg_to_sqlite(q):
    q = re.sub(r'::\s*\w+', '', q)
    q = re.sub(r'(?i)\bilike\b', 'LIKE', q)
    q = re.sub(r'(?i)extract\s*\(\s*year\s+from\s+([^)]+)\)', r"CAST(strftime('%Y', \1) AS INTEGER)", q)
    q = re.sub(r'(?i)\bdate\s+(\'[^\']*\')', r'\1', q)
    q = re.sub(r'(?i)\bcurrent_date\b', "date('now')", q)
    return q


def controlla(schema, domanda, query):
    errori, avvisi = [], []
    db = sqlite3.connect(':memory:')
    db.executescript(schema_sql(schema))
    stmts = [s.strip() for s in pg_to_sqlite(query).split(';') if s.strip()]
    for s in stmts:
        try:
            if re.match(r'(?i)create\s+view', s):
                s = re.sub(r'(?is)^(create\s+view\s+\w+\s+as)\s*\((.*)\)$', r'\1 \2', s)  # PG ammette AS ( ... )
                db.execute(s)
                db.execute('SELECT * FROM ' + re.search(r'(?i)view\s+(\w+)', s).group(1))  # sqlite valida la view solo all'uso
            else:
                db.execute('EXPLAIN ' + s)
        except sqlite3.Error as e:
            errori.append(f'sqlite: {e}')
    d, ql = domanda.lower(), query.lower()
    for rq, rsql, nome in PATTERN:
        if re.search(rq, d) and not re.search(rsql, ql):
            avvisi.append(f'pattern {nome}: la domanda lo chiede, la query non sembra usarlo')
    # costrutti mai visti nelle soluzioni del prof (lui usa VIEW, subquery, HAVING, NOT IN/EXISTS)
    for rx, msg in [(r'^\s*with\b', 'WITH/CTE mai usato dal prof: usa CREATE VIEW'), (r'\bover\s*\(', 'window function mai usata dal prof'), (r'\blateral\b', 'LATERAL mai usato dal prof'), (r'\bfetch\s+first\b', 'FETCH FIRST mai usato dal prof')]:
        if re.search(rx, ql, re.M):
            avvisi.append(msg)
    righe = len([r for r in query.splitlines() if r.strip()])
    if righe > MAX_RIGHE:
        avvisi.append(f'{righe} righe > {MAX_RIGHE} (il prof ne usa 3-10)')
    return {'ok': not errori and not avvisi, 'errori': errori, 'avvisi': avvisi, 'righe': righe}


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    r = controlla(sys.argv[1], sys.argv[2], open(sys.argv[3], encoding='utf-8').read())
    print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.exit(0 if r['ok'] else 1)
