from src.core.database import DatabaseManager
import os

db = DatabaseManager()
base_path = os.path.join(os.getcwd(), "data", "items")

files = ["weapons.json", "food.json", "potions.json"]

print("Updating Database from JSON files...")
for f in files:
    path = os.path.join(base_path, f)
    if os.path.exists(path):
        if db.import_items_from_json(path):
            print(f"✅ Imported {f}")
        else:
            print(f"❌ Failed to import {f}")
    else:
        print(f"⚠️ File not found: {f}")

db.close()
print("Done.")
