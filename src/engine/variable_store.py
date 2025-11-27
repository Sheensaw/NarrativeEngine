# src/engine/variable_store.py
from typing import Any, Dict, Callable, List


class VariableStore:
    """
    Gère l'état global du jeu (variables, inventaire, quêtes).
    Implémente le pattern Observer pour notifier l'UI des changements.
    """

    def __init__(self):
        # Stockage principal des variables {nom: valeur}
        self._variables: Dict[str, Any] = {
            "health": 10,
            "max_health": 10,
            "strength": 0,
            "dexterity": 0,
            "resistance": 0,
            "gold": 0,
            "inventory": {},      # {item_id: qty}
            "equipped": {},       # {slot: item_id}
            "companions": [],     # [npc_id]
            "active_quests": [],  # [quest_id]
            "completed_quests": []
        }

        # Liste des fonctions à appeler quand une variable change
        # Signature: callback(var_name: str, new_value: Any)
        self._observers: List[Callable[[str, Any], None]] = []


    def load_state(self, variables: Dict[str, Any]):
        """Charge un état complet (ex: chargement de sauvegarde ou init projet)."""
        self._variables = variables.copy()
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
        inv = self.get_var("inventory", {})
        if item_id in inv:
            inv[item_id] += qty
        else:
            inv[item_id] = qty
        self.set_var("inventory", inv)
        print(f"[Jeu] Ajout item : {item_id} x{qty}")

    def remove_item(self, item_id: str, qty: int = 1):
        """Retire un item."""
        inv = self.get_var("inventory", {})
        if item_id in inv:
            inv[item_id] = max(0, inv[item_id] - qty)
            if inv[item_id] == 0:
                del inv[item_id]
            self.set_var("inventory", inv)

    def start_quest(self, quest_id: str):
        """Démarre une quête."""
        quests = self.get_var("active_quests", [])
        if quest_id not in quests:
            quests.append(quest_id)
            self.set_var("active_quests", quests)
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