import os
import json

LORE_DIR = r"c:\Users\garwi\Documents\Twine\Stories\Sword\server\lore"

def get_main_location_name(node_id, node_data):
    name = node_data.get("name", "")
    
    # 1. Explicit " - " in name (e.g. "Lorn - Place Royale")
    if " - " in name:
        return name.split(" - ")[0]
        
    # 2. ID based heuristics
    parts = node_id.split("_")
    
    # Known prefixes mapping
    PREFIX_MAP = {
        "Lorn": "Lorn",
        "Ardel": "Ardel",
        "OstVelen": "Ost-Velen",
        "Gue": "Gué-du-Roi",
        "Dalen": "Dalen",
        "KharGhul": "Khar-Ghul",
        "PortOstral": "Port-Ostral",
        "Lirn": "Lirn",
        "Vulkar": "Vulkar",
        "Relais": "Relais",
        "Ruines": "Ruines",
        "Foret": "Forêt",
        "Village": "Village",
        "Thaurgrim": "Thaurgrim",
        "Iskarion": "Iskarion",
        "Helrun": "Helrün",
        "Varnal": "Varnäl",
        "Velkar": "Velkar",
        "Tarran": "Tarran",
        "Falaar": "Falaar",
        "Cenra": "Cenra",
        "Kaar": "Kaar",
        "Thun": "Thun'ar",
        "Agri": "Agri-Nove",
        "Zhair": "Zhaïr",
        "Shaar": "Shaar-Keth",
        "Korra": "Korra",
        "Asuren": "Asuren",
        "Vethar": "Vethar",
        "Skarnheim": "Skarnheim",
        "Nerr": "Nerr",
        "Narvik": "Narvik",
        "Ygral": "Ygral",
        "Isbjorn": "Isbjorn-Havn"
    }

    first_part = parts[0]
    if first_part in PREFIX_MAP:
        return PREFIX_MAP[first_part]
        
    # Special handling for multi-word prefixes like "Foret_Noire"
    if len(parts) >= 2:
        prefix_2 = f"{parts[0]}_{parts[1]}"
        if prefix_2 == "Foret_Noire":
            return "Forêt Noire"
        if prefix_2 == "Port_Ostral":
            return "Port-Ostral"
            
    # Fallback: Just capitalize the first part of ID or Name
    return name.split(" ")[0]

def update_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if "nodes" not in data:
            return

        modified = False
        for key, node in data["nodes"].items():
            if "main_location_name" not in node:
                main_loc = get_main_location_name(key, node)
                node["main_location_name"] = main_loc
                modified = True
                print(f"[{key}] Added main_location_name: {main_loc}")
        
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Updated {filepath}")
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    if not os.path.exists(LORE_DIR):
        print(f"Directory not found: {LORE_DIR}")
        return

    for filename in os.listdir(LORE_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(LORE_DIR, filename)
            update_json_file(filepath)

if __name__ == "__main__":
    main()
