# src/core/database.py
import sqlite3
import json
import os
from typing import Dict, Any, List, Optional

class DatabaseManager:
    """
    Gère la persistance des données du jeu (Items, Quêtes, PNJ, Lieux) via SQLite.
    """
    
    def __init__(self, db_path: str = "game.db"):
        self.db_path = db_path
        self.connection = None
        self._init_db()

    def _init_db(self):
        """Initialise la connexion et crée les tables si nécessaire."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        cursor = self.connection.cursor()
        
        # Table Items
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                description TEXT,
                data TEXT,
                source_file TEXT
            )
        """)
        
        # Migration: Add source_file if missing (for existing DBs)
        try:
            cursor.execute("ALTER TABLE items ADD COLUMN source_file TEXT")
        except sqlite3.OperationalError:
            pass # Column likely exists

        # Table Quests
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quests (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                data TEXT
            )
        """)
        
        # Table NPCs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS npcs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                data TEXT
            )
        """)

        # Table Locations
        # Schema: id, place, city, coords, type, continent, source_file
        
        # Check if table exists and has 'name' column (Old Schema)
        try:
            cursor.execute("SELECT name FROM locations LIMIT 1")
            # If successful, it means 'name' exists. We need to migrate or drop.
            # Since we have an import script, dropping is safer to enforce new schema.
            print("Detected old 'locations' schema. Dropping table to recreate...")
            cursor.execute("DROP TABLE locations")
        except sqlite3.OperationalError:
            # 'name' column not found or table doesn't exist. Good.
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id TEXT PRIMARY KEY,
                place TEXT NOT NULL,
                city TEXT,
                coords TEXT,
                type TEXT,
                continent TEXT,
                source_file TEXT
            )
        """)
        
        self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()

    # --- GENERIC METHODS ---

    def _save_entity(self, table: str, id: str, name_field: str, name_val: str, **kwargs):
        """Sauvegarde générique (Upsert)."""
        # Construction dynamique
        cols = ["id", name_field]
        vals = [id, name_val]
        placeholders = ["?", "?"]
        
        # Autres colonnes
        for k, v in kwargs.items():
            cols.append(k)
            vals.append(v)
            placeholders.append("?")
        
        sql = f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
        
        cursor = self.connection.cursor()
        cursor.execute(sql, vals)
        self.connection.commit()

    def _get_all(self, table: str) -> Dict[str, Any]:
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        results = {}
        for row in rows:
            d = dict(row)
            # Parse JSON fields if known
            if "data" in d and d["data"]:
                try: d["data"] = json.loads(d["data"])
                except: d["data"] = {}
            if "coords" in d and d["coords"]:
                try: d["coords"] = json.loads(d["coords"])
                except: d["coords"] = {}
                
            results[d["id"]] = d
        return results

    # --- ITEMS ---
    def save_item(self, id: str, name: str, type: str, description: str, properties: Dict, source_file: str = None):
        if not source_file:
            existing = self.get_item(id)
            if existing: source_file = existing.get("source_file")
        
        # Items still use 'data' for props
        data_str = json.dumps(properties) if properties else "{}"
        self._save_entity("items", id, "name", name, type=type, description=description, source_file=source_file, data=data_str)

    def get_item(self, id: str) -> Optional[Dict]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM items WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            if "data" in d and d["data"]:
                try: d["data"] = json.loads(d["data"])
                except: d["data"] = {}
            return d
        return None

    def get_all_items(self) -> Dict[str, Any]:
        return self._get_all("items")

    def import_items_from_json(self, json_path: str):
        if not os.path.exists(json_path): return False
        normalized_path = os.path.abspath(json_path)
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
            if isinstance(items, dict): items = items.values()
            for item in items:
                item_id = item.get("id")
                if not item_id: continue
                name = item.get("name") or item.get("label") or "Unknown"
                itype = item.get("type", "misc")
                desc = item.get("description", "")
                props = {k: v for k, v in item.items() if k not in ["id", "name", "label", "type", "description"]}
                self.save_item(item_id, name, itype, desc, props, source_file=normalized_path)
            return True
        except Exception as e:
            print(f"Error importing items: {e}")
            return False

    def delete_item(self, id: str):
        item = self.get_item(id)
        source_file = item.get("source_file") if item else None
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (id,))
        self.connection.commit()
        if source_file and os.path.exists(source_file):
            self.update_json_from_db(source_file)

    def update_json_from_db(self, source_file: str):
        if not source_file or not os.path.exists(source_file): return False
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM items WHERE source_file = ?", (source_file,))
        rows = cursor.fetchall()
        items_list = []
        for row in rows:
            d = dict(row)
            item_export = {"id": d["id"], "name": d["name"], "type": d["type"], "description": d["description"]}
            if d["data"]:
                try: item_export.update(json.loads(d["data"]))
                except: pass
            items_list.append(item_export)
        try:
            with open(source_file, 'w', encoding='utf-8') as f:
                json.dump(items_list, f, indent=4, ensure_ascii=False)
            print(f"Synced {len(items_list)} items to {source_file}")
            return True
        except Exception as e:
            print(f"Error syncing JSON: {e}")
            return False

    # --- QUESTS ---
    def save_quest(self, id: str, title: str, description: str, properties: Dict):
        data_str = json.dumps(properties) if properties else "{}"
        self._save_entity("quests", id, "title", title, description=description, data=data_str)

    def get_all_quests(self) -> Dict[str, Any]:
        return self._get_all("quests")

    # --- NPCS ---
    def save_npc(self, id: str, name: str, properties: Dict):
        data_str = json.dumps(properties) if properties else "{}"
        self._save_entity("npcs", id, "name", name, data=data_str)

    def get_all_npcs(self) -> Dict[str, Any]:
        return self._get_all("npcs")
    
    def import_npcs_from_json(self, json_path: str):
        if not os.path.exists(json_path): return False
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                npcs = json.load(f)
            if isinstance(npcs, dict): npcs = npcs.values()
            for npc in npcs:
                nid = npc.get("id")
                if not nid: continue
                name = npc.get("name", "Unknown")
                props = {k: v for k, v in npc.items() if k not in ["id", "name"]}
                self.save_npc(nid, name, props)
            return True
        except Exception as e:
            print(f"Error importing NPCs: {e}")
            return False

    # --- LOCATIONS ---
    def save_location(self, id: str, place: str, city: str, coords: Dict, type: str, continent: str, source_file: str = None):
        if not source_file:
            existing = self.get_location(id)
            if existing: source_file = existing.get("source_file")
        
        coords_str = json.dumps(coords) if coords else "{}"
        self._save_entity("locations", id, "place", place, city=city, coords=coords_str, type=type, continent=continent, source_file=source_file)

    def get_location(self, id: str) -> Optional[Dict]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM locations WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            if "coords" in d and d["coords"]:
                try: d["coords"] = json.loads(d["coords"])
                except: d["coords"] = {}
            return d
        return None

    def get_all_locations(self) -> Dict[str, Any]:
        return self._get_all("locations")

    def import_locations_from_json(self, json_path: str):
        if not os.path.exists(json_path): return False
        normalized_path = os.path.abspath(json_path)
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            locations = []
            if "nodes" in data:
                for key, node in data["nodes"].items():
                    node["id"] = key
                    locations.append(node)
            elif isinstance(data, list): locations = data
            elif isinstance(data, dict): locations = data.values()
            
            for loc in locations:
                loc_id = loc.get("id")
                if not loc_id: continue
                
                place = loc.get("name") or loc.get("place") or "Unknown"
                city = loc.get("city", "")
                ltype = loc.get("type", "Unknown")
                continent = loc.get("continent", "Unknown")
                
                # Extract coords
                x = loc.get("x", 0)
                y = loc.get("y", 0)
                coords = {"x": x, "y": y}
                
                self.save_location(loc_id, place, city, coords, ltype, continent, source_file=normalized_path)
            return True
        except Exception as e:
            print(f"Error importing locations: {e}")
            return False

    def delete_location(self, id: str):
        loc = self.get_location(id)
        source_file = loc.get("source_file") if loc else None
        
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM locations WHERE id = ?", (id,))
        self.connection.commit()
        
        if source_file and os.path.exists(source_file):
            self.update_location_json_from_db(source_file)

    def update_location_json_from_db(self, source_file: str):
        if not source_file or not os.path.exists(source_file): return False
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM locations WHERE source_file = ?", (source_file,))
        rows = cursor.fetchall()
        nodes_dict = {}
        for row in rows:
            d = dict(row)
            loc_id = d["id"]
            
            # Reconstruct
            node_data = {
                "name": d["place"], # Map back 'place' to 'name' in JSON? Or keep 'place'? 
                                    # Lore JSONs usually use 'name' for the place name.
                                    # User said "place (actuellement name)".
                                    # I will map DB 'place' -> JSON 'name' to maintain compatibility if other tools expect 'name'.
                                    # Or should I use 'place' in JSON too?
                                    # Existing JSONs use 'name'. I should probably stick to 'name' in JSON for now unless user wants full refactor.
                                    # But wait, user said "place (actuellement name)".
                                    # I'll use 'name' in JSON for compatibility.
                "city": d["city"],
                "type": d["type"],
                "continent": d["continent"]
            }
            
            if d["coords"]:
                try:
                    coords = json.loads(d["coords"])
                    node_data["x"] = coords.get("x", 0)
                    node_data["y"] = coords.get("y", 0)
                except: pass
            
            nodes_dict[loc_id] = node_data
            
        export_data = {"nodes": nodes_dict}
        try:
            with open(source_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            print(f"Synced {len(nodes_dict)} locations to {source_file}")
            return True
        except Exception as e:
            print(f"Error syncing JSON: {e}")
            return False
