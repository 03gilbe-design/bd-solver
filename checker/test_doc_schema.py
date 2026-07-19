"""Test doc_schema.py sul caso reale dell'esame 16/07 (TIPO_visita/VISITA/GRUPPO/TURISTA).
Struttura dal diagramma fotografato:
  TIPO_visita (0,N) --tipologia-- (1,1) VISITA_per_gruppi
  VISITA (0,N) --divisione-- (1,1) GRUPPO
  GRUPPO (1,N) --assegnazione-- (0,N) TURISTA
Radici marcate nel diagramma: VISITA (DOCvis) e TURISTA (DOCtur).
Atteso: GRUPPO annidato (lista) in VISITA; TIPO_visita NON annidabile in VISITA
(TIPO ha (0,N): un tipo serve molte visite -> riferimento); TURISTA riferito da GRUPPO."""
import doc_schema as ds

spec = {
  "entita": {
    "TIPO_VISITA": {"attr": ["nome","lingua"], "id": [["nome"]]},
    "VISITA": {"attr": ["codice","data","durata"], "id": [["codice"]]},
    "GRUPPO": {"attr": ["lettera","ora_inizio","ora_fine","accompagnatore"], "id": [["lettera"]]},
    "TURISTA": {"attr": ["cod_tur","nome","cognome","nazionalita"], "id": [["cod_tur"]]},
  },
  "relazioni": {
    "TIPOLOGIA": {"tra": ["VISITA","TIPO_VISITA"], "card": {"VISITA":[1,1], "TIPO_VISITA":[0,"N"]}, "attr": []},
    "DIVISIONE": {"tra": ["GRUPPO","VISITA"], "card": {"GRUPPO":[1,1], "VISITA":[0,"N"]}, "attr": []},
    "ASSEGNAZIONE": {"tra": ["TURISTA","GRUPPO"], "card": {"TURISTA":[0,"N"], "GRUPPO":[1,"N"]}, "attr": []},
  }
}
docs = ds.build(spec, roots=["VISITA", "TURISTA"])

v = docs["VISITA"]
# GRUPPO: max=1 verso VISITA -> annidato, come lista (VISITA ne ha 0,N)
assert "GRUPPO" in v["annidati"], v
assert v["annidati"]["GRUPPO"]["_lista"] is True
# TIPO_VISITA: (0,N) -> NON annidabile, riferimento
assert "TIPO_VISITA" in v["riferimenti"], v
# dentro GRUPPO: TURISTA e' radice -> riferimento, mai annidato
g = v["annidati"]["GRUPPO"]
assert "TURISTA" in g["riferimenti"], g
assert not g["annidati"], g

t = docs["TURISTA"]
# TURISTA: GRUPPO ha max=N verso TURISTA? GRUPPO partecipa (1,N) -> riferimento
assert "GRUPPO" in t["riferimenti"], t

out = ds.render_text(docs)
assert "DOC_VISITA" in out and "DOC_TURISTA" in out
assert "rif:" in out

# --- etichette con la notazione UFFICIALE (slide 27b_ER_MongoDB_Embedding.pdf):
# GRUPPO: (1,1) verso VISITA (padre ne ha 0,N = molti) -> array sicuro = XRL
# TIPO_VISITA visto da VISITA: TIPO (0,N) = lato molti del figlio -> N:M-like... no:
#   la relazione TIPOLOGIA e' VISITA(1,1)-TIPO(0,N): il "figlio" TIPO ha card (0,N) -> X_R
lab = ds.labels(spec, roots=["VISITA", "TURISTA"])
assert lab.get("GRUPPO") == "XRL", lab
assert lab.get("TIPO_VISITA") == "X_R", lab
print("TUTTI I TEST OK")
