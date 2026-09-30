"""Controllo della TRASCRIZIONE foto/testo d'esame -> spec (l'anello piu' fragile: il 14/09 la chat ha
trascritto "<> 'Lombardia'" come se fosse "=" e il costo e' venuto sbagliato).

Uso:
  python checker/controllo_trascrizione.py spec.json testo_esame.txt     # spec contro il testo
  python checker/controllo_trascrizione.py specA.json specB.json         # due trascrizioni indipendenti
Il testo puo' venire da pdftotext (PDF) o da una trascrizione indipendente della foto.
Stdlib pura (Termux)."""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt2_ripresa, pt2_schedule


def _norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("≠", "<>").replace("!=", "<>")
    return re.sub(r"\s+", " ", s)


def _contigua(piccola, grande):
    n = len(piccola)
    return any(grande[i:i + n] == piccola for i in range(len(grande) - n + 1))


def contro_testo(spec, testo):
    t = _norm(testo)
    numeri = {int(x.replace(".", "")) for x in re.findall(r"\d[\d.]*", t) if x.replace(".", "").isdigit()}
    err, ok = [], []
    for e in spec["esercizi"]:
        ide = f"{e.get('id', '?')}) {e['tipo']}"
        if e["tipo"] == "ripresa":
            s = [(k, a) for k, a in pt2_ripresa.parse_log(e["log"])]
            g = [(k, [x.replace("0", "O") if re.match(r"0\d", x) else x for x in a])
                 for k, a in pt2_ripresa.parse_log(t)]
            (ok if _contigua(s, g) else err).append(f"{ide}: log di {len(s)} record " +
                                                    ("trovato identico nel testo" if _contigua(s, g) else "NON trovato identico"))
        elif e["tipo"] == "schedule":
            s = pt2_schedule.parse(e["schedule"])
            g = pt2_schedule.parse(t)
            (ok if _contigua(s, g) else err).append(f"{ide}: schedule di {len(s)} azioni " +
                                                    ("identico nel testo" if _contigua(s, g) else "NON trovato identico"))
        elif e["tipo"] == "costo":
            p = e["parametri"]
            mancano = []
            for k, v in p.items():
                if isinstance(v, bool) or v is None:
                    continue
                v = int(v) if float(v).is_integer() else v
                if v in numeri:
                    continue
                derivabile = any(isinstance(v, int) and a % b == 0 and a // b == v
                                 for a in numeri for b in numeri if b and a > v)
                if not derivabile:
                    mancano.append(f"{k}={v}")
            (err if mancano else ok).append(f"{ide}: numeri " + ("tutti nel testo (o NR/VAL di numeri del testo)"
                                                                if not mancano else "NON nel testo: " + ", ".join(mancano)))
            diverso_testo = "<>" in t or re.search(r"\bnon (residenti|sono|e') ", t) is not None
            if diverso_testo and not p.get("selezione_diverso"):
                err.append(f"{ide}: il testo contiene '<>' (o una negazione) ma lo spec NON ha selezione_diverso "
                           "-> NR sel sarebbe NR/VAL invece di NR-NR/VAL (errore del 14/09)")
            if not diverso_testo and p.get("selezione_diverso"):
                err.append(f"{ide}: selezione_diverso=true ma nel testo non c'e' nessun '<>'")
            scritto = re.search(r"salvat\w* in (\d+) pagine", t)
            if scritto and int(scritto.group(1)) not in (p.get("outer_pagine_scritte"), p.get("pagine_sel_inner")):
                err.append(f"{ide}: il testo dice 'salvato in {scritto.group(1)} pagine' ma lo spec non usa quel numero")
        elif e["tipo"] == "btree":
            chiavi = [str(k) for f in e["foglie"] for k in f] + [str(o["key"]) for o in e.get("operazioni", [])]
            parole = set(re.findall(r"[A-Za-z0-9]+", t))
            mancano = [k for k in chiavi if k not in parole]
            fo = re.search(r"fan-?out\s*=?\s*(\d+)", t)
            if fo and int(fo.group(1)) != e["fanout"]:
                err.append(f"{ide}: fan-out {e['fanout']} ma il testo dice {fo.group(1)}")
            (err if mancano else ok).append(f"{ide}: {len(chiavi)} chiavi " +
                                            ("tutte nel testo" if not mancano else "NON nel testo: " + ", ".join(mancano)))
    return ok, err


def due_trascrizioni(a, b):
    """confronta SOLO i dati degli esercizi con motore, accoppiati per tipo (teoria/SQL sono testo libero)."""
    diff = []
    motori = ("ripresa", "schedule", "costo", "btree")
    ea = [x for x in a["esercizi"] if x["tipo"] in motori]
    eb = [x for x in b["esercizi"] if x["tipo"] in motori]
    if [x["tipo"] for x in ea] != [x["tipo"] for x in eb]:
        diff.append(f"esercizi diversi: {[x['tipo'] for x in ea]} vs {[x['tipo'] for x in eb]}")
    for x, y in zip(ea, eb):
        for k in sorted(set(x) | set(y)):
            if k in ("id", "punti", "titolo", "descrizione", "risposta", "risposta_minimal", "domanda", "nota", "note"):
                continue
            vx, vy = x.get(k), y.get(k)
            if k == "log":
                vx, vy = pt2_ripresa.parse_log(vx or ""), pt2_ripresa.parse_log(vy or "")
            if k == "schedule":
                vx, vy = pt2_schedule.parse(vx or ""), pt2_schedule.parse(vy or "")
            if vx != vy:
                diff.append(f"{x.get('id')}) {x['tipo']}.{k}: {vx} <> {vy}")
    return diff


if __name__ == "__main__":
    a = json.load(open(sys.argv[1], encoding="utf-8"))
    if sys.argv[2].endswith(".json"):
        d = due_trascrizioni(a, json.load(open(sys.argv[2], encoding="utf-8")))
        print("\n".join(d) if d else "LE DUE TRASCRIZIONI COINCIDONO")
        sys.exit(1 if d else 0)
    ok, err = contro_testo(a, open(sys.argv[2], encoding="utf-8", errors="replace").read())
    for x in ok:
        print("  ok     ", x)
    for x in err:
        print("  ERRORE ", x)
    sys.exit(1 if err else 0)
