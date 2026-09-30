"""Foto venuta male / pezzo che non si vede: RICOSTRUIRE invece di indovinare.

1. ARCHIVIO: gli esami si riciclano (14/09/2026 = 15/06/2026 parola per parola). Il testo letto dalla foto,
   anche con buchi (scrivi ?? o [...] dove non si legge), viene cercato nei testi d'esame passati
   (riferimenti_teoria/esami/*.txt, solo in locale: materiale del prof). Se una riga combacia oltre la
   soglia, il pezzo mancante si LEGGE dall'esame originale.
2. LOG DI RIPRESA: un CK(...) illeggibile e' DETERMINATO dal log: sono le transazioni attive in quel punto
   (B visto, C/A non ancora). Un record con transazione illeggibile (U(T?,O5,B5,A5)) ha come candidati solo
   le transazioni attive in quel punto.
Uso:
  python checker/ricostruisci.py archivio "testo con ?? dove non si legge"
  python checker/ricostruisci.py ck "B(T1), B(T2), C(T1), CK(??), B(T3)"
Stdlib pura (Termux). Da usare SOLO dopo aver guardato bene la foto."""
import difflib, glob, os, re, sys

QUI = os.path.dirname(os.path.abspath(__file__))
ARCHIVIO = os.path.join(QUI, "..", "riferimenti_teoria", "esami")
BUCO = re.compile(r"\?\?+|\[\.\.\.\]|…")


def _righe(testo):
    return [re.sub(r"\s+", " ", r).strip() for r in testo.splitlines() if len(r.strip()) > 8]


def cerca_archivio(parziale, soglia=0.75, cartella=ARCHIVIO):
    """Per ogni riga letta (con buchi), la riga piu' simile dell'archivio. Ritorna l'esame che combacia di
    piu' e, per le righe con buchi, la riga originale da cui leggere il pezzo mancante."""
    esami = {os.path.basename(f)[:-4]: _righe(open(f, encoding="utf-8", errors="replace").read())
             for f in glob.glob(os.path.join(cartella, "*.txt"))}
    lette = _righe(parziale)
    punteggi = {}
    for nome, righe in esami.items():
        tot = 0.0
        for r in lette:
            pulita = BUCO.sub("", r)
            tot += max((difflib.SequenceMatcher(None, pulita, x).ratio() for x in righe), default=0)
        punteggi[nome] = tot / max(len(lette), 1)
    if not punteggi:
        return {"esame": None, "somiglianza": 0, "ricostruite": []}
    nome = max(punteggi, key=punteggi.get)
    ricostruite = []
    for r in lette:
        if BUCO.search(r):
            pulita = BUCO.sub("", r)
            best = max(esami[nome], key=lambda x: difflib.SequenceMatcher(None, pulita, x).ratio())
            s = difflib.SequenceMatcher(None, pulita, best).ratio()
            ricostruite.append((r, best, round(s, 2), s >= soglia))
    return {"esame": nome, "somiglianza": round(punteggi[nome], 2), "ricostruite": ricostruite,
            "classifica": sorted(punteggi.items(), key=lambda x: -x[1])[:3]}


def completa_log(log):
    """CK(??) -> transazioni attive; T? in un record -> candidati = attive in quel punto."""
    rec = re.findall(r"(CK|B|C|A|U|I|D)\s*\(([^)]*)\)", log)
    attive, out = [], []
    for k, args in rec:
        a = [x.strip() for x in args.split(",")]
        if k == "CK":
            out.append(("CK", "CK(" + ",".join(attive) + ")", "determinato: transazioni attive in quel punto"
                        if BUCO.search(args) or not args.strip() else "letto"))
            continue
        t = a[0] if a else ""
        if BUCO.search(t) or t in ("T?", "T"):
            cand = list(attive) if k in "UIDCA" else []
            out.append((k, f"{k}({args})", f"transazione illeggibile: candidati {cand}" +
                        (" -> UNICA, determinata" if len(cand) == 1 else "")))
            if len(cand) == 1:
                t = cand[0]
            else:
                continue
        if k == "B":
            attive.append(t)
        elif k in ("C", "A") and t in attive:
            attive.remove(t)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    if sys.argv[1] == "archivio":
        r = cerca_archivio(sys.argv[2])
        print(f"ESAME PIU' SIMILE: {r['esame']}  (somiglianza media {r['somiglianza']})  classifica: {r.get('classifica')}")
        for letta, orig, s, ok in r["ricostruite"]:
            print(f"  letta   : {letta}\n  archivio: {orig}\n  -> {'RICOSTRUITA' if ok else 'troppo diversa, NON fidarti'} ({s})")
    else:
        for k, rec, nota in completa_log(sys.argv[2]):
            if nota != "letto" or k == "CK":
                print(f"  {rec:30} {nota}")
