
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.engine.script_parser import ScriptParser
from src.engine.variable_store import VariableStore

def test_script_parser():
    print("--- Testing ScriptParser ---")
    store = VariableStore()
    parser = ScriptParser(store)

    # Test cases based on MACRO_DEFINITIONS in src/core/definitions.py
    test_events = [
        {"type": "set", "parameters": {"name": "gold", "value": 100}},
        {"type": "addItem", "parameters": {"item_id": "sword", "qty": 1}},
        {"type": "spawn", "parameters": {"id": "guard_01", "target": "Gate", "x": 10, "y": 20}},
        {"type": "movePnj", "parameters": {"id": "guard_01", "target": "Castle", "x": 50, "y": 50}},
        {"type": "setrelation", "parameters": {"id": "merchant_01", "value": 75}},
        {"type": "setmood", "parameters": {"id": "king", "mood": "angry"}},
        {"type": "print", "parameters": {"text": "Hello World"}},
    ]

    print("Executing events...")
    parser.execute_events(test_events)

    # Verify VariableStore updates
    gold = store.get_var("gold")
    print(f"Gold: {gold} (Expected: 100)")
    
    inventory = store.get_var("inventory", {})
    print(f"Inventory: {inventory} (Expected: {{'sword': 1}})")

    if gold == 100 and inventory.get("sword") == 1:
        print("SUCCESS: ScriptParser handled events correctly.")
    else:
        print("FAILURE: ScriptParser did not update state correctly.")

if __name__ == "__main__":
    test_script_parser()
