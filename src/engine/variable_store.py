# src/engine/variable_store.py
from typing import Any, Dict, Callable, List, Optional

class VariableStore:
    def __init__(self):
        self._observers: List[Callable[[str, Any], None]] = []
        self._variables: Dict[str, Any] = {
            "health": 100,
            "max_health": 100,
            "strength": 10,
            "dexterity": 10,
            "resistance": 0,
            "xp": 0,
            "level": 1,
            "xp_next": 100,
            "gold": 0,
            "inventory": {},
            "active_quests": [],
            "completed_quests": [],
            "returned_quests": [],
            "active_quest_offer": None,
            "player_coordinates": {"x": 0, "y": 0, "continent": "Eldaron"},
        }

    def load_state(self, data: Dict[str, Any]):
        if not data:
            return
        for key, value in data.items():
            self._variables[key] = value
        coords = self._variables.get("player_coordinates")
        if not isinstance(coords, dict):
             self._variables["player_coordinates"] = {"x": 0, "y": 0, "continent": "Eldaron"}
        else:
             if "x" not in coords: coords["x"] = 0
             if "y" not in coords: coords["y"] = 0
             if "continent" not in coords: coords["continent"] = "Eldaron"

    def set_var(self, name: str, value: Any):
        old_val = self._variables.get(name)
        if old_val != value:
            self._variables[name] = value
            self.notify(name, value)

    def get_var(self, name: str, default: Any = None) -> Any:
        return self._variables.get(name, default)
        
    def get_all(self) -> Dict[str, Any]:
        return self._variables.copy()

    def add_observer(self, callback: Callable[[str, Any], None]):
        if callback not in self._observers:
            self._observers.append(callback)

    def notify(self, name: str, value: Any):
        for callback in self._observers:
            try:
                callback(name, value)
            except Exception as e:
                print(f"[VariableStore] Erreur dans un observer : {e}")

    def notify_all(self):
        for name, value in self._variables.items():
            self.notify(name, value)

    def add_xp(self, amount: int):
        current_xp = self.get_var("xp", 0)
        current_lvl = self.get_var("level", 1)
        xp_next = self.get_var("xp_next", 100)
        
        current_xp += amount
        
        leveled_up = False
        while current_xp >= xp_next:
            current_xp -= xp_next
            current_lvl += 1
            xp_next = int(current_lvl * 100 * 1.5) # Simple curve
            leveled_up = True
            
        self.set_var("xp", current_xp)
        self.set_var("level", current_lvl)
        self.set_var("xp_next", xp_next)
        
        if leveled_up:
            print(f"[Jeu] Niveau supérieur ! Niveau {current_lvl}")
            # Optionally trigger an event or heal player here
            max_hp = self.get_var("max_health", 100)
            self.set_var("health", max_hp)

    def add_item(self, item_id: str, qty: int = 1):
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
        active = self.get_var("active_quests", [])
        completed = self.get_var("completed_quests", [])
        returned = self.get_var("returned_quests", [])
        
        # Prevent restarting if already active, completed or returned
        if quest_id in active or quest_id in completed or quest_id in returned:
            return

        active.append(quest_id)
        self.set_var("active_quests", active)
        
        # Initialize step progress
        steps = self.get_var("quest_steps", {})
        steps[quest_id] = 0
        self.set_var("quest_steps", steps)
        
        print(f"[Jeu] Quête démarrée : {quest_id}")

    def advance_quest_step(self, quest_id: str):
        active = self.get_var("active_quests", [])
        if quest_id not in active:
            return

        steps = self.get_var("quest_steps", {})
        current_step = steps.get(quest_id, 0)
        steps[quest_id] = current_step + 1
        self.set_var("quest_steps", steps)
        print(f"[Jeu] Quête {quest_id} avancée à l'étape {current_step + 1}")

    def complete_quest(self, quest_id: str):
        active = self.get_var("active_quests", [])
        completed = self.get_var("completed_quests", [])
        
        # Only complete if currently active
        if quest_id in active:
            active.remove(quest_id)
            self.set_var("active_quests", active)
            
            if quest_id not in completed:
                completed.append(quest_id)
                self.set_var("completed_quests", completed)
                print(f"[Jeu] Quête terminée : {quest_id}")
        else:
            print(f"[Jeu] Tentative de terminer une quête non active : {quest_id}")

    def return_quest(self, quest_id: str):
        completed = self.get_var("completed_quests", [])
        returned = self.get_var("returned_quests", [])
        
        # Only return if currently completed
        if quest_id in completed:
            completed.remove(quest_id)
            self.set_var("completed_quests", completed)
            
            if quest_id not in returned:
                returned.append(quest_id)
                self.set_var("returned_quests", returned)
                print(f"[Jeu] Quête rendue : {quest_id}")
        else:
            print(f"[Jeu] Tentative de rendre une quête non terminée : {quest_id}")

    def show_quest(self, quest_id: str):
        self.set_var("active_quest_offer", quest_id)
        print(f"[Jeu] Proposition de quête : {quest_id}")

    def hide_quest_offer(self):
        self.set_var("active_quest_offer", None)

    def equip_item(self, item_id: str, slot: str):
        equipped = self.get_var("equipped", {})
        if not isinstance(equipped, dict): equipped = {}
        else: equipped = equipped.copy()
        if slot in equipped:
            pass
        equipped[slot] = item_id
        self.set_var("equipped", equipped)
        print(f"[Jeu] Item équipé : {item_id} sur {slot}")

    def unequip_item(self, slot: str):
        equipped = self.get_var("equipped", {})
        if not isinstance(equipped, dict): equipped = {}
        else: equipped = equipped.copy()
        if slot in equipped:
            del equipped[slot]
            self.set_var("equipped", equipped)
            print(f"[Jeu] Item déséquipé du slot {slot}")

    def mark_choice_used(self, choice_id: str):
        used = self.get_var("used_choices", [])
        if not isinstance(used, list): used = []
        else: used = list(used)
        if choice_id not in used:
            used.append(choice_id)
            self.set_var("used_choices", used)

    def is_choice_used(self, choice_id: str) -> bool:
        used = self.get_var("used_choices", [])
        if not isinstance(used, list): return False
        return choice_id in used

    def set_node_text(self, node_id: str, text: str):
        overrides = self.get_var("node_text_overrides", {})
        if not isinstance(overrides, dict): overrides = {}
        else: overrides = overrides.copy()
        overrides[node_id] = text
        self.set_var("node_text_overrides", overrides)

    def get_node_text(self, node_id: str) -> Optional[str]:
        overrides = self.get_var("node_text_overrides", {})
        if not isinstance(overrides, dict): return None
        return overrides.get(node_id)

    def increment_visit_count(self, node_id: str):
        visits = self.get_var("visit_counts", {})
        if not isinstance(visits, dict): visits = {}
        else: visits = visits.copy()
        current = visits.get(node_id, 0)
        visits[node_id] = current + 1
        self.set_var("visit_counts", visits)
        
    def get_visit_count(self, node_id: str) -> int:
        visits = self.get_var("visit_counts", {})
        if not isinstance(visits, dict): return 0
        return visits.get(node_id, 0)