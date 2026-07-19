"""Test pt2_btree contro la soluzione UFFICIALE 20_esR_b+tree.pdf (fan-out 5):
1) costruzione: root (F,O,S,W)
2) insert H: root (O); intermedi (F,H) (S,W); foglie (A,B,C,D)(F,G)(H,M,N)(O,P)(S,T)(W,Z)
3) delete Z: root (F,H,O,S); foglie (A,B,C,D)(F,G)(H,M,N)(O,P)(S,T,W)"""
import pt2_btree as bt

F = 5
LEAVES = [["A","B","C","D"], ["F","G","M","N"], ["O","P"], ["S","T"], ["W","Z"]]

# 1) costruzione
t = bt.build(LEAVES, F)
assert bt.levels(t) == [
    [["F","O","S","W"]],
    [["A","B","C","D"], ["F","G","M","N"], ["O","P"], ["S","T"], ["W","Z"]],
], bt.levels(t)

# 2) insert H
t = bt.insert(t, "H", F)
assert bt.levels(t) == [
    [["O"]],
    [["F","H"], ["S","W"]],
    [["A","B","C","D"], ["F","G"], ["H","M","N"], ["O","P"], ["S","T"], ["W","Z"]],
], bt.levels(t)

# 3) delete Z
t = bt.delete(t, "Z", F)
assert bt.levels(t) == [
    [["F","H","O","S"]],
    [["A","B","C","D"], ["F","G"], ["H","M","N"], ["O","P"], ["S","T","W"]],
], bt.levels(t)

print(bt.render_text(t))

# Vincoli di riempimento fan-out PARI (Lezione_04_Strutture_Fisiche_BTree_Hash.pdf, teoria
# ufficiale): fan-out=4 -> 2<=#chiavi<=3, 2<=#puntatori<=4. Bug reale: ceil(f/2)-1 dava 1
# invece di 2 per f pari (formula corretta e' ceil((f-1)/2)).
assert bt._mins(4) == (2, 2), bt._mins(4)
assert bt._mins(5) == (3, 2), bt._mins(5)
assert bt._mins(3) == (2, 1), bt._mins(3)
assert bt._mins(6) == (3, 3), bt._mins(6)

# Costruzione con fan-out=4 (esempio slide pag.9, CASO A riempimento minimo):
# foglie A,B | D,E | F,G | L,M | N,P -> root con 2 chiavi (min), 3 puntatori (min)
t4 = bt.build([["A","B"], ["D","E"], ["F","G"], ["L","M"], ["N","P"]], 4)
lv = bt.levels(t4)
assert lv[-1] == [["A","B"], ["D","E"], ["F","G"], ["L","M"], ["N","P"]], lv[-1]

print("TUTTI I TEST OK")
