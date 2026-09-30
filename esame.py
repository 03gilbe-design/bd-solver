"""PUNTO D'INGRESSO UNICO PER L'ESAME (parte 2). Un comando fa tutta la catena di controllo.

  python esame.py spec.json [testo_esame.txt] [--doppia spec2.json] [--quadretti] [--colori]

spec.json: esercizi con motore (ripresa, schedule, costo, btree) + teoria {domanda, risposta, punti}
+ sql {domanda, query, [query2 = seconda formulazione indipendente], schema "T(a,b); U(c)"}.
Esce 0 solo se tutto e' verde. Output in out_esame/ (soluzione.pdf, soluzione_minimal.pdf).
Stdlib pura; pdflatex/pdftotext opzionali (su Termux: senza PDF si ferma al .tex)."""
import json, os, shutil, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(QUI, "checker"))
from controllo_trascrizione import plausibile, contro_testo, due_trascrizioni
from teoria import verifica
from sql_check import controlla as sql_controlla
from sql_prova import confronta as sql_confronta
from passaggi_check import controlla as passaggi

args = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args:
    sys.exit(__doc__)
spec_path = args[0]
spec = json.load(open(spec_path, encoding="utf-8"))
testo = open(args[1], encoding="utf-8", errors="replace").read() if len(args) > 1 else None
righe, tutto_ok = [], True


def passo(nome, fn):
    global tutto_ok
    t0 = time.time()
    try:
        problemi = fn() or []
    except Exception as ex:                  # un controllo che si rompe e' un problema, non un OK
        problemi = [f"errore interno: {ex!r}"]
    tutto_ok &= not problemi
    righe.append((nome, "OK" if not problemi else "DA SISTEMARE", time.time() - t0, problemi))


passo("plausibilita' (cose impossibili in un esame)", lambda: plausibile(spec))
if testo:
    passo("trascrizione contro il testo d'esame", lambda: contro_testo(spec, testo)[1])
if "--doppia" in sys.argv:
    altra = json.load(open(sys.argv[sys.argv.index("--doppia") + 1], encoding="utf-8"))
    passo("doppia trascrizione indipendente", lambda: due_trascrizioni(spec, altra))
for e in spec["esercizi"]:
    ide = f"{e.get('id', '?')})"
    if e["tipo"] == "teoria" and e.get("risposta"):
        def t(e=e):
            v = verifica(e.get("domanda", ""), " ".join(e["risposta"]), e.get("punti", 3))
            return [] if v["ok"] else [f"mancano {v.get('mancanti')} | parole {v.get('parole')} in {v.get('range')} "
                                       f"| copiate {v.get('ngram_copiati')}"]
        passo(f"teoria {ide}", t)
    if e["tipo"] == "sql":
        schema = e.get("schema") or spec.get("schema", "")
        passo(f"sql {ide} sintassi+pattern", lambda e=e, s=schema:
              (lambda r: r["errori"] + r["avvisi"])(sql_controlla(s, e.get("domanda", ""), e["query"])))
        if e.get("query2"):
            passo(f"sql {ide} eseguita su 400 DB contro la 2a formulazione", lambda e=e, s=schema:
                  (lambda r: [] if r["uguali"] else [f"DIVERSE: dati {r['dati']} -> {r['q1']} vs {r['q2']}"])(
                      sql_confronta(s, e["query"], e["query2"])))
        else:
            righe.append((f"sql {ide} eseguita", "SALTATO", 0, ["aggiungi 'query2' (altra tecnica) per provarla davvero"]))

out = os.path.join(os.path.dirname(os.path.abspath(spec_path)) or ".", "out_esame")
extra = [x for x in ("--quadretti", "--colori", "--verticale") if x in sys.argv]
for nome, flags in (("soluzione", []), ("soluzione_minimal", ["--minimal"])):
    def gen(nome=nome, flags=flags):
        d = os.path.join(out, nome)
        r = subprocess.run([sys.executable, os.path.join(QUI, "checker", "solve_pt2.py"), spec_path, d, *flags, *extra],
                           capture_output=True, encoding="utf-8", errors="replace")
        pdf = os.path.join(d, "soluzione.pdf")
        if not os.path.exists(pdf):
            return [] if "non disponibile" in r.stdout else [r.stdout[-300:] + r.stderr[-300:]]
        shutil.copy(pdf, os.path.join(out, nome + ".pdf"))
        prob = [l for l in r.stdout.splitlines() if "AVVISO" in l]
        qa = subprocess.run([sys.executable, os.path.join(QUI, "checker", "pdf_qa.py"), pdf],
                            capture_output=True, encoding="utf-8", errors="replace")
        if qa.returncode:
            prob.append("pdf_qa: " + qa.stdout.strip()[-200:])
        if shutil.which("pdftotext") and "--quadretti" not in extra:
            txt = subprocess.run(["pdftotext", "-enc", "UTF-8", pdf, "-"], capture_output=True,
                                 encoding="utf-8", errors="replace").stdout
            p = passaggi(txt)
            prob += [f"{x['esercizio']} passi mancanti {x['passi_mancanti']}" for x in p["esercizi"] if x["passi_mancanti"]]
        return prob
    passo(f"PDF {nome} (+ pdf_qa, passaggi)", gen)

print(f"\n{'passo':58} {'esito':13} {'tempo':>6}")
for nome, esito, dt, prob in righe:
    print(f"{nome:58} {esito:13} {dt:5.1f}s")
    for x in prob:
        print(f"      - {x}")
print("\nPRONTO DA CONSEGNARE: rileggi le pagine di out_esame/*.pdf" if tutto_ok else
      "\nNON CONSEGNARE: sistema i punti DA SISTEMARE (all'esame NON modificare i motori in checker/)")
sys.exit(0 if tutto_ok else 1)
