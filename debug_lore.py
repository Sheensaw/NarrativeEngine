import os
import json
from src.core.lore_manager import LoreManager

def debug_lore():
    lore_dir = "tests/mock_lore_debug"
    os.makedirs(lore_dir, exist_ok=True)
    
    # Create Macro File (velkarum.json)
    macro_data = {
        "nodes": {
            "Lorn": {
                "x": 45, "y": 55, "continent": "Eldaron",
                "name": "Lorn (Macro)", "type": "City"
            }
        }
    }
    with open(os.path.join(lore_dir, "velkarum.json"), "w") as f:
        json.dump(macro_data, f)
        
    print(f"Created mock lore in {lore_dir}")
    
    manager = LoreManager(lore_dir)
    manager.load_lore()
    print(f"Loaded {len(manager.locations)} locations")
    for l in manager.locations:
        print(f"  - {l['name']} ({l['x']}, {l['y']}) [{l['continent']}]")
    
    print("Calling get_location_at(45, 55, 'Eldaron')...")
    loc = manager.get_location_at(45, 55, "Eldaron")
    print(f"Result: {loc}")

if __name__ == "__main__":
    debug_lore()
