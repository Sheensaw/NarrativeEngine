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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                data TEXT
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
        
        # Autres colonnes (ex: type, description, source_file)
        for k, v in kwargs.items():
            if k != "data":
                cols.append(k)
                vals.append(v)
                placeholders.append("?")
        
        # Data JSON
        data = kwargs.get("data", {})
        if isinstance(data, dict):
            data = json.dumps(data)
        cols.append("data")
        vals.append(data)
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
            if "data" in d and d["data"]:
                try:
                    d["data"] = json.loads(d["data"])
                except:
                    d["data"] = {}
            results[d["id"]] = d
        return results

    # --- ITEMS ---
    def save_item(self, id: str, name: str, type: str, description: str, properties: Dict, source_file: str = None):
        # Si source_file n'est pas fourni, on essaie de le récupérer de l'existant
        if not source_file:
            existing = self.get_item(id)
            if existing:
                source_file = existing.get("source_file")
        
        self._save_entity("items", id, "name", name, type=type, description=description, source_file=source_file, data=properties)

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
        """Importe une liste d'items depuis un fichier JSON."""
        if not os.path.exists(json_path):
            return False
        
        # Normalisation du chemin pour stockage
        normalized_path = os.path.abspath(json_path)
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
                
            # Support list or dict format
            if isinstance(items, dict):
                items = items.values()
                
            for item in items:
                # Mapping flexible selon le format d'entrée
                item_id = item.get("id")
                if not item_id: continue
                
                name = item.get("name") or item.get("label") or "Unknown"
                itype = item.get("type", "misc")
                desc = item.get("description", "")
                
                # Tout le reste va dans data/properties
                props = {k: v for k, v in item.items() if k not in ["id", "name", "label", "type", "description"]}
                
                self.save_item(item_id, name, itype, desc, props, source_file=normalized_path)
            return True
        except Exception as e:
            print(f"Error importing items: {e}")
            return False

    def delete_item(self, id: str):
        """Supprime un item de la DB et du fichier JSON source."""
        # 1. Récupérer l'info pour le fichier source
        item = self.get_item(id)
        source_file = item.get("source_file") if item else None
        
        # 2. Supprimer de la DB
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (id,))
        self.connection.commit()
        
        # 3. Mettre à jour le JSON si nécessaire
        if source_file and os.path.exists(source_file):
            self.update_json_from_db(source_file)

    def update_json_from_db(self, source_file: str):
        """Réécrit le fichier JSON avec les données actuelles de la DB pour ce fichier."""
        if not source_file or not os.path.exists(source_file):
            return False
            
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM items WHERE source_file = ?", (source_file,))
        rows = cursor.fetchall()
        
        items_list = []
        for row in rows:
            d = dict(row)
            item_export = {
                "id": d["id"],
                "name": d["name"],
                "type": d["type"],
                "description": d["description"]
            }
            
            # Merge properties
            if d["data"]:
                try:
                    props = json.loads(d["data"])
                    item_export.update(props)
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
        self._save_entity("quests", id, "title", title, description=description, data=properties)

    def get_all_quests(self) -> Dict[str, Any]:
        return self._get_all("quests")

    # --- NPCS ---
    def save_npc(self, id: str, name: str, properties: Dict):
        self._save_entity("npcs", id, "name", name, data=properties)

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
    def save_location(self, id: str, name: str, properties: Dict):
        self._save_entity("locations", id, "name", name, data=properties)

    def get_all_locations(self) -> Dict[str, Any]:
        return self._get_all("locations")
