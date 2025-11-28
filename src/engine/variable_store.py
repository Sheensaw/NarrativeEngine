# src/engine/variable_store.py
from typing import Any, Dict, Callable, List


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
            "equipped": {},
            "companions": [],
            "used_choices": [], # List of choice IDs
            "active_quests": [],
            "completed_quests": []
        }

    def load_state(self, variables: Dict[str, Any]):
        """Charge un état complet (ex: chargement de sauvegarde ou init projet)."""
        self._variables = variables.copy()
        
        # Sanitize types
        if not isinstance(self._variables.get("inventory"), dict):
            self._variables["inventory"] = {}
        if not isinstance(self._variables.get("equipped"), dict):
            self._variables["equipped"] = {}
        if not isinstance(self._variables.get("used_choices"), list):
            self._variables["used_choices"] = []
            
        # On notifie tout le monde du rechargement complet
        self.notify_all()

    def get_all(self) -> Dict[str, Any]:
        """Retourne une copie de toutes les variables."""
        return self._variables.copy()

    def set_var(self, name: str, value: Any):
        """Définit ou met à jour une variable."""
        old_val = self._variables.get(name)
        if old_val != value:
            self._variables[name] = value
            self.notify(name, value)

    def get_var(self, name: str, default: Any = None) -> Any:
        """Récupère la valeur d'une variable."""
        return self._variables.get(name, default)

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