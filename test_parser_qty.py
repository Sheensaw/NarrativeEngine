from src.engine.script_parser import ScriptParser
from src.engine.variable_store import VariableStore

def test_qty_logic():
    store = VariableStore()
    parser = ScriptParser(store)
    
    # Test 1: Event with "quantity"
    print("Testing 'quantity' parameter...")
    parser.execute_events([{"type": "addItem", "parameters": {"item_id": "apple", "quantity": 5}}])
    
    # Test 2: Event with "qty" (User case)
    print("Testing 'qty' parameter...")
    parser.execute_events([{"type": "addItem", "parameters": {"item_id": "apple", "qty": 3}}])
    
    inv = store.get_var("inventory")
    print(f"Final Inventory: {inv}")
    
    expected = 8
    actual = inv.get("apple", 0)
    
    if actual == expected:
        print(f"✅ SUCCESS: Total is {actual}")
    else:
        print(f"❌ FAILURE: Expected {expected}, got {actual}")

if __name__ == "__main__":
    test_qty_logic()
