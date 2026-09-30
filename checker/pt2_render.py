#!/usr/bin/env python3
"""pt2_render.py — genera blocchi LaTeX per ciascun tipo di esercizio parte 2,
a partire dai motori deterministici pt2_*. Usato da solve_pt2.py (spec generico,
come render.py/solve.py fanno per parte 1).

Ogni funzione render_X(ex) prende un dict esercizio dello spec JSON e ritorna
una stringa LaTeX (titolo + contenuto + spiegazioni + eventuale disegno TikZ)."""
import math, re
import pt2_ripresa, pt2_schedule, pt2_costo, pt2_btree

def esc(s):
    """Scappa i caratteri speciali di LaTeX in testo libero (query SQL,
    risposte di teoria). Mancava quasi tutto tranne _ { } - con '%' non
    scappato (carattere di commento LaTeX) una query tipo LIKE 'A%' perdeva
    silenziosamente tutto cio' che veniva dopo sulla stessa riga: bug reale,
    trovato in un PDF generato (query c con NOT EXISTS, 'A%' troncata dopo
    la 'A'). Il backslash va scappato PER PRIMO, altrimenti raddoppia i
    backslash aggiunti dagli escape successivi."""
    s = str(s)
    # le parti $...$ (es. $\bowtie$, B$^+$) sono LaTeX voluto: passano intatte.
    # Bug reale 30/09: "COLLEGIO $\bowtie$ VOTO" stampato letterale nel PDF.
    if re.search(r"\$[^$]+\$", s):
        return "".join(p if i % 2 else esc(p) for i, p in enumerate(re.split(r"(\$[^$]+\$)", s)))
    s = s.replace("\\", "\\textbackslash{}")
    s = s.replace("&", "\\&").replace("%", "\\%").replace("$", "\\$")
    s = s.replace("#", "\\#").replace("_", "\\_")
    s = s.replace("{", "\\{").replace("}", "\\}")
    s = s.replace("~", "\\textasciitilde{}")
    s = s.replace("^", "\\textasciicircum{}")
    s = s.replace("<", "\\textless{}").replace(">", "\\textgreater{}")
    return s

SOL = "%%SOLUZIONE%%\n"   # separa testo d'esame e risposta (vedi render_esercizio)

def par(s):
    return esc(s) + "\\par\\smallskip\n"

MINIMAL = False   # --minimal: via le note di spiegazione, restano passi + formule (i passaggi contano per il prof)

def note(s):
    if MINIMAL:
        return ""
    return "{\\footnotesize\\textit{" + s + "}}\\par\\smallskip\n"

COLORI = False   # --colori: dati estratti dall'esame colorati per verificarli a colpo d'occhio

def _log_colorato(log):
    """Log ripresa: B verde, C blu, A rosso, CK arancio grassetto (colori definiti in solve_pt2)."""
    col = {"B": "opB", "C": "opC", "A": "opA", "CK": "opCK"}
    out, pos = [], 0
    for m in re.finditer(r"(CK|B|C|A|U|I|D)\s*\([^)]*\)", log):
        out.append(esc(log[pos:m.start()]))
        t = esc(m.group(0))
        k = m.group(1)
        out.append(("\\textbf{\\textcolor{opCK}{" + t + "}}") if k == "CK" else
                   ("\\textcolor{" + col[k] + "}{" + t + "}") if k in col else t)
        pos = m.end()
    return "".join(out) + esc(log[pos:])

def _schedule_colorato(S):
    """Schedule: ogni operazione col colore della sua transazione (t1..t8)."""
    return re.sub(r"([rw])(\d+)\(([^)]*)\)",
                  lambda m: f"\\textcolor{{t{int(m.group(2)) % 8}}}{{{m.group(0)}}}", esc(S))

def _domanda_evidenziata(q):
    """Domanda di teoria: parole chiave del modello in grassetto, sotto-punti (i)(ii)(iii) colorati."""
    import teoria
    s = esc(q)
    m, _ = teoria.riconosci(q)
    for k in sorted(m["chiavi"] if m else [], key=len, reverse=True):
        s = re.sub("(" + re.escape(esc(k)) + ")", r"\\textbf{\1}", s, flags=re.I)
    return re.sub(r"\((i{1,3}|iv|v)\)", r"\\textbf{\\textcolor{opCK}{(\1)}}", s)

def formula(s):
    """Formula usata = passaggio, resta anche in --minimal."""
    return "{\\raggedright\\footnotesize " + s + "\\par}\\smallskip\n"   # raggedright: la parte $...$ non si spezza

def _titolo(ex):
    """Titolo esercizio nello stile dei testi d'esame del prof:
    'd) (4) Gestore dell'affidabilita'' — id, punti tra parentesi, nome sottolineato."""
    pid = ex.get("id", "")
    pt = f"({ex['punti']}) " if ex.get("punti") else ""
    return ("\\bigskip\\par\\noindent\\textbf{" + esc(pid) + ") " + pt +
            "\\underline{" + esc(ex.get("titolo", "")) + "}}\\par\\nopagebreak\\medskip\n")


def render_ripresa(ex):
    L = [_titolo(ex)]
    log = ex["log"]
    # raggedright: il texttt non si allarga/stringe -> senza, righe lunghe del log sforavano il margine (30/09)
    L.append("{\\raggedright\\footnotesize\\texttt{" + (_log_colorato(log) if COLORI else esc(log)) + " guasto}\\par}\\medskip\n")
    L.append(SOL)
    r = pt2_ripresa.ripresa(log)
    notes = [
        "Si cerca l'ultimo CK nel log: le transazioni elencate al suo interno sono quelle attive in quel momento.",
        "Per definizione, appena dopo il CK tutte le transazioni attive vanno in UNDO; REDO parte vuoto.",
        "Si scorre il log dal CK in poi: un C(T) sposta T da UNDO a REDO; un B(T) nuovo aggiunge T a UNDO. Un A(T) NON sposta T: resta in UNDO.",
        "Le operazioni delle transazioni in UNDO si annullano scorrendo il log ALL'INDIETRO: U ripristina Before, I diventa cancellazione, D diventa inserimento.",
        "Le operazioni delle transazioni in REDO si rieseguono scorrendo il log IN AVANTI dall'inizio, applicando il valore After.",
    ]
    vuoto = lambda s: par(s.replace("{}", "0/")).replace("0/", "$\\emptyset$")
    for i, (s, n) in enumerate(zip(r["steps"], notes)):
        if i == 2:   # Passo 3 come il prof: UNDO/REDO dopo ogni B/C, poi la situazione finale
            L.append("Passo 3: dal CK in avanti\\par\n")
            L.extend("\\quad " + vuoto(e) for e in r["evoluzione"])
        L.append(vuoto(s))
        L.append(note(n))
    return "".join(L)


QUADRETTI = False   # --quadretti: figure disegnate in quadretti interi (vedi _btree_quadretti)
COLONNE = 36        # larghezza utile della pagina a quadretti: 180 mm / 5 mm
PENNA = "line width=0.75pt"   # tratto un po' piu' spesso, come una penna
CIFRA = "font=\\fontsize{11}{11}\\selectfont"   # carattere che riempie bene un quadretto da 5 mm


def _graph_quadretti(nodes, edges):
    """Grafo dei conflitti sulla griglia: centri sugli INCROCI, cerchi di raggio 1 quadretto,
    bounding box di quadretti interi (cosi' la figura parte e finisce su una linea)."""
    n = len(nodes)
    R = 5 if n <= 4 else 7
    pos = {t: (round(COLONNE / 2 + R * math.cos(2 * math.pi * i / n + math.pi / 2)),
               round(-(R + 1) + R * math.sin(2 * math.pi * i / n + math.pi / 2))) for i, t in enumerate(nodes)}
    fondo = min(y for _, y in pos.values()) - 1
    out = [f"\\figura{{\\begin{{tikzpicture}}[x=5mm,y=5mm,{PENNA},node/.style={{circle,draw,{PENNA},"
           f"minimum size=10mm,inner sep=0pt,{CIFRA}}}]",
           f"\\useasboundingbox (0,0) rectangle ({COLONNE},{fondo});"]
    for t in nodes:
        x, y = pos[t]
        out.append(f"\\node[node] (T{t}) at ({x},{y}) {{T{t}}};")
    for a, b in edges:
        out.append(f"\\draw[-{{Stealth}},{PENNA}] (T{a}) -- (T{b});")
    out.append("\\end{tikzpicture}}")
    return "\n".join(out)


def _btree_quadretti(root, caption):
    """B+-tree scritto sui quadretti come a mano: ogni carattere di una chiave occupa UN quadretto,
    ogni chiave ha la sua cella, bordi e separatori sulle linee della griglia, frecce che partono dai
    confini fra le celle (i puntatori), 2 righe vuote fra i livelli. Ritorna None se non entra nei
    36 quadretti (allora si usa il disegno normale)."""
    chiavi = lambda n: [str(k) for k in (n if pt2_btree.is_leaf(n) else pt2_btree.keys_of(n))]
    # tentativi, dal piu' leggibile: fra le chiavi uno SPAZIO (= 1 quadretto vuoto) oppure una linea;
    # fra le foglie 2 o 1 quadretti; limite 36 colonne (testo) o 40 (entra nei margini, resta
    # sempre 1 quadretto dal bordo del foglio)
    for sep, gap, limite in [(1, 2, COLONNE), (1, 1, COLONNE), (1, 1, COLONNE + 4),
                             (0, 2, COLONNE), (0, 1, COLONNE), (0, 1, COLONNE + 4)]:
        larg = lambda n: sum(len(k) for k in chiavi(n)) + sep * (len(chiavi(n)) - 1)
        nodi, frecce, foglie, cur = [], [], [], [0]

        def piazza(n, d):
            i = len(nodi)
            nodi.append(None)
            if pt2_btree.is_leaf(n):
                nodi[i] = [cur[0], d, n]
                cur[0] += larg(n) + gap
                foglie.append(i)
                return cur[0] - gap - larg(n), cur[0] - gap
            spans = []
            for c in n["ch"]:
                frecce.append((i, len(nodi)))
                spans.append(piazza(c, d + 1))
            centro = (spans[0][0] + spans[-1][1]) / 2
            nodi[i] = [math.floor(centro - larg(n) / 2 + 0.5), d, n]
            return nodi[i][0], nodi[i][0] + larg(n)
        piazza(root, 0)
        for d in {x[1] for x in nodi}:       # stesso livello: mai sovrapposti (almeno 1 quadretto)
            fila = sorted((x for x in nodi if x[1] == d), key=lambda x: x[0])
            for a, b in zip(fila, fila[1:]):
                b[0] = max(b[0], a[0] + larg(a[2]) + 1)
        larghezza = max(x[0] + larg(x[2]) for x in nodi)
        if larghezza <= limite:
            break
    else:
        return None
    off = (COLONNE - larghezza) // 2        # centrato di un numero INTERO di quadretti
    alt = max(x[1] for x in nodi)
    top = lambda d: -3 * d
    out = [f"\\textbf{{{caption}}}\\par",
           f"\\figura{{\\begin{{tikzpicture}}[x=5mm,y=5mm,{PENNA},c/.style={{inner sep=0pt,anchor=center,{CIFRA}}}]",
           f"\\useasboundingbox (0,0) rectangle ({COLONNE},{top(alt) - 1});"]
    confini = {}
    for i, (x, d, n) in enumerate(nodi):
        x += off
        out.append(f"\\draw ({x},{top(d)}) rectangle ({x + larg(n)},{top(d) - 1});")
        b, pos = [x], x
        for k in chiavi(n):
            for j, ch in enumerate(k):
                out.append(f"\\node[c] at ({pos + j + 0.5},{top(d) - 0.5}) {{{esc(ch)}}};")
            pos += len(k)
            if pos < x + larg(n):            # fra due chiavi: centro dello spazio, oppure una linea
                if sep:
                    b.append(pos + 0.5)
                else:
                    b.append(pos)
                    out.append(f"\\draw ({pos},{top(d)}) -- ({pos},{top(d) - 1});")
                pos += sep
        b.append(x + larg(n))
        confini[i] = b                       # k chiavi -> k+1 confini = k+1 puntatori
    for p, c in frecce:
        figli = [cc for pp, cc in frecce if pp == p]
        xp = confini[p][figli.index(c)] if len(confini[p]) == len(figli) else \
            confini[p][0] + larg(nodi[p][2]) * figli.index(c) / max(len(figli) - 1, 1)
        xc = nodi[c][0] + off + larg(nodi[c][2]) / 2
        out.append(f"\\draw[-{{Stealth}}] ({xp},{top(nodi[p][1]) - 1}) -- ({xc},{top(nodi[c][1])});")
    for a, b in zip(foglie, foglie[1:]):     # catena delle foglie, a meta' altezza
        y = top(nodi[a][1]) - 0.5
        out.append(f"\\draw[-{{Stealth[length=1.2mm]}},densely dashed] ({nodi[a][0] + off + larg(nodi[a][2])},{y}) -- "
                   f"({nodi[b][0] + off},{y});")
    out.append("\\end{tikzpicture}}")
    return "\n".join(out)


# --- "quaderno": ogni carattere in un quadretto -------------------------------------------------
# Prende il LaTeX che generiamo noi (insieme chiuso di comandi) e lo riduce a caratteri con stile;
# poi va a capo a parole su righe di COLONNE quadretti. Unicode speciali -> comando LaTeX nel box.
_MATH = {r"\emptyset": "∅", r"\to": "→", r"\Rightarrow": "⇒", r"\subseteq": "⊆", r"\bowtie": "⋈",
         r"\le": "≤", r"\times": "×", r"\lceil": "⌈", r"\rceil": "⌉", r"\cdot": "·"}
_BOX = {"∅": r"$\emptyset$", "→": r"$\to$", "⇒": r"$\Rightarrow$", "⊆": r"$\subseteq$", "⋈": r"$\bowtie$",
        "≤": r"$\le$", "×": r"$\times$", "⌈": r"$\lceil$", "⌉": r"$\rceil$", "·": r"$\cdot$", "⁺": r"$^+$"}
_ACC = {"`e": "è", "'e": "é", "`a": "à", "`o": "ò", "`u": "ù", "`i": "ì", "`E": "È"}
_ESC = {"textbackslash": "\\", "textless": "<", "textgreater": ">", "textasciitilde": "~", "textasciicircum": "^"}
_IGNORA = {"par", "smallskip", "medskip", "bigskip", "nopagebreak", "noindent", "raggedright", "footnotesize",
           "small", "scriptsize", "large", "Large", "centering", "normalsize", "selectfont"}


def _gruppo(s, i):
    """indice dopo il gruppo {...} che inizia in s[i] (graffe bilanciate)."""
    d = 0
    for j in range(i, len(s)):
        d += {"{": 1, "}": -1}.get(s[j], 0)
        if d == 0:
            return j + 1
    return len(s)


def _eventi(s, stile=(), math=False):
    """LaTeX nostro -> lista di ('c', char, stile) | ('par',) | ('fig', raw) | ('sol', on) | ('item',)."""
    ev, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+\*?|.)", s[i:])
            cmd, i = m.group(1), i + len(m.group(0))
            arg = lambda: (s[i + 1:_gruppo(s, i) - 1], _gruppo(s, i)) if i < len(s) and s[i] == "{" else ("", i)
            if cmd == "par" or cmd in ("begin", "end") and s[i:].startswith("{itemize}"):
                ev.append(("par",)); i = _gruppo(s, i) if cmd != "par" else i
            elif cmd in ("begin", "end"):
                nome, i = arg()
                if nome == "soluzione":
                    ev.append(("sol", cmd == "begin"))
                elif nome == "center":
                    ev.append(("par",))
            elif cmd == "item":
                ev.append(("item",))
            elif cmd == "figura":
                raw, i = arg(); ev.append(("fig", raw))
            elif cmd in ("textbf", "textit", "underline", "texttt", "text"):
                x, i = arg(); ev += _eventi(x, stile + (("b",) if cmd == "textbf" else ()), math)
            elif cmd == "textcolor":
                col, i = arg(); x, i = arg(); ev += _eventi(x, stile + (("col", col),), math)
            elif cmd in _ESC:
                ev.append(("c", _ESC[cmd], stile)); i = _gruppo(s, i) if s[i:i + 1] == "{" else i
            elif cmd in ("quad", "hspace*", "hspace"):
                ev.append(("c", " ", stile)); i = _gruppo(s, i) if s[i:i + 1] == "{" else i
            elif cmd in ("`", "'") and i < len(s):
                ev.append(("c", _ACC.get(cmd + s[i], s[i]), stile)); i += 1
            elif "\\" + cmd in _MATH:
                ev.append(("c", _MATH["\\" + cmd], stile))
            elif cmd in _IGNORA or len(cmd) > 1:
                pass
            else:                                  # \% \_ \{ \} \& \# \$
                ev.append(("c", cmd, stile))
        elif c == "$":
            j = s.index("$", i + 1)
            ev += _eventi(s[i + 1:j], stile, True); i = j + 1
        elif c in "{}":
            i += 1
        elif math and c in "^_":
            i += 1
            if c == "^" and s[i:i + 1] in ("+", "{"):
                ev.append(("c", "⁺", stile)); i = _gruppo(s, i) if s[i] == "{" else i + 1
        elif c == "%" and s[i:].startswith("%%SOLUZIONE%%"):
            i += len("%%SOLUZIONE%%")
        elif c in "\n~" or c.isspace():
            ev.append(("c", " ", stile)); i += 1
        else:
            ev.append(("c", c, stile)); i += 1
    return ev


def _cella(ch, stile, sol):
    if sol:
        ch = ch.upper()          # soluzione scritta "a mano" in stampatello maiuscolo, come i suoi appunti
    t = _BOX.get(ch) or (esc(ch) if ch != " " else "")
    if ("b",) in stile:
        t = "\\textbf{" + t + "}"
    col = next((x[1] for x in stile if x[0] == "col"), "sol" if sol else None)
    return ("\\qs{" if _mezzo(ch) else "\\q{") + ("\\textcolor{" + col + "}{" + t + "}" if col and t else t) + "}"


def _mezzo(ch):
    """Caratteri stretti = mezzo quadretto (richiesta jeans): I, 1, punteggiatura, parentesi, spazio."""
    return ch.upper() in "I1.,:;'!|()"   # lo SPAZIO no: fra parole un quadretto intero, deve vedersi


def quaderno(frag, colonne=None):
    """Frammento LaTeX -> righe di quadretti: 1 carattere = 1 quadretto, a capo a parole,
    soluzione rientrata di 1 quadretto, elenchi di 2, UNA riga vuota fra un paragrafo e l'altro."""
    W = 2 * (colonne or COLONNE)             # in MEZZI quadretti: I, 1, punteggiatura e spazio = 1, il resto = 2
    def piano(cs):
        """(larghezza in mezzi quadretti, celle). Le lettere intere partono SEMPRE su una linea della
        griglia: un carattere stretto da solo prima di una lettera occupa il quadretto intero (centrato,
        niente buco "TRANSAZI ONE"); due stretti di fila (es. "I," ").") stanno in un quadretto;
        se serve, mezzo quadretto vuoto per tornare in carreggiata."""
        pos, s = 0, []
        for k, c in enumerate(cs):
            stretto = _mezzo(c[0])
            dopo = cs[k + 1][0] if k + 1 < len(cs) else " "
            if stretto and pos % 2 == 0 and not _mezzo(dopo):
                stretto = False                   # da solo: quadretto intero, centrato
            if not stretto and pos % 2:
                s.append("\\qs{}"); pos += 1
            s.append(_cella(*c).replace("\\qs{", "\\q{", 1) if not stretto else _cella(*c))
            pos += 1 if stretto else 2
        return pos, "".join(s)
    u = lambda cs: piano(cs)[0]
    celle = lambda cs: piano(cs)[1]
    out, riga, parola, sol, rientro = [], [], [], False, 0

    def chiudi_parola():
        nonlocal riga, parola
        while parola:
            spazio = [(" ", (), sol)] if riga else []
            if u(riga + spazio + parola) <= W - 2 * rientro:
                riga += spazio + parola; parola = []
            elif not riga and u(parola) > W - 2 * rientro:   # parola piu' lunga della riga: la spezzo
                n = next(i for i in range(len(parola), 0, -1) if u(parola[:i]) <= W - 2 * rientro)
                riga, parola = parola[:n], parola[n:]; chiudi_riga()
            else:
                chiudi_riga()

    def chiudi_riga():
        nonlocal riga
        if riga:
            out.append("\\qline{" + "\\q{}" * rientro + celle(riga) + "}")
            out.append("\\qline{}")          # lettere alte quanto il quadretto: riga vuota dopo OGNI riga scritta
        riga = []

    def paragrafo():
        chiudi_parola(); chiudi_riga()
        if out and out[-1] != "\\qline{}":
            out.append("\\qline{}")                      # una riga vuota fra le frasi

    ev, prof = _eventi(frag), 0
    for k, e in enumerate(ev):
        if e[0] == "c":
            prof += (e[1] in "({") - (e[1] in ")}")
            succ = next((x[1] for x in ev[k + 1:] if x[0] == "c" and x[1] != " "), "")
            if e[1] == " " and (succ in ",;)}" or prof > 0 and parola[-1:] and parola[-1][0] == ","):
                continue                     # come a mano: "{T1,T2,T3}", niente " ," (quadretti risparmiati)
            if e[1] == " ":
                chiudi_parola()
            else:
                parola.append((e[1], e[2], sol))
        elif e[0] == "par":
            paragrafo()
        elif e[0] == "sol":
            paragrafo(); sol = e[1]; rientro = 1 if sol else 0
            if sol:
                out.append("\\qline{}")          # riga vuota anche fra la domanda e SOLUZIONE
                out.append("\\qline{" + "\\q{}" + "".join(_cella(ch, (("b",),), True) for ch in "SOLUZIONE") + "}")
                out.append("\\qline{}")
        elif e[0] == "item":
            paragrafo(); rientro = (1 if sol else 0); parola = [("-", (), sol)]; chiudi_parola()
            rientro += 1
        elif e[0] == "fig":
            paragrafo(); out.append("\\figura{" + e[1] + "}"); out.append("\\qline{}")
    paragrafo()
    return "\n".join(out) + "\n"


def _graph_tikz(nodes, edges):
    if QUADRETTI:
        return _graph_quadretti(nodes, edges)
    R = 3.2
    n = len(nodes)
    pos = {t: (R * math.cos(2 * math.pi * i / n + math.pi / 2),
               R * math.sin(2 * math.pi * i / n + math.pi / 2)) for i, t in enumerate(nodes)}
    out = ["\\figura{\\begin{tikzpicture}[node/.style={circle,draw,minimum size=8mm,font=\\small}]"]
    for t in nodes:
        x, y = pos[t]
        out.append(f"\\node[node] (T{t}) at ({x:.2f},{y:.2f}) {{$T_{{{t}}}$}};")
    for a, b in edges:
        out.append(f"\\draw[-{{Stealth}},thick] (T{a}) -- (T{b});")
    out.append("\\end{tikzpicture}}")
    return "\n".join(out)


def render_schedule(ex):
    L = [_titolo(ex)]
    S = ex["schedule"]
    L.append("{\\raggedright\\texttt{S: " + (_schedule_colorato(S) if COLORI else esc(S)) + "}\\par}\\medskip\n")
    L.append(SOL)
    ops = pt2_schedule.parse(S)
    # come prof (2015/2016) e studente (es4): ogni transazione scomposta, poi i conflitti
    for t, tops_ in sorted(pt2_schedule.transactions(ops).items()):
        L.append(f"T{t} = " + ", ".join(pt2_schedule.fmt_op(op) for op in tops_) + "\\par\n")
    L.append("\\smallskip\n")
    conf = pt2_schedule.conflicts(ops)
    fmt = lambda op: f"{op[0]}{op[1]}({op[2]})"
    L.append("\\textbf{Conflitti:} " + ", ".join(f"({fmt(a)},{fmt(b)})" for a, b in conf) + "\\par\\smallskip\n")
    L.append(note("Due azioni sono in conflitto se sono di transazioni diverse, agiscono sullo stesso oggetto, e almeno una è una scrittura."))
    edges = sorted(pt2_schedule.conflict_graph(ops))
    nodes = sorted(set(t for _, t, _ in ops))
    L.append("\\textbf{Grafo dei conflitti:}\\par\n")
    L.append(_graph_tikz(nodes, edges))
    L.append(note("CSR sse il grafo dei conflitti non ha cicli: un ordinamento topologico dà uno schedule seriale equivalente."))
    # CSR giustificato come il prof: "Poiche' il grafo non e' ACICLICO lo schedule non e' CSR"
    cyc = pt2_schedule.ciclo(ops)
    T = lambda ts: ",".join(f"T{t}" for t in ts)
    if cyc:
        L.append("\\textbf{CSR:} poich\\'e il grafo ha un ciclo (" + " $\\to$ ".join(f"T{t}" for t in cyc) +
                 "), S \\textbf{non \\`e CSR}.\\par\\smallskip\n")
    else:
        top = pt2_schedule.topological_orders(ops)[0]
        L.append("\\textbf{CSR:} poich\\'e il grafo \\`e aciclico, S \\textbf{\\`e CSR} "
                 f"(seriale equivalente: {T(top)}).\\par\\smallskip\n")
    # VSR giustificato: LeggeDa + ScrittureFinali -> vincoli -> seriale (o nessuno)
    if True:   # VSR sempre giustificato con LeggeDa + ScrittureFinali (esami dal 2022: "giustificare")
        rf =sorted(pt2_schedule.reads_from(ops), key=lambda p: ops.index(p[0]) if p[0] in ops else 0)
        fr = lambda p: f"({pt2_schedule.fmt_op(p[0])}, " + ("iniziale" if p[1][1] == 0 else pt2_schedule.fmt_op(p[1])) + ")"
        fw = sorted(pt2_schedule.final_writes(ops), key=lambda w: w[2])
        L.append("\\textbf{VSR:} LeggeDa(S) = \\{" + ", ".join(fr(p) for p in rf) + "\\}\\par\n")
        L.append("ScrittureFinali(S) = \\{" + ", ".join(pt2_schedule.fmt_op(w) for w in fw) + "\\}\\par\n")
        vinc = pt2_schedule.vincoli_view(ops)
        L.append("$\\Rightarrow$ vincoli: " + ", ".join(f"T{a} $<$ T{b}" for a, b in vinc) + "\\par\n")
        ser = pt2_schedule.seriale_view(ops)
        if ser:
            L.append(f"S \\`e view-equivalente al seriale {T(ser)}: S \\textbf{{\\`e VSR}}" +
                     (" (coerente con CSR $\\subseteq$ VSR)" if not cyc else "") + ".\\par\\smallskip\n")
        else:
            opp = next(((a, b) for a, b in vinc if (b, a) in vinc), None)
            perche = (f"T{opp[0]} $<$ T{opp[1]} e T{opp[1]} $<$ T{opp[0]} si contraddicono"
                      if opp else "nessun ordine seriale rispetta tutti i vincoli")
            L.append(perche + ": S \\textbf{non \\`e VSR} (nonSR).\\par\\smallskip\n")
    motivo = pt2_schedule.perche_non_2pl(ops)
    if motivo is None:   # testimone: lock/unlock a due fasi compatibili con S (lock anche anticipati)
        lp = pt2_schedule.lock_2pl(ops)
        L.append("\\textbf{2PL:} s\\`i: esiste un'assegnazione di lock a due fasi compatibile con S "
                 "(ogni transazione acquisisce tutti i suoi lock, se serve in anticipo, prima di rilasciarne "
                 "uno; sl = lock condiviso, xl = esclusivo, u = rilascio):\\par\n"
                 "{\\raggedright\\small\\texttt{" + esc(pt2_schedule.sequenza_lock(ops, lp)) + "}\\par}\n")
        L.append(note("Le azioni restano nello stesso ordine; nessun lock esclusivo coesiste con un altro lock "
                      "sullo stesso oggetto."))
        if not pt2_schedule.is_2pl_primo_uso(ops):   # le due letture della slide differiscono: le mostro entrambe
            L.append(par("Nota: questo vale ammettendo lock acquisiti in anticipo (slide: conta solo che "
                         "dopo un rilascio non si acquisiscano altri lock). Se invece ogni lock si prende solo "
                         "alla prima azione sull'oggetto, S NON sarebbe 2PL: una transazione dovrebbe "
                         "acquisire un lock dopo averne gia' ceduto uno."))
    else:
        L.append("\\textbf{2PL:} no: " + esc(motivo) + ".\\par\n")
    cls = pt2_schedule.classify(S)
    L.append(f"\\textbf{{Esito: S \\`e {cls}}}.\\par\n")
    return "".join(L)


def render_costo(ex):
    L = [_titolo(ex)]
    p = ex["parametri"]
    rc = pt2_costo.solve(**p)
    if "descrizione" in ex:
        L.append(par(ex["descrizione"]))
    L.append(SOL)
    # nomi veri delle tabelle come il prof (NP(MEDICO), non "NP esterna"): da "X $\bowtie$ Y"
    m = re.search(r"(\w+)\s*\$\\bowtie\$\s*(\w+)", ex.get("descrizione", ""))
    est, inn = (m.group(1), m.group(2)) if m else ("esterna", "interna")
    nomi = lambda s: (s.replace("NR_sel_esterna", f"NR({est} sel)").replace("NP_sel_interna", f"NP({inn} sel)")
                       .replace("interna", inn).replace("esterna", est).replace(" = NP = ", " = NP = "))
    sel_inn = p.get("interna_selezionata", True)
    termini = ([f"NP({inn})", f"scrittura selezione {inn}"] if sel_inn else []) + [f"NP({est})"]
    if p.get("outer_pagine_scritte"):
        termini += [f"scrittura selezione {est}", f"rilettura selezione {est} nel JOIN"]
    np_inn = f"NP({inn}_{{sel}})" if sel_inn else f"NP({inn})"
    L.append(formula(f"Formula NLJ ({est} esterna, {inn} interna): costo = " + " + ".join(termini) +
                     f" + $NR({est}_{{sel}}) \\times {np_inn}$."))
    for s in rc["steps"]:
        if s.startswith("(d)"):   # come il prof: da dove viene NR selezionato (es. 1200/25)
            nr, val = p["nr_outer"], p["val_sel_outer"]
            if p.get("selezione_diverso"):   # WHERE A <> v: complemento dell'uguaglianza
                L.append(par(f"NR({est} sel) = NR({est}) - NR({est}) / VAL = {nr} - {nr} / {val} = "
                             f"{nr} - {pt2_costo.nr_sel(nr, val):g} = {rc['nr_sel_esterna']:g} (selezione con <>)"))
            else:
                L.append(par(f"NR({est} sel) = NR({est}) / VAL = {nr} / {val} = {rc['nr_sel_esterna']:g}"))
        L.append(par(nomi(s)))

    def somma(steps, tot):
        """'totale = (a)+(b)+(c)+(d) = 750+150+150+11250 = 12.300' come il prof."""
        voci = [(re.match(r"\(([a-e](?:-bis)?)\)", s).group(1), s.rsplit("=", 1)[1].strip())
                for s in steps if re.match(r"\([a-e]", s)]
        return ("totale = " + "+".join(f"({k})" for k, _ in voci) + " = " + "+".join(v for _, v in voci) +
                " = " + f"{tot:,}".replace(",", "."))
    L.append("\\textbf{" + esc(somma(rc["steps"], rc["totale"])) + " accessi" +
             (" (punto 1)" if "steps_indice" in rc else "") + "}\\par\\medskip\n")
    if "steps_indice" in rc:
        d = p.get("prof_indice")
        L.append(formula(f"Con indice B$^+$-tree di profondit\\`a {d} su {inn}: $NP({inn}_{{sel}})$ diventa "
                         f"$d+\\lceil NR({inn}_{{sel}})/VAL(\\text{{join}},{inn})\\rceil$."))
        L.append(par(nomi(rc["steps_indice"][-1])))
        L.append("\\textbf{" + esc(somma(rc["steps_indice"], rc["totale_indice"])) + " accessi (punto 2)}\\par\n")
    return "".join(L)


def _btree_tikz(root, caption):
    """Disegno come nelle slide del prof: albero a cono (ogni padre CENTRATO sopra
    i suoi figli), frecce padre->figlio, catena di frecce tra foglie consecutive."""
    if QUADRETTI:
        q = _btree_quadretti(root, caption)
        if q:
            return q
        print(f"AVVISO quadretti: albero '{caption}' piu' largo di {COLONNE} quadretti, disegno normale")
    GAP = 0.5          # spazio orizzontale tra nodi foglia
    ROWH = 1.6         # distanza verticale tra livelli

    def width(n):
        keys = n if pt2_btree.is_leaf(n) else pt2_btree.keys_of(n)
        return 0.55 * max(len(keys), 1) + 0.35

    nodes = []          # (id, x_centro, y, testo)
    edges = []          # (id_padre, id_figlio)
    leaf_ids = []
    cursor = [0.0]      # x del prossimo bordo sinistro di foglia

    def place(n, depth):
        nid = len(nodes)
        nodes.append(None)                        # placeholder, x dopo
        if pt2_btree.is_leaf(n):
            x = cursor[0] + width(n) / 2
            cursor[0] += width(n) + GAP
            leaf_ids.append(nid)
            nodes[nid] = (nid, x, -depth * ROWH, ",".join(str(k) for k in n))
            return x
        child_xs = []
        for c in n["ch"]:
            cid_before = len(nodes)
            child_xs.append(place(c, depth + 1))
            edges.append((nid, cid_before))
        x = (child_xs[0] + child_xs[-1]) / 2      # padre centrato sui figli -> cono
        nodes[nid] = (nid, x, -depth * ROWH,
                       ",".join(str(k) for k in pt2_btree.keys_of(n)))
        return x

    place(root, 0)
    out = [f"\\textbf{{{caption}}}\\par",
           "\\figura{\\begin{tikzpicture}[font=\\footnotesize,",
           "node/.style={draw,minimum height=6mm,inner sep=3pt}]"]
    for nid, x, y, txt in nodes:
        out.append(f"\\node[node] (n{nid}) at ({x:.2f},{y:.2f}) {{{txt}}};")
    for p, c in edges:
        out.append(f"\\draw[-{{Stealth}}] (n{p}.south) -- (n{c}.north);")
    for a, b in zip(leaf_ids, leaf_ids[1:]):      # catena foglie come nel disegno del prof
        out.append(f"\\draw[-{{Stealth}},densely dashed] (n{a}.east) -- (n{b}.west);")
    out.append("\\end{tikzpicture}}")
    return "\n".join(out)


def render_btree(ex):
    L = [_titolo(ex)]
    f = ex["fanout"]
    min_ptr, min_keys = pt2_btree._mins(f)   # stessa fonte del motore (fix fan-out pari, luglio)
    # vincoli scritti come il prof: "2 <= chiavi <= 4, 3 <= puntatori <= 5"
    L.append(formula(f"Vincoli (fan-out {f}): ${min_keys} \\le$ \\#chiavi foglia $\\le {f-1}$, "
                     f"${min_ptr} \\le$ \\#puntatori nodo interno $\\le {f}$ (radice esente dal minimo)."))
    L.append(note("Le chiavi dei nodi interni sono il minimo valore del sotto-albero a destra."))
    t = pt2_btree.build(ex["foglie"], f)
    L.append(_btree_tikz(t, "a) costruzione"))

    def stat(n):   # (n. foglie, altezza, n. nodi interni)
        if pt2_btree.is_leaf(n):
            return 1, 0, 0
        s = [stat(c) for c in n["ch"]]
        return sum(x[0] for x in s), 1 + max(x[1] for x in s), 1 + sum(x[2] for x in s)

    for i, op in enumerate(ex.get("operazioni", [])):
        letter = chr(ord("b") + i)
        f0, h0, n0 = stat(t)
        k = op["key"]
        if op["op"] == "insert":
            t = pt2_btree.insert(t, k, f)
            f1, h1, n1 = stat(t)
            if f1 == f0:
                cosa = f"{k} entra nella foglia senza superare {f-1} chiavi: nessuno split."
            else:
                cosa = f"la foglia supera {f-1} chiavi: SPLIT (senza guardare i fratelli)"
                cosa += ("; lo split si propaga fino alla radice: nuova radice, un livello in pi\\`u." if h1 > h0
                         else "; il nodo interno riceve un puntatore in pi\\`u" + (" e si divide anche lui." if n1 > n0 else "."))
        else:
            t = pt2_btree.delete(t, k, f)
            f1, h1, n1 = stat(t)
            if f1 == f0:
                cosa = f"la foglia resta con almeno {min_keys} chiavi (o si ridistribuisce col fratello sinistro): nessun merge."
            else:
                cosa = f"la foglia scende sotto {min_keys} chiavi: MERGE col fratello sinistro"
                cosa += ("; anche il nodo interno scende sotto il minimo e si fonde: un livello in meno." if h1 < h0
                         else "; si ricalcolano le chiavi del nodo interno.")
        L.append(esc(f"{'Inserimento' if op['op'] == 'insert' else 'Cancellazione'} di {k}: ") + cosa + "\\par\\smallskip\n")
        L.append(_btree_tikz(t, f"{letter}) dopo {op['op']} {k}"))
    return "".join(L)


def render_teoria(ex):
    """Domanda di teoria: testo domanda + risposta discorsiva scritta nello spec
    (campo 'risposta': lista di paragrafi, o stringhe che iniziano con '- ' per elenchi).
    Le risposte NON vengono da un motore: vanno scritte basandosi sulle slide."""
    L = [_titolo(ex)]
    if ex.get("domanda"):
        L.append("\\textit{" + (_domanda_evidenziata(ex["domanda"]) if COLORI else esc(ex["domanda"])) + "}\\par\\medskip\n")
    L.append(SOL)
    items = []
    def flush_items():
        if items:
            L.append("\\begin{itemize}" +
                     "".join("\\item " + esc(i) + "\n" for i in items) +
                     "\\end{itemize}\n")
            items.clear()
    # --minimal: se lo spec ha la versione corta (scritta dal modello) usa quella
    risposta = ex.get("risposta_minimal") if MINIMAL and ex.get("risposta_minimal") else ex.get("risposta", [])
    for p in risposta:
        if p.startswith("- "):
            items.append(p[2:])
        else:
            flush_items()
            L.append(esc(p) + "\\par\\smallskip\n")
    flush_items()
    return "".join(L)


def render_sql(ex):
    """Query SQL (domande c/d): testo + query in verbatim (controllata prima con sql_check.py)
    + eventuali note ('note': lista di frasi)."""
    L = [_titolo(ex), "\\textit{" + esc(ex["domanda"]) + "}\\par\\medskip\n", SOL,
         "\\begin{verbatim}\n" + ex["query"].rstrip() + "\n\\end{verbatim}\n"]
    L += [note(esc(n)) for n in ex.get("note", [])]
    return "".join(L)


RENDERERS = {"ripresa": render_ripresa, "schedule": render_schedule,
             "costo": render_costo, "btree": render_btree, "teoria": render_teoria, "sql": render_sql}

def render_esercizio(ex):
    """Testo d'esame (titolo + dati) normale, risposta nel riquadro 'soluzione' (blu, barra).
    SOL separa le due parti; se manca, e' soluzione tutto cio' che segue il titolo."""
    s = RENDERERS[ex["tipo"]](ex)
    if SOL not in s:
        t = _titolo(ex)
        s = t + SOL + s[len(t):]
    testa, corpo = s.split(SOL, 1)
    return testa + "\\begin{soluzione}\n" + corpo + "\\end{soluzione}\n"
