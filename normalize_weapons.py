import json
import os

def normalize_weapons():
    path = "data/items/weapons.json"
    if not os.path.exists(path):
        print("File not found.")
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Flatten Structure (Handle {"category": [...]})
    items_list = []
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, list):
                items_list.extend(val)
    elif isinstance(data, list):
        items_list = data
    else:
        print("Unknown format.")
        return

    # 2. Normalize Fields
    normalized_items = []
    for item in items_list:
        new_item = item.copy()
        
        # Name/Label
        if "label" in new_item and "name" not in new_item:
            new_item["name"] = new_item.pop("label")
            
        # Damage
        if "damage" in new_item and isinstance(new_item["damage"], dict):
            dmg = new_item.pop("damage")
            new_item["damage_min"] = dmg.get("min", 0)
            new_item["damage_max"] = dmg.get("max", 0)
            
        # Requirements (Flattening optional, but Editor uses 'requirements' dict, so keep it)
        # Editor uses: props.get("requirements", {}).get("forceMin") -> This matches JSON structure!
        
        # Crit (CamelCase to snake_case if needed, but Editor uses keys directly)
        # Editor uses: props.get("crit_chance")
        # JSON has: "critChance"
        if "critChance" in new_item:
            new_item["crit_chance"] = new_item.pop("critChance")
            
        # Editor uses: props.get("is_two_handed")
        # JSON has: "isTwoHanded" (sometimes missing)
        if "isTwoHanded" in new_item:
            new_item["is_two_handed"] = new_item.pop("isTwoHanded")

        normalized_items.append(new_item)

    # 3. Save back
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(normalized_items, f, indent=4, ensure_ascii=False)
    
    print(f"Normalized {len(normalized_items)} weapons.")

if __name__ == "__main__":
    normalize_weapons()
