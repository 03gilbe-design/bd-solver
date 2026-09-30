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


def plausibile(spec):
    """Cose che in un esame NON possono esserci: se lo spec le contiene, la lettura della foto e' sbagliata
    (o va ricostruita). Ritorna la lista dei problemi."""
    p = []
    for e in spec["esercizi"]:
        ide = f"{e.get('id', '?')}) {e['tipo']}"
        if e["tipo"] == "ripresa":
            stato, ck = {}, 0
            for k, a in pt2_ripresa.parse_log(e["log"]):
                t = a[0] if a else None
                if k == "B":
                    if t in stato:
                        p.append(f"{ide}: B({t}) ripetuto")
                    stato[t] = "attiva"
                elif k == "CK":
                    ck += 1
                    attive = sorted(x for x, s in stato.items() if s == "attiva")
                    if sorted(a) != attive:
                        p.append(f"{ide}: CK({','.join(a)}) ma le attive in quel punto sono {attive}")
                elif stato.get(t) != "attiva":
                    p.append(f"{ide}: {k}({','.join(a)}) su {t} non attiva (manca B o gia' conclusa)")
                elif k in "CA":
                    stato[t] = k
                if k == "U" and len(a) != 4 or k in "ID" and len(a) != 3:
                    p.append(f"{ide}: {k}({','.join(a)}) ha {len(a)} argomenti (U=4, I/D=3)")
            if ck == 0:
                p.append(f"{ide}: nessun CK nel log (negli esami c'e' sempre)")
        elif e["tipo"] == "schedule":
            ops = pt2_schedule.parse(e["schedule"])
            ts = {t for _, t, _ in ops}
            if not ops or len(ts) > 6 or len(ops) > 20:
                p.append(f"{ide}: schedule anomalo ({len(ops)} azioni, {len(ts)} transazioni)")
        elif e["tipo"] == "costo":
            q = e["parametri"]
            if q["np_outer"] > q["nr_outer"] or q["np_inner"] > q.get("nr_sel_inner", q["np_inner"]) * 10 ** 6:
                p.append(f"{ide}: NP > NR (pagine piu' delle righe)")
            if q["val_sel_outer"] > q["nr_outer"] or q["val_join_inner"] > max(q.get("nr_sel_inner", 1), 1) * 10 ** 6:
                p.append(f"{ide}: VAL > NR")
            if q.get("pagine_sel_inner", 0) > q["np_inner"]:
                p.append(f"{ide}: selezione salvata in piu' pagine della tabella intera")
            if q.get("outer_pagine_scritte", 0) > q["np_outer"]:
                p.append(f"{ide}: selezione esterna salvata in piu' pagine della tabella intera")
            if q.get("prof_indice") is not None and not 1 <= q["prof_indice"] <= 5:
                p.append(f"{ide}: profondita' indice {q['prof_indice']} (negli esami 2-4)")
        elif e["tipo"] == "btree":
            f, fl = e["fanout"], e["foglie"]
            chiavi = [k for x in fl for k in x]
            if f not in (3, 4, 5, 6):
                p.append(f"{ide}: fan-out {f} insolito")
            if chiavi != sorted(chiavi) or len(set(chiavi)) != len(chiavi):
                p.append(f"{ide}: chiavi delle foglie non crescenti o ripetute: {chiavi}")
            mn = -(-(f - 1) // 2)
            for x in fl:
                if not mn <= len(x) <= f - 1:
                    p.append(f"{ide}: foglia {x} fuori dai limiti {mn}..{f - 1}")
            for o in e.get("operazioni", []):
                if o["op"] == "insert" and o["key"] in chiavi or o["op"] == "delete" and o["key"] not in chiavi \
                        and not any(q["key"] == o["key"] for q in e["operazioni"] if q["op"] == "insert"):
                    p.append(f"{ide}: {o['op']} {o['key']} incoerente con le foglie")
    return p


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
