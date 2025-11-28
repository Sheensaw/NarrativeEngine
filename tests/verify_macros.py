import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.engine.script_parser import ScriptParser
from src.engine.variable_store import VariableStore
from src.core.definitions import MACRO_DEFINITIONS

def test_macros():
    store = VariableStore()
    parser = ScriptParser(store)
    
    print("Testing NPC Macros...")
    
    # Test spawn
    print("\n[Test] spawn")
    parser._dispatch_event("spawn", {"pnjId": "guard_01", "x": 10, "y": 20})
    
    # Test movePnj
    print("\n[Test] movePnj")
    parser._dispatch_event("movePnj", {"pnjId": "guard_01", "targetPassage": "CastleGate", "x": 15, "y": 25})
    
    # Test setrelation
    print("\n[Test] setrelation")
    parser._dispatch_event("setrelation", {"pnjId": "guard_01", "value": 50})
    
    # Test changemood
    print("\n[Test] changemood")
    parser._dispatch_event("changemood", {"pnjId": "guard_01", "value": "angry"})
    
    print("\nVerification complete.")

if __name__ == "__main__":
    test_macros()
