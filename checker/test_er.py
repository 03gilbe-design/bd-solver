"""Self-test er.py - assert only, nessun framework. Run: python test_er.py"""
import er

# --- caso minimo N:N -> tabella propria + FK
spec = {
  "entita": {
    "STUDENTE": {"attr": ["matricola","nome"], "id": [["matricola"]]},
    "CORSO":    {"attr": ["codice","titolo"], "id": [["codice"]]},
  },
  "relazioni": {
    "ISCRITTO": {"tra": ["STUDENTE","CORSO"],
                 "card": {"STUDENTE": [0,"N"], "CORSO": [0,"N"]},
                 "attr": ["data_iscrizione"]},
  }
}
assert er.check(spec) == [], er.check(spec)
t = {x["name"]: x for x in er.translate(spec)}
assert "ISCRITTO" in t, "N:N deve creare tabella propria"
# la tabella ISCRITTO ha PK composta dalle due chiavi
pk = [c for c,ispk,_ in t["ISCRITTO"]["cols"] if ispk]
assert set(pk) == {"studente_matricola","corso_codice"}, pk
assert "data_iscrizione" in [c for c,_,_ in t["ISCRITTO"]["cols"]]

# --- 1:N -> FK sul lato N, niente tabella
spec2 = {
  "entita": {
    "REPARTO":  {"attr": ["rid","nome"], "id": [["rid"]]},
    "PRODOTTO": {"attr": ["pid","descr","prezzo"], "id": [["pid"]]},
  },
  "relazioni": {
    "APPARTIENE": {"tra": ["PRODOTTO","REPARTO"],
                   "card": {"PRODOTTO": [1,1], "REPARTO": [0,"N"]}, "attr": []},
  }
}
assert er.check(spec2) == []
t2 = {x["name"]: x for x in er.translate(spec2)}
assert "APPARTIENE" not in t2, "1:N non deve creare tabella"
# PRODOTTO (lato 1, cioe max=1) ospita la FK verso REPARTO
prod_cols = [c for c,_,_ in t2["PRODOTTO"]["cols"]]
assert "reparto_rid" in prod_cols, prod_cols
assert any(ref == "REPARTO" for _, ref in t2["PRODOTTO"]["fk"])

# --- check rileva errori: entita senza id, cardinalita mancante
bad = {"entita": {"X": {"attr": ["a"], "id": []}},
       "relazioni": {"R": {"tra": ["X","Y"], "card": {"X":[1,1]}}}}
errs = er.check(bad)
assert any("senza identificatore" in e for e in errs), errs
assert any("inesistente 'Y'" in e or "entita inesistente" in e for e in errs), errs
assert any("manca cardinalita" in e for e in errs), errs

# --- nullable: partecipazione opzionale (min=0) sul lato FK -> colonna nullable
spec3 = {
  "entita": {
    "IMPIEGATO": {"attr": ["mat","nome"], "id": [["mat"]]},
    "AUTO":      {"attr": ["targa"], "id": [["targa"]]},
  },
  "relazioni": {
    "GUIDA": {"tra": ["IMPIEGATO","AUTO"],
              "card": {"IMPIEGATO": [0,1], "AUTO": [0,"N"]}, "attr": []},
  }
}
t3 = {x["name"]: x for x in er.translate(spec3)}
# IMPIEGATO vede "al piu 1" auto (max=1) -> ospita FK verso AUTO; min(IMPIEGATO)=0 -> nullable
nul = {c: n for c,_,n in t3["IMPIEGATO"]["cols"]}
assert nul.get("auto_targa") is True, t3["IMPIEGATO"]["cols"]
assert any(ref == "AUTO" for _, ref in t3["IMPIEGATO"]["fk"])

# --- identificazione esterna: relazione identificante deve essere (x,1) sul lato debole
weak = {
  "entita": {
    "EDIFICIO": {"attr": ["civico"], "id": [["civico"]]},
    "STANZA":   {"attr": ["numero"], "id": [["numero","IN"]]},   # id esterno via IN
  },
  "relazioni": {
    "IN": {"tra": ["STANZA","EDIFICIO"], "card": {"STANZA":[1,1], "EDIFICIO":[0,"N"]}, "attr": []},
  }
}
assert er.check(weak) == [], er.check(weak)
tw = {x["name"]: x for x in er.translate(weak)}
# STANZA eredita la chiave di EDIFICIO nella sua PK
spk = [c for c,ispk,_ in tw["STANZA"]["cols"] if ispk]
assert "numero" in spk and "edificio_civico" in spk, spk
# se il lato debole non e' (x,1) -> errore
weak_bad = {"entita": {"EDIFICIO":{"attr":["civico"],"id":[["civico"]]},
                        "STANZA":{"attr":["numero"],"id":[["numero","IN"]]}},
            "relazioni": {"IN":{"tra":["STANZA","EDIFICIO"],"card":{"STANZA":[1,"N"],"EDIFICIO":[0,"N"]}}}}
assert any("identificazione esterna" in e for e in er.check(weak_bad)), er.check(weak_bad)

# --- ISA strategia 'figli': tabelle separate con FK al padre
isa = {
  "entita": {
    "DIPENDENTE": {"attr": ["matricola","nome"], "id": [["matricola"]]},
    "PILOTA":     {"attr": ["anno_brevetto"], "id": [["matricola"]]},
    "ASSISTENTE": {"attr": ["anni_volo"], "id": [["matricola"]]},
  },
  "relazioni": {},
  "isa": [{"padre":"DIPENDENTE","figli":["PILOTA","ASSISTENTE"],"strategia":"figli"}]
}
ti = {x["name"]: x for x in er.translate(isa)}
assert "PILOTA" in ti and any(ref=="DIPENDENTE" for _,ref in ti["PILOTA"]["fk"]), ti["PILOTA"]
pil_pk = [c for c,pk,_ in ti["PILOTA"]["cols"] if pk]
assert "dipendente_matricola" in pil_pk, pil_pk
assert "anno_brevetto" in [c for c,_,_ in ti["PILOTA"]["cols"]]

# --- ISA strategia 'padre': accorpa, figli spariscono, discriminante 'tipo'
isa2 = dict(isa); isa2["isa"] = [{"padre":"DIPENDENTE","figli":["PILOTA","ASSISTENTE"],"strategia":"padre"}]
tp = {x["name"]: x for x in er.translate(isa2)}
assert "PILOTA" not in tp and "ASSISTENTE" not in tp, list(tp)
dcols = [c for c,_,_ in tp["DIPENDENTE"]["cols"]]
assert "anno_brevetto" in dcols and "anni_volo" in dcols and "tipo" in dcols, dcols

# --- tikz non crasha e contiene i nodi
tz = er.tikz(spec)
assert "\\begin{tikzpicture}" in tz and "STUDENTE" in tz and "ISCRITTO" in tz

# --- ISA strategia 'accorpa_nei_figli': padre sparisce, ogni figlio assorbe i suoi attributi
isa3 = dict(isa); isa3["isa"] = [{"padre":"DIPENDENTE","figli":["PILOTA","ASSISTENTE"],"strategia":"accorpa_nei_figli"}]
tf = {x["name"]: x for x in er.translate(isa3)}
assert "DIPENDENTE" not in tf, list(tf)
pil_cols = [c for c,_,_ in tf["PILOTA"]["cols"]]
assert "matricola" in pil_cols and "nome" in pil_cols and "anno_brevetto" in pil_cols, pil_cols
pil_pk = [c for c,pk,_ in tf["PILOTA"]["cols"] if pk]
assert pil_pk == ["matricola"], pil_pk  # niente FK sintetica, la pk e' quella ereditata pari pari

# --- 1:1 -> FK va sul lato con partecipazione TOTALE (min=1): regola "a chi va la chiave"
# per il caso 1:1, spesso fonte di errore. Es: PERSONA(1,1)--CARTA_IDENTITA(0,1):
# ogni persona ha esattamente una carta, non ogni carta ha per forza una persona assegnata
# -> la FK verso CARTA_IDENTITA sta su PERSONA (il lato obbligatorio), non viceversa.
spec4 = {
  "entita": {
    "PERSONA": {"attr": ["cf","nome"], "id": [["cf"]]},
    "CARTA_IDENTITA": {"attr": ["numero"], "id": [["numero"]]},
  },
  "relazioni": {
    "HA_CARTA": {"tra": ["PERSONA","CARTA_IDENTITA"],
                 "card": {"PERSONA": [1,1], "CARTA_IDENTITA": [0,1]}, "attr": []},
  }
}
t4 = {x["name"]: x for x in er.translate(spec4)}
assert any(ref == "CARTA_IDENTITA" for _, ref in t4["PERSONA"]["fk"]), t4["PERSONA"]["fk"]
assert not t4["CARTA_IDENTITA"]["fk"], "il lato non-totale non deve ospitare la FK"
# simmetrico: se e' CARTA_IDENTITA ad avere min=1, la FK si sposta di conseguenza
spec4b = {
  "entita": {
    "PERSONA": {"attr": ["cf","nome"], "id": [["cf"]]},
    "CARTA_IDENTITA": {"attr": ["numero"], "id": [["numero"]]},
  },
  "relazioni": {
    "HA_CARTA": {"tra": ["PERSONA","CARTA_IDENTITA"],
                 "card": {"PERSONA": [0,1], "CARTA_IDENTITA": [1,1]}, "attr": []},
  }
}
t4b = {x["name"]: x for x in er.translate(spec4b)}
assert any(ref == "PERSONA" for _, ref in t4b["CARTA_IDENTITA"]["fk"]), t4b["CARTA_IDENTITA"]["fk"]
assert not t4b["PERSONA"]["fk"]

# --- relazione TERNARIA con un lato max=1 -> ASSORBITA in quell'entita', NON tabella
# propria. Bug reale trovato: prima creavo sempre tabella per n-arie a prescindere dalla
# cardinalita'. Fonte: Agente_A_Algebra_2.md (26/02/2014) - ternaria A-B-E con E:(0,1) ->
# E(e2,e1,a1*,a2*,b1*,k1*), NESSUNA tabella R.
isa5 = {
  "entita": {
    "A": {"attr": ["a1","a2"], "id": [["a1"]]},
    "B": {"attr": ["b1","b2","b3"], "id": [["b1"]]},
    "E": {"attr": ["e1","e2"], "id": [["e1"]]},
  },
  "relazioni": {
    "R": {"tra": ["A","B","E"], "card": {"A":[0,"N"], "B":[0,"N"], "E":[0,1]}, "attr": ["k1"]},
  }
}
te = {x["name"]: x for x in er.translate(isa5)}
assert "R" not in te, "ternaria con un lato (0,1) deve assorbire, non fare tabella"
e_cols = [c for c,_,_ in te["E"]["cols"]]
assert "a_a1" in e_cols and "b_b1" in e_cols and "k1" in e_cols, e_cols
e_nul = [c for c,_,n in te["E"]["cols"] if n]
assert "k1" in e_nul, "k1 deve essere nullable (E ha min=0 nella relazione)"
k1_count = [c for c,_,_ in te["E"]["cols"]].count("k1")
assert k1_count == 1, f"k1 duplicato: appare {k1_count} volte"

# --- REGOLA SOTTOLINEATURA/ASTERISCO su TUTTI i casi in un colpo solo (richiesto
# esplicitamente): sottolineato (pk=True) SOLO quando la FK identifica la riga
# (identificazione esterna, ISA-figli, tabella N:N/n-aria); asterisco (nullable) sempre e
# solo quando min=0 sul lato che ospita la FK.
spec_rules = {
  "entita": {
    "UNO":  {"attr": ["u"], "id": [["u"]]},
    "MOLTI": {"attr": ["m"], "id": [["m"]]},
    "DEBOLE": {"attr": ["d"], "id": [["d","IDENT"]]},
    "PADRE": {"attr": ["p"], "id": [["p"]]},
    "FIGLIO": {"attr": []},
    "X": {"attr": ["x"], "id": [["x"]]},
    "Y": {"attr": ["y"], "id": [["y"]]},
  },
  "relazioni": {
    "R1N":  {"tra": ["UNO","MOLTI"], "card": {"UNO":[0,"N"], "MOLTI":[1,1]}, "attr": []},
    "IDENT": {"tra": ["DEBOLE","UNO"], "card": {"DEBOLE":[1,1], "UNO":[0,"N"]}, "attr": []},
    "XY": {"tra": ["X","Y"], "card": {"X":[0,"N"], "Y":[0,"N"]}, "attr": []},
  },
  "isa": [{"padre":"PADRE","figli":["FIGLIO"],"strategia":"figli"}]
}
tr = {t["name"]: t for t in er.translate(spec_rules)}
# 1:N: FK su MOLTI (lato max=1), NON sottolineata, NOT NULL (MOLTI ha min=1 nella relazione)
molti_fk = [(n,pk,nul) for n,pk,nul in tr["MOLTI"]["cols"] if "uno" in n]
assert molti_fk == [("uno_u", False, False)], molti_fk
# identificazione esterna: FK su DEBOLE, sottolineata (fa parte della chiave)
debole_pk = [n for n,pk,_ in tr["DEBOLE"]["cols"] if pk]
assert "uno_u" in debole_pk, debole_pk
# ISA figli: chiave ereditata sottolineata
figlio_pk = [n for n,pk,_ in tr["FIGLIO"]["cols"] if pk]
assert "padre_p" in figlio_pk, figlio_pk
# N:N: tutte le FK della tabella-relazione sottolineate
xy_pk = [n for n,pk,_ in tr["XY"]["cols"] if pk]
assert set(xy_pk) == {"x_x","y_y"}, xy_pk

print("TUTTI I TEST OK")
