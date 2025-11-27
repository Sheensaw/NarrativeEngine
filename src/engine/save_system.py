# src/engine/save_system.py
import json
import os
import base64
import time
from typing import Optional
from src.engine.story_manager import StoryManager


class SaveSystem:
    """
    Gère la persistance de la progression du joueur (Save/Load).
    """

    @staticmethod
    def create_save_data(manager: StoryManager) -> dict:
        """Capture l'état actuel du manager pour créer une sauvegarde."""
        if not manager.current_node:
            return {}

        return {
            "timestamp": time.time(),
            "current_node_id": manager.current_node.id,
            "variables": manager.variables.get_all(),
            "history": manager.history
        }

    @staticmethod
    def save_game(manager: StoryManager, filepath: str) -> bool:
        """Ecrit la sauvegarde sur le disque (avec un encodage léger)."""
        data = SaveSystem.create_save_data(manager)
        if not data:
            return False

        try:
            json_str = json.dumps(data)
            # Encodage Base64 simple pour éviter la triche trop facile (obfuscation)
            encoded_bytes = base64.b64encode(json_str.encode('utf-8'))

            with open(filepath, 'wb') as f:
                f.write(encoded_bytes)
            return True
        except Exception as e:
            print(f"[SaveSystem] Erreur écriture : {e}")
            return False

    @staticmethod
    def load_game(manager: StoryManager, filepath: str) -> bool:
        """Charge une sauvegarde et restaure l'état du manager."""
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, 'rb') as f:
                encoded_bytes = f.read()

            json_str = base64.b64decode(encoded_bytes).decode('utf-8')
            data = json.loads(json_str)

            # Restauration
            manager.variables.load_state(data.get("variables", {}))
            manager.history = data.get("history", [])

            # On force le saut vers le nœud sauvegardé
            node_id = data.get("current_node_id")
            if node_id and manager.project and node_id in manager.project.nodes:
                # On utilise set_current_node pour déclencher les scripts on_enter
                # Attention : cela déclenchera aussi on_exit du nœud 'None' initial, ce qui est sans effet
                manager.set_current_node(node_id)

            return True
        except Exception as e:
            print(f"[SaveSystem] Erreur lecture : {e}")
            return False