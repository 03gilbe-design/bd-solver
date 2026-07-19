#!/usr/bin/env python3
"""scan_corpus.py — test RICORSIVO sul corpus intero.
Per ogni PDF in corpus_esami/:
  1. rileva se ha una soluzione ufficiale nel testo (pattern 'Ristrutturazione:' o righe TABELLA(...))
  2. se esiste dataset/<nome>.spec.json -> genera la traduzione e calcola le DIFFERENZE
     rispetto alle tabelle estratte dal PDF originale (confronto automatico, non a occhio)
  3. se non esiste ancora uno spec -> lo segnala come 'DA MODELLARE' (onesto: non finge copertura)

Uso: python dataset/scan_corpus.py
Uscita: tabella per esame con stato COPERTO/PARZIALE/DA MODELLARE + eventuali differenze.
"""
import sys, os, re, glob, json, subprocess, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "checker"))
import er

HERE = os.path.dirname(__file__)
CORPUS = os.path.join(HERE, "..", "corpus_esami")

# manifest esplicito: spec (senza .spec.json) -> file PDF sorgente nel corpus (senza .pdf)
# necessario perche' i nomi spec sono mnemonici (es. "aeroporto") mentre i PDF hanno nomi
# tipo "1-17_A" -> nessun match automatico possibile per stringa.
MANIFEST = {
    "aeroporto": "1-17_A",
    "scuola_sci": "1-18_A",
    "catena_alberghi": "12-22_A",
    "elearning": "2-14_A",
    "ristoranti_1222B": "12-22_B",
}

def _pdftotext(path):
    exe = shutil.which("pdftotext") or os.path.expanduser(
        r"~/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdftotext.exe")
    if not os.path.exists(exe) and not shutil.which("pdftotext"):
        return ""
    r = subprocess.run([exe, path, "-"], capture_output=True, text=True)
    return r.stdout

TABLE_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\(([A-Za-z0-9_,*\s]+)\)")

def extract_solution_tables(text):
    """Estrae righe tipo NOME(campo, campo*, ...) dal testo della soluzione ufficiale.
    Euristico (non un parser LaTeX): usato solo per stabilire SE una soluzione esiste
    e QUANTE tabelle nomina, non per un confronto byte-perfetto."""
    hits = {}
    for m in TABLE_RE.finditer(text):
        name, body = m.group(1), m.group(2)
        if len(body.split(",")) < 1:
            continue
        hits[name] = [c.strip() for c in body.split(",") if c.strip()]
    return hits

def has_official_solution(text):
    return ("Ristrutturazione" in text) or bool(re.search(r"[A-Z]{3,}\([A-Za-z_]+,", text))

def compare_spec_vs_extract(spec_path, extracted):
    spec = json.load(open(spec_path, encoding="utf-8"))
    errs = er.check(spec)
    if errs:
        return {"valida": False, "errori": errs}
    tables = er.translate(spec)
    got_names = {t["name"] for t in tables}
    exp_names = set(extracted)
    common = got_names & exp_names
    only_mine = got_names - exp_names
    only_theirs = exp_names - got_names
    return {"valida": True, "tabelle_mie": len(got_names), "tabelle_estratte": len(exp_names),
            "in_comune": len(common), "solo_mie": sorted(only_mine), "solo_prof": sorted(only_theirs)}

def main():
    pdfs = sorted(glob.glob(os.path.join(CORPUS, "*.pdf")))
    if not pdfs:
        print("nessun PDF nel corpus"); return
    specs = {os.path.basename(p)[:-len(".spec.json")]
             for p in glob.glob(os.path.join(HERE, "*.spec.json"))}
    pdf_to_spec = {v: k for k, v in MANIFEST.items() if k in specs}
    print(f"{'ESAME':45s} {'SOLUZIONE':10s} {'SPEC':6s} {'STATO'}")
    print("-" * 90)
    coperti, con_sol, totali = 0, 0, len(pdfs)
    for p in pdfs:
        name = os.path.basename(p)[:-4]
        text = _pdftotext(p)
        has_sol = has_official_solution(text)
        con_sol += has_sol
        spec_name = pdf_to_spec.get(name)
        if spec_name:
            spec_path = os.path.join(HERE, spec_name + ".spec.json")
            extracted = extract_solution_tables(text)
            cmp = compare_spec_vs_extract(spec_path, extracted)
            coperti += 1
            stato = f"OK spec={spec_name} comuni={cmp.get('in_comune','?')}/{cmp.get('tabelle_estratte','?')}"
        elif has_sol:
            stato = "DA MODELLARE (ha soluzione ufficiale, nessuno spec ancora)"
        else:
            stato = "senza soluzione ufficiale nel testo (o non estratta)"
        print(f"{name[:45]:45s} {'si' if has_sol else 'no':10s} {'si' if spec_name else 'no':6s} {stato}")
    print("-" * 90)
    print(f"Totale esami: {totali} | con soluzione ufficiale rilevata: {con_sol} | con spec+test: {coperti}")
    print(f"Copertura reale: {coperti}/{con_sol} degli esami CON soluzione hanno un test automatico.")

if __name__ == "__main__":
    main()
