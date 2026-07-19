import sys
import pt2_btree as bt
import pt2_costo as pc

def test_btree_cascading_split():
    print("--- Test B-Tree Cascading Split (fan-out=3) ---")
    F = 3
    root = [1, 2]
    for i in [3, 4, 5, 6, 7, 8]:
        root = bt.insert(root, i, F)
        
    print("Albero iniziale:")
    print(bt.render_text(root))
    
    print("Inserisco 9:")
    root = bt.insert(root, 9, F)
    print(bt.render_text(root))

def test_btree_delete_decrease_height():
    print("\n--- Test B-Tree Delete Height Decrease ---")
    F = 3
    root = [1, 2]
    for i in [3, 4]:
        root = bt.insert(root, i, F)
    print("Albero iniziale:")
    print(bt.render_text(root))
    
    print("Cancello 4:")
    root = bt.delete(root, 4, F)
    print(bt.render_text(root))
    
    print("Cancello 3:")
    root = bt.delete(root, 3, F)
    print(bt.render_text(root))

def test_costo_val_1():
    print("\n--- Test Costo VAL=1 (Selettivita' 100%) ---")
    res = pc.solve(np_outer=100, nr_outer=1000, val_sel_outer=1,
                   np_inner=500, pagine_sel_inner=500,
                   nr_sel_inner=5000, val_join_inner=500, prof_indice=2)
    
    for step in res["steps"]:
        print(step)
    
    print("ns outer:", res["nr_sel_esterna"])
    print("Totale:", res["totale"])
    
    try:
        assert res["nr_sel_esterna"] == 1000
        assert res["totale"] == 501100
        print("Calcoli costo corretti.")
    except Exception as e:
        print("ERRORE nel calcolo:", e)

if __name__ == "__main__":
    try:
        test_btree_cascading_split()
        test_btree_delete_decrease_height()
        test_costo_val_1()
    except Exception as e:
        print(f"Exception raised: {e}")
