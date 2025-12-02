import os
import sys
import glob

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.database import DatabaseManager

def import_lore():
    db = DatabaseManager("game.db")
    lore_dir = os.path.abspath(os.path.join("server", "lore"))
    
    print(f"Importing lore from {lore_dir}...")
    
    json_files = glob.glob(os.path.join(lore_dir, "*.json"))
    
    for json_file in json_files:
        print(f"Processing {os.path.basename(json_file)}...")
        success = db.import_locations_from_json(json_file)
        if success:
            print(f"  -> Success")
        else:
            print(f"  -> Failed")
            
    db.close()
    print("Import complete.")

if __name__ == "__main__":
    import_lore()
