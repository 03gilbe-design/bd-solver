#!/usr/bin/env python3
"""pt2_extract.py — estrazione DETERMINISTICA (regex, no LLM/OCR) di esercizi
pt2 dal testo di un esame (pdftotext -layout su PDF testo-nativo).

Estrae solo cio' che e' meccanicamente riconoscibile: la stringa schedule,
la stringa log di ripresa, i parametri NP/NR/VAL per il costo query. NON
estrae i nodi foglia del B+-tree (disegnati in caselle, non in testo lineare
affidabile) ne' testo di teoria: quelli restano da leggere a mano.

Uso: python pt2_extract.py file.txt  -> stampa JSON con quanto trovato."""
import re
import sys
import json

SCHED_RE = re.compile(r"^\s*S\d*\s*:\s*((?:[rw]\d+\([a-zA-Z]\)\s*,?\s*)+)", re.MULTILINE)
LOG_RE = re.compile(r"((?:[BCA]|CK|U|I|D)\([^)]*\)(?:\s*,\s*(?:[BCA]|CK|U|I|D)\([^)]*\))+)")
NP_RE = re.compile(r"NP\s*\(\s*([A-Za-z]+)\s*\)\s*=\s*(\d+)")
NR_RE = re.compile(r"NR\s*\(\s*([A-Za-z]+)\s*\)\s*=\s*(\d+)")
VAL_RE = re.compile(r"VAL\s*\(\s*([A-Za-z]+)\s*,\s*([A-Za-z]+)\s*\)\s*=\s*(\d+)")
PROF_RE = re.compile(r"profondit[àa]\s*(?:pari\s*a\s*)?(\d+)", re.IGNORECASE)
FANOUT_RE = re.compile(r"fan-?out\s*=\s*(\d+)", re.IGNORECASE)


def extract(text):
    out = {}

    scheds = [m.group(1).strip().rstrip(",") for m in SCHED_RE.finditer(text)]
    if scheds:
        out["schedule_candidati"] = scheds

    for m in LOG_RE.finditer(text):
        s = m.group(1)
        if "CK(" in s or ("B(" in s and "C(" in s):   # log di ripresa plausibile
            out.setdefault("log_candidati", []).append(s.strip())

    np_vals = {t: int(v) for t, v in NP_RE.findall(text)}
    nr_vals = {t: int(v) for t, v in NR_RE.findall(text)}
    val_vals = {(a, b): int(v) for a, b, v in VAL_RE.findall(text)}
    if np_vals:
        out["NP"] = np_vals
    if nr_vals:
        out["NR"] = nr_vals
    if val_vals:
        out["VAL"] = {f"{a},{b}": v for (a, b), v in val_vals.items()}

    profs = [int(p) for p in PROF_RE.findall(text)]
    if profs:
        out["profondita_candidate"] = profs

    fans = [int(f) for f in FANOUT_RE.findall(text)]
    if fans:
        out["fanout_candidati"] = fans

    return out


if __name__ == "__main__":
    text = open(sys.argv[1], encoding="utf8", errors="replace").read()
    print(json.dumps(extract(text), indent=2, ensure_ascii=False))
