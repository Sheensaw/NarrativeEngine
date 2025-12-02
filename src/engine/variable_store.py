# src/engine/variable_store.py
from typing import Any, Dict, Callable, List, Optional


class VariableStore:
    """Gère l'état global des variables du jeu (stats, inventaire, quêtes...)."""

    def __init__(self):
        self._observers: List[Callable[[str, Any], None]] = []
        self._variables: Dict[str, Any] = {
            "health": 100,
            "max_health": 100,
            "strength": 10,
            "dexterity": 10,
            "resistance": 0,
            "gold": 0,
            "inventory": {},
            "player_coordinates": {"x": 0, "y": 0, "continent": "Eldaron"},
            "visit_counts": {},
            "node_text_overrides": {},
            "used_choices": [],
            "active_quests": [],
            "completed_quests": [],
            "equipped": {}
        }

    def load_state(self, data: Dict[str, Any]):
        """Charge l'état des variables depuis une sauvegarde ou un projet."""
        if not data:
            return
            
        # Update known keys
        for key, value in data.items():
            self._variables[key] = value
            
        # Sanitize player_coordinates
        coords = self._variables.get("player_coordinates")
        if not isinstance(coords, dict):
             self._variables["player_coordinates"] = {"x": 0, "y": 0, "continent": "Eldaron"}
        else:
             # Ensure keys exist
             if "x" not in coords: coords["x"] = 0
             if "y" not in coords: coords["y"] = 0
             if "continent" not in coords: coords["continent"] = "Eldaron"

    def set_var(self, name: str, value: Any):
        """Définit ou met à jour une variable."""
        old_val = self._variables.get(name)
        if old_val != value:
            self._variables[name] = value
            self.notify(name, value)

    def get_var(self, name: str, default: Any = None) -> Any:
        """Récupère la valeur d'une variable."""
        return self._variables.get(name, default)
        
    def get_all(self) -> Dict[str, Any]:
        """Retourne une copie de toutes les variables."""
        return self._variables.copy()

    def add_observer(self, callback: Callable[[str, Any], None]):
        """Abonne une fonction aux changements de variables."""
        if callback not in self._observers:
            self._observers.append(callback)

    def notify(self, name: str, value: Any):
        """Avertit les observateurs d'un changement spécifique."""
        for callback in self._observers:
            try:
                callback(name, value)
            except Exception as e:
                print(f"[VariableStore] Erreur dans un observer : {e}")

    def notify_all(self):
        """Force la notification de toutes les variables."""
        for name, value in self._variables.items():
            self.notify(name, value)

    # --- Helpers RPG ---

    def add_item(self, item_id: str, qty: int = 1):
        """Ajoute un item à l'inventaire (variable 'inventory')."""
        # IMPORTANT: .copy() pour créer une nouvelle référence et déclencher le notify
        inv = self.get_var("inventory", {})
        if not isinstance(inv, dict):
            inv = {}
        else:
            inv = inv.copy()

        if item_id in inv:
            inv[item_id] += qty
        else:
            inv[item_id] = qty
        self.set_var("inventory", inv)
        print(f"[Jeu] Ajout item : {item_id} x{qty}")

    def remove_item(self, item_id: str, qty: int = 1):
        """Retire un item."""
        inv = self.get_var("inventory", {})
        if not isinstance(inv, dict):
            inv = {}
        else:
            inv = inv.copy()

        if item_id in inv:
            inv[item_id] = max(0, inv[item_id] - qty)
            if inv[item_id] == 0:
                del inv[item_id]
            self.set_var("inventory", inv)

    def start_quest(self, quest_id: str):
        """Démarre une quête."""
        active = self.get_var("active_quests", [])
        if quest_id not in active:
            active.append(quest_id)
            self.set_var("active_quests", active)
            print(f"[Jeu] Quête démarrée : {quest_id}")

    def complete_quest(self, quest_id: str):
        """Termine une quête."""
        active = self.get_var("active_quests", [])
        completed = self.get_var("completed_quests", [])
        
        if quest_id in active:
            active.remove(quest_id)
            self.set_var("active_quests", active)
        
        if quest_id not in completed:
            completed.append(quest_id)
            self.set_var("completed_quests", completed)
            print(f"[Jeu] Quête terminée : {quest_id}")

    def equip_item(self, item_id: str, slot: str):
        """Équipe un item dans un slot donné."""
        # 1. Get current state
        equipped = self.get_var("equipped", {})
        if not isinstance(equipped, dict): equipped = {}
        else: equipped = equipped.copy()
        
        # 2. Check if slot is occupied
        if slot in equipped:
            # We just replace it. The old item stays in inventory (it never left).
            pass
            
        # 3. Equip new item
        equipped[slot] = item_id
        self.set_var("equipped", equipped)
        print(f"[Jeu] Item équipé : {item_id} sur {slot}")

    def unequip_item(self, slot: str):
        """Déséquipe un item d'un slot."""
        equipped = self.get_var("equipped", {})
        if not isinstance(equipped, dict): equipped = {}
        else: equipped = equipped.copy()
        
        if slot in equipped:
            del equipped[slot]
            self.set_var("equipped", equipped)
            print(f"[Jeu] Item déséquipé du slot {slot}")

    def mark_choice_used(self, choice_id: str):
        """Marque un choix comme utilisé."""
        used = self.get_var("used_choices", [])
        if not isinstance(used, list): used = []
        else: used = list(used) # Copy
        
        if choice_id not in used:
            used.append(choice_id)
            self.set_var("used_choices", used)

    def is_choice_used(self, choice_id: str) -> bool:
        """Vérifie si un choix a déjà été utilisé."""
        used = self.get_var("used_choices", [])
        if not isinstance(used, list): return False
        return choice_id in used

    def set_node_text(self, node_id: str, text: str):
        """Définit un texte de remplacement pour un nœud."""
        overrides = self.get_var("node_text_overrides", {})
        if not isinstance(overrides, dict): overrides = {}
        else: overrides = overrides.copy()
        
        overrides[node_id] = text
        self.set_var("node_text_overrides", overrides)

    def get_node_text(self, node_id: str) -> Optional[str]:
        """Récupère le texte de remplacement d'un nœud s'il existe."""
        overrides = self.get_var("node_text_overrides", {})
        if not isinstance(overrides, dict): return None
        return overrides.get(node_id)

    # --- Visit Counts ---

    def increment_visit_count(self, node_id: str):
        """Incrémente le compteur de visites pour un nœud."""
        visits = self.get_var("visit_counts", {})
        if not isinstance(visits, dict): visits = {}
        else: visits = visits.copy()
        
        current = visits.get(node_id, 0)
        visits[node_id] = current + 1
        self.set_var("visit_counts", visits)
        
    def get_visit_count(self, node_id: str) -> int:
        """Retourne le nombre de visites pour un nœud."""
        visits = self.get_var("visit_counts", {})
        if not isinstance(visits, dict): return 0
        return visits.get(node_id, 0)