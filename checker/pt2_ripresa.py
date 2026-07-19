#!/usr/bin/env python3
"""pt2_ripresa.py — esercizio "Gestore dell'affidabilita'" (ripresa a caldo) della III prova.
Dato il LOG al momento del guasto, produce i 5 passi della procedura ufficiale.

FONTE VERIFICATA: lesson_02_esercizio_ripresa_a_caldo_01.pdf (esercizio risolto ufficiale):
  Passo 1: risali all'ultimo CK
  Passo 2: UNDO = transazioni attive nel CK, REDO = {}
  Passo 3: dal CK in avanti: B(T)->UNDO+=T; C(T)-> T da UNDO a REDO
           (A(T) NON sposta: la transazione abortita resta in UNDO)
  Passo 4: UNDO a ritroso su TUTTO il log: U(T,O,B,A)->O:=B ; I(T,O,A)->Delete(O) ;
           D(T,O,B)->Insert(O)   [solo per T in UNDO]
  Passo 5: REDO in avanti dal'inizio: U(T,O,B,A)->O:=A ; I(T,O,A)->Insert/O:=A ;
           D(T,O,B)->Delete(O)   [solo per T in REDO]

Record log: B(Ti) begin, C(Ti) commit, A(Ti) abort, CK(T..) checkpoint,
U(Ti,Oj,Before,After) update, I(Ti,Oj,After) insert, D(Ti,Oj,Before) delete."""
import re

def parse_log(s):
    out = []
    for m in re.finditer(r"(B|C|A|CK|U|I|D)\s*\(([^)]*)\)", s):
        kind = m.group(1)
        args = [a.strip() for a in m.group(2).split(",")]
        out.append((kind, args))
    return out

def ripresa(log_str):
    log = parse_log(log_str)
    # Passo 1: ultimo checkpoint
    ck_idx = max((i for i, (k, _) in enumerate(log) if k == "CK"), default=None)
    if ck_idx is None:
        undo, redo = set(), set()
        start = 0
        ck_txt = "nessun checkpoint: si riparte dall'inizio del log"
    else:
        undo = set(log[ck_idx][1])          # Passo 2
        redo = set()
        start = ck_idx + 1
        ck_txt = f"ultimo CK({','.join(log[ck_idx][1])}) in posizione {ck_idx+1}"
    def _set(s):
        return "{" + ", ".join(sorted(s)) + "}" if s else "{}"
    steps = [f"Passo 1: {ck_txt}",
             f"Passo 2: UNDO = {_set(undo)} , REDO = {{}}"]
    # Passo 3: dal CK in avanti
    for k, args in log[start:]:
        if k == "B":
            undo.add(args[0])
        elif k == "C":
            undo.discard(args[0]); redo.add(args[0])
        # A(T): resta in UNDO (fonte ufficiale: A(T3) e T3 resta in UNDO)
    steps.append(f"Passo 3 (finale): UNDO = {_set(undo)} , REDO = {_set(redo)}")
    # Passo 4: undo a ritroso su tutto il log
    undo_actions = []
    for k, args in reversed(log):
        if k == "U" and args[0] in undo:
            undo_actions.append(f"{args[1]} := {args[2]}")
        elif k == "I" and args[0] in undo:
            undo_actions.append(f"Delete({args[1]})")
        elif k == "D" and args[0] in undo:
            undo_actions.append(f"Insert({args[1]})")
    steps.append("Passo 4 (UNDO, a ritroso): " + "; ".join(undo_actions))
    # Passo 5: redo in avanti
    redo_actions = []
    for k, args in log:
        if k == "U" and args[0] in redo:
            redo_actions.append(f"{args[1]} := {args[3]}")
        elif k == "I" and args[0] in redo:
            redo_actions.append(f"Insert({args[1]}={args[2]})")
        elif k == "D" and args[0] in redo:
            redo_actions.append(f"Delete({args[1]})")
    steps.append("Passo 5 (REDO, in avanti): " + "; ".join(redo_actions))
    return {"undo": sorted(undo), "redo": sorted(redo),
            "undo_actions": undo_actions, "redo_actions": redo_actions,
            "steps": steps}
