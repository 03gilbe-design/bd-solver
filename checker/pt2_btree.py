#!/usr/bin/env python3
"""pt2_btree.py — esercizio B+-tree della III prova (parte 2). Deterministico, stdlib puro.

FONTE VERIFICATA: 20_esR_b+tree.pdf (esercizio ufficiale) + Lezione_04_Strutture_Fisiche_
BTree_Hash.pdf (teoria ufficiale, vincoli di riempimento):
- fan-out f: max #puntatori = f, max #chiavi foglia = f-1;
  minimi = ceil(f/2) puntatori, ceil((f-1)/2) chiavi (root esente dal minimo)
  ATTENZIONE: ceil((f-1)/2) NON coincide con ceil(f/2)-1 per f pari (es. f=4: 2 vs 1) —
  bug reale trovato il 2026-07-19 confrontando col PDF di teoria, prima testato solo con
  fan-out dispari (5) dove le due formule coincidono per caso.
- chiavi nodo intermedio = "minimo valore del sotto-albero di destra"
- INSERT con overflow -> SPLIT senza guardare i fratelli:
  foglia: primi min_keys valori nel primo nodo, il resto nel secondo;
  intermedio: primi min_ptr puntatori nel primo, il resto nel secondo
- DELETE con underflow -> MERGE col fratello di SINISTRA (il primo figlio usa il destro);
  se il totale sta in un nodo -> vero merge, altrimenti redistribuzione;
  la propagazione puo' far scendere l'altezza (root con 1 figlio -> il figlio e' la nuova root)

FIX 2026-07-19 (da Esercitazione_2015-soluzioni.pdf): per un nodo IN MEZZO (non
primo ne' ultimo figlio) in underflow, la scelta del fratello sinistro vs destro
non e' arbitraria — il prof preferisce il lato che produce un VERO MERGE (non
una redistribuzione), quando solo un lato lo permette. Esempio ufficiale:
root(L,T), foglie (B,E,G)(L,N)(T,Z), fan-out 4, delete L -> foglia (N) sotto
minimo; fondere a sinistra darebbe (B,E,G,N)=4 chiavi>max (redistribuzione),
fondere a destra da' (N,T,Z)=3 chiavi<=max (vero merge) -> il prof sceglie
destra. Implementato in _merge: prova il lato che da' vero merge; se nessuno
dei due o entrambi, default sinistra (comportamento invariato per i casi limite
gia' verificati: primo/ultimo figlio restano come da 20_esR/Esercitazione_2016).

Rappresentazione: foglia = lista ordinata di chiavi; nodo interno = {"ch": [figli]}.
Le chiavi dei nodi interni si ricalcolano sempre da zero (regola del minimo a destra),
come nell'esercizio ufficiale ("i valori chiave sono stati ricalcolati")."""
import math

def _mins(f):
    min_ptr = math.ceil(f / 2)
    min_keys = math.ceil((f - 1) / 2)
    return min_ptr, min_keys   # (min puntatori interni, min chiavi foglia)

def is_leaf(n):
    return isinstance(n, list)

def leftmost(n):
    while not is_leaf(n):
        n = n["ch"][0]
    return n[0]

def keys_of(n):
    """chiavi di un nodo interno: min del sotto-albero destro per ogni figlio dopo il primo"""
    return [leftmost(c) for c in n["ch"][1:]]

def build(leaves, f):
    """costruzione bottom-up dai nodi foglia dati (come il punto 1 dell'esercizio ufficiale)"""
    level = [sorted(l) for l in leaves]
    while len(level) > 1:
        n = len(level)
        k = math.ceil(n / f)                      # numero minimo di nodi al livello sopra
        base, extra = divmod(n, k)
        nxt, i = [], 0
        for j in range(k):
            size = base + (1 if j < extra else 0)
            nxt.append({"ch": level[i:i + size]})
            i += size
        level = nxt
    return level[0]

def insert(root, key, f):
    min_ptr, min_keys = _mins(f)

    def _ins(n):
        """ritorna None oppure il nuovo nodo destro creato dallo split"""
        if is_leaf(n):
            n.append(key); n.sort()
            if len(n) <= f - 1:
                return None
            right = n[min_keys:]          # "primi 2 valori nel primo nodo e i rimanenti nel secondo"
            del n[min_keys:]
            return right
        ks = keys_of(n)
        idx = 0
        while idx < len(ks) and key >= ks[idx]:
            idx += 1
        new = _ins(n["ch"][idx])
        if new is None:
            return None
        n["ch"].insert(idx + 1, new)
        if len(n["ch"]) <= f:
            return None
        right = {"ch": n["ch"][min_ptr:]}  # split intermedio: primi min_ptr, il resto
        del n["ch"][min_ptr:]
        return right

    new = _ins(root)
    if new is not None:
        root = {"ch": [root, new]}         # nuova root: minimo non richiesto
    return root

def delete(root, key, f):
    min_ptr, min_keys = _mins(f)

    def _would_merge(a_node, b_node):
        """True se unire a_node+b_node darebbe un vero merge (non redistribuzione)"""
        if is_leaf(a_node):
            return len(a_node) + len(b_node) <= f - 1
        return len(a_node["ch"]) + len(b_node["ch"]) <= f

    def _merge(children, i):
        """fonde/redistribuisce il figlio i col fratello sinistro o destro.
        Preferenza: se un solo lato produce un vero merge (non redistribuzione)
        si sceglie quello (coerente con l'esempio ufficiale Esercitazione_2015,
        dove per un nodo di mezzo si sceglie il lato che permette il merge vero);
        altrimenti si sceglie sinistra di default (o destra se i==0, primo figlio)."""
        left_ok = i > 0 and _would_merge(children[i - 1], children[i])
        right_ok = i < len(children) - 1 and _would_merge(children[i], children[i + 1])
        if i == 0:
            j = i + 1
        elif i == len(children) - 1:
            j = i - 1
        elif right_ok and not left_ok:
            j = i + 1
        else:
            j = i - 1
        a, b = (j, i) if j < i else (i, j)
        left, right = children[a], children[b]
        if is_leaf(left):
            allk = left + right
            if len(allk) <= f - 1:                       # vero merge
                children[a:b + 1] = [allk]
            else:                                        # redistribuzione
                children[a] = allk[:len(allk) // 2]
                children[b] = allk[len(allk) // 2:]
        else:
            allc = left["ch"] + right["ch"]
            if len(allc) <= f:
                children[a:b + 1] = [{"ch": allc}]
            else:
                children[a] = {"ch": allc[:len(allc) // 2]}
                children[b] = {"ch": allc[len(allc) // 2:]}

    def _del(n):
        """ritorna True se n e' in underflow"""
        if is_leaf(n):
            n.remove(key)
            return len(n) < min_keys
        ks = keys_of(n)
        idx = 0
        while idx < len(ks) and key >= ks[idx]:
            idx += 1
        if _del(n["ch"][idx]):
            _merge(n["ch"], idx)
        return len(n["ch"]) < min_ptr

    _del(root)
    if not is_leaf(root) and len(root["ch"]) == 1:
        root = root["ch"][0]
    return root

def levels(root):
    """[[chiavi nodo, ...] per livello] — per confronto e stampa"""
    out, cur = [], [root]
    while cur:
        out.append([n if is_leaf(n) else keys_of(n) for n in cur])
        cur = [c for n in cur if not is_leaf(n) for c in n["ch"]]
        cur = [c for c in cur]
    return out

def render_text(root):
    return "\n".join("livello %d: %s" % (i, "  ".join("(" + ",".join(str(k) for k in ks) + ")" for ks in lv))
                     for i, lv in enumerate(levels(root)))
