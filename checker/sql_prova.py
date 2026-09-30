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


def valore(col, rnd, cost=()):
    c = col.lower()
    if c.startswith(("data", "ora")) or "data" in c:
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


def confronta(schema, q1, q2, istanze=400, insiemi=False, seed=1):
    rnd = random.Random(seed)
    cost = costanti(q1, q2)
    for n in range(istanze):
        db = sqlite3.connect(":memory:")
        db.executescript(schema_sql(schema))
        dati = {}
        for t, cols in tabelle(schema):
            righe = [tuple(valore(c, rnd, cost) for c in cols) for _ in range(rnd.randint(0, 6))]
            db.executemany(f"INSERT INTO {t} VALUES ({','.join('?' * len(cols))})", righe)
            dati[t] = righe
        r1, r2 = esegui(db, q1), esegui(db, q2)
        a, b = (set(r1), set(r2)) if insiemi else (sorted(map(repr, r1)), sorted(map(repr, r2)))
        if a != b:
            return {"uguali": False, "istanza": n, "dati": dati, "q1": r1, "q2": r2}
    return {"uguali": True, "istanze": istanze}


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    ist = int(sys.argv[sys.argv.index("--istanze") + 1]) if "--istanze" in sys.argv else 400
    r = confronta(a[0], open(a[1], encoding="utf-8").read(), open(a[2], encoding="utf-8").read(),
                  ist, "--insiemi" in sys.argv)
    if r["uguali"]:
        print(f"UGUALI su {r['istanze']} database casuali")
    else:
        print(f"DIVERSE all'istanza {r['istanza']}:")
        for t, rows in r["dati"].items():
            print(f"  {t}: {rows}")
        print(f"  q1 -> {r['q1']}\n  q2 -> {r['q2']}")
        sys.exit(1)
