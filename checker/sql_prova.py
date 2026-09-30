"""Prova VERA di una query SQL: la esegue su tanti database casuali (sqlite) e la confronta con una
seconda formulazione scritta in modo indipendente. Se su un'istanza i risultati differiscono, stampa
il controesempio (dati + le due uscite): almeno una delle due query e' sbagliata.

Uso: python checker/sql_prova.py "T(a,b); U(c,a)" q1.sql q2.sql [--istanze 400] [--insiemi]
  --insiemi: confronta come insiemi (ignora duplicati), per domande dove DISTINCT e' irrilevante.
Valori generati per NOME di colonna (piccoli domini, cosi' join e condizioni scattano spesso):
  data*/ora*  -> date 2024-2026;  nome/titolo/cognome/descr* -> stringhe, alcune iniziano con 'A';
  tipo/categoria/regione/... -> poche parole;  altro -> interi 1..5 (anche chiavi, per avere match).
Stdlib pura (Termux)."""
import random, re, sqlite3, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sql_check import schema_sql, pg_to_sqlite

PAROLE = ["Aula1", "Aula2", "Basi di Dati", "Bianchi", "Verona", "Padova", "Rossi", "Lombardia", "Veneto",
          "fisica", "online-web", "online-app", "ordinario", "Cardiologia"]


def costanti(*query):
    """stringhe usate nelle query ('Basi di Dati', 'A%' -> 'A...'), cosi' i dati le contengono spesso
    e le condizioni scattano davvero (senza, un filtro dimenticato puo' non vedersi mai)."""
    out = []
    for q in query:
        for s in re.findall(r"'([^']*)'", q):
            if not re.match(r"\d{4}-\d\d-\d\d$", s):
                out.append(s.replace("%", "x").replace("_", "y"))
    return out or PAROLE


CONFINI = ["2025-12-31", "2026-01-01", "2026-12-31", "2027-01-01"]   # date al confine d'anno


def valore(col, rnd, cost=(), nulli=False):
    c = col.lower()
    if nulli and rnd.random() < 0.12:
        return None                                   # NULL: NOT IN e NOT EXISTS qui divergono
    if c.startswith(("data", "ora")) or "data" in c:
        if rnd.random() < 0.25:
            return rnd.choice(CONFINI)
        return f"{rnd.choice([2024, 2025, 2026])}-{rnd.randint(1, 12):02d}-{rnd.randint(1, 28):02d}"
    if any(k in c for k in ("nome", "titolo", "cognome", "descr", "indirizzo", "comune", "citta", "provincia",
                            "regione", "tipo", "categoria", "specialita", "ruolo", "posizione", "modello", "colore")):
        return rnd.choice(list(cost)) if cost and rnd.random() < 0.6 else rnd.choice(PAROLE)
    if c in ("coperto", "pagato"):
        return rnd.choice([0, 1])
    return rnd.randint(1, 5)


def tabelle(schema):
    return [(m.group(1), [c.strip().strip("*_ ") for c in m.group(2).split(",") if c.strip()])
            for m in re.finditer(r"(\w+)\s*\(([^)]*)\)", schema)]


def esegui(db, q):
    stm = [s.strip() for s in pg_to_sqlite(q).split(";") if s.strip()]
    for s in stm[:-1]:
        s = re.sub(r"(?is)^(create\s+view\s+\w+\s+as)\s*\((.*)\)$", r"\1 \2", s)
        db.execute(s)
    return db.execute(stm[-1]).fetchall()


def _istanza(schema, rnd, cost, nulli):
    db = sqlite3.connect(":memory:")
    db.executescript(schema_sql(schema))
    dati = {}
    for t, cols in tabelle(schema):
        # dati POSSIBILI: prima colonna = chiave (unica, mai NULL). Due righe con la stessa chiave in un DB
        # vero non esistono: all'inizio le generavo e davano "differenze" finte (30/09).
        righe, chiavi = [], set()
        for _ in range(rnd.randint(0, 6)):
            r = (valore(cols[0], rnd, cost),) + tuple(valore(c, rnd, cost, nulli) for c in cols[1:])
            if r[0] not in chiavi:
                chiavi.add(r[0]); righe.append(r)
        db.executemany(f"INSERT INTO {t} VALUES ({','.join('?' * len(cols))})", righe)
        dati[t] = righe
    return db, dati


def confronta(schema, q1, q2, istanze=400, insiemi=False, seed=1):
    """Fase 1 senza NULL (dati 'da esame'), fase 2 con NULL. Se differiscono SOLO con i NULL: 'solo_null'
    (dipende da cosa lo schema ammette: chiavi/NOT NULL). Tabelle vuote, duplicati, pareggi e date di confine
    compaiono da soli nei dati casuali."""
    rnd = random.Random(seed)
    cost = costanti(q1, q2)
    for fase, nulli in ((1, False), (2, True)):
        for n in range(istanze):
            db, dati = _istanza(schema, rnd, cost, nulli)
            r1, r2 = esegui(db, q1), esegui(db, q2)
            a, b = (set(r1), set(r2)) if insiemi else (sorted(map(repr, r1)), sorted(map(repr, r2)))
            if a != b:
                return {"uguali": False, "solo_null": nulli, "istanza": n, "dati": dati, "q1": r1, "q2": r2}
    return {"uguali": True, "istanze": 2 * istanze}


def mutanti(q):
    """Query 'rotte apposta' (errori tipici): se i test NON le distinguono dall'originale, o i dati sono
    deboli o quel pezzo di query non serve."""
    out = []
    regole = [(r"(?i)\bNOT\s+(EXISTS|IN)\b", r"\1", "tolto NOT"), (r"(?i)\bEXISTS\b", "NOT EXISTS", "aggiunto NOT"),
              (r"<=", "<", "<= -> <"), (r"(?<![<>!])>=", ">", ">= -> >"), (r"(?<![<>=!])<(?![=>])", "<=", "< -> <="),
              (r"(?<![<>=!-])>(?!=)", ">=", "> -> >="), (r"(?i)\bAND\b", "OR", "AND -> OR"),
              (r"(?i)\bMAX\(", "MIN(", "MAX -> MIN"), (r"(?i)\bCOUNT\(\s*DISTINCT\s+", "COUNT(", "tolto DISTINCT"),
              (r"(?i)\bLEFT\s+JOIN\b", "JOIN", "LEFT JOIN -> JOIN")]
    for rx, rep, nome in regole:
        for m in re.finditer(rx, q):
            out.append((f"{nome} (pos {m.start()})", q[:m.start()] + re.sub(rx, rep, m.group(0), count=1) + q[m.end():]))
    for m in re.finditer(r"(?i)\bAND\s+[^()]*?(?=\bAND\b|\bGROUP\b|\bORDER\b|\)|$)", q):
        out.append((f"tolta condizione '{m.group(0).strip()[:40]}'", q[:m.start()] + q[m.end():]))
    return out


def forza(schema, q, istanze=150):
    """Mutation testing: ritorna i mutanti SOPRAVVISSUTI (non distinti da q). Idealmente nessuno."""
    vivi = []
    for nome, m in mutanti(q):
        try:
            if confronta(schema, q, m, istanze)["uguali"]:
                vivi.append(nome)
        except sqlite3.Error:
            pass                                       # mutante non valido: conta come ucciso
    return vivi


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    ist = int(sys.argv[sys.argv.index("--istanze") + 1]) if "--istanze" in sys.argv else 400
    r = confronta(a[0], open(a[1], encoding="utf-8").read(), open(a[2], encoding="utf-8").read(),
                  ist, "--insiemi" in sys.argv)
    if "--mutanti" in sys.argv:
        for i, q in enumerate(a[1:3], 1):
            vivi = forza(a[0], open(q, encoding="utf-8").read())
            print(f"q{i}: mutanti sopravvissuti {vivi if vivi else 'nessuno (i test vedono ogni errore tipico)'}")
    if r["uguali"]:
        print(f"UGUALI su {r['istanze']} database casuali (anche con NULL, duplicati, date di confine)")
    else:
        print(("DIVERSE SOLO CON I NULL (conta se lo schema li ammette: chiavi/NOT NULL) " if r["solo_null"]
               else "DIVERSE ") + f"all'istanza {r['istanza']}:")
        for t, rows in r["dati"].items():
            print(f"  {t}: {rows}")
        print(f"  q1 -> {r['q1']}\n  q2 -> {r['q2']}")
        sys.exit(1)
