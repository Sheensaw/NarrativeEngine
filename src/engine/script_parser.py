# src/engine/script_parser.py
import re
from typing import Any, Dict, List
from src.engine.variable_store import VariableStore


class ScriptParser:
    """
    Analyse le texte pour interpoler les variables et évaluer les expressions logiques.
    Sécurisé pour éviter l'exécution de code arbitraire dangereux.
    """

    def __init__(self, variable_store: VariableStore):
        self.store = variable_store
        self.project = None # Pour accéder aux définitions de quêtes/items
        # Regex pour trouver les motifs ${nom_variable}
        self.var_pattern = re.compile(r'\$\{([a-zA-Z0-9_]+)\}')

    def set_project(self, project):
        """Injecte le modèle projet pour accéder aux données statiques (Quêtes, Items)."""
        self.project = project

    def parse_text(self, text: str, extra_context: Dict[str, Any] = None) -> str:
        """
        Remplace les variables dans le texte.
        Ex: "Bonjour ${player_name}" -> "Bonjour Arthur"
        """
        if not text:
            return ""

        def replacer(match):
            var_name = match.group(1)
            # Check extra_context first
            if extra_context and var_name in extra_context:
                return str(extra_context[var_name])
            
            val = self.store.get_var(var_name, f"ERR:{var_name}")
            return str(val)

        return self.var_pattern.sub(replacer, text)

    def evaluate_condition(self, condition: str, extra_context: Dict[str, Any] = None) -> bool:
        """
        Évalue une expression conditionnelle (ex: "gold >= 10 and not is_dead").
        Retourne True ou False.
        """
        if not condition or condition.strip() == "":
            return True

        # On crée un contexte local contenant uniquement les variables du jeu
        # Cela permet d'utiliser "gold" directement au lieu de "variables['gold']"
        context = self.store.get_all()
        
        # Merge extra context (e.g. local variables like 'visits')
        if extra_context:
            context.update(extra_context)

        try:
            # Pre-process condition to allow $variable syntax (replace $var with var)
            # We use the same regex pattern but replace with group 1
            # Note: var_pattern expects ${var}, but conditions usually use $var
            # Let's handle both $var and ${var}
            
            # Replace ${var} -> var
            clean_condition = re.sub(r'\$\{([a-zA-Z0-9_]+)\}', r'\1', condition)
            # Replace $var -> var
            clean_condition = re.sub(r'\$([a-zA-Z0-9_]+)', r'\1', clean_condition)

            # ATTENTION : eval() est puissant mais dangereux.
            # Ici, nous limitons le contexte aux seules variables du jeu.
            # Pour une sécurité totale en prod, il faudrait un parser custom,
            # mais pour un outil desktop créateur, eval restreint est acceptable.
            result = eval(clean_condition, {"__builtins__": {}}, context)
            return bool(result)
        except Exception as e:
            print(f"[ScriptParser] Erreur d'évaluation '{condition}': {e}")
            return False

    def execute_script(self, script_lines: list):
        """
        Exécute une liste de commandes (lignes de texte).
        Supporte les macros Twine-like : <<command arg1 arg2>>
        """
        if not script_lines:
            return

        for line in script_lines:
            if not line or not isinstance(line, str):
                continue
            
            line = line.strip()
            if not line.startswith("<<") or not line.endswith(">>"):
                continue

            # Extraction du contenu : <<addItem "Sword" 1>> -> addItem "Sword" 1
            content = line[2:-2].strip()
            
            # Parsing basique (séparation par espaces, en respectant les guillemets)
            # Regex pour capturer : mot ou "chaine avec espaces"
            # parts = [p.strip('"') for p in re.findall(r'(?:[^\s"]+|"[^"]*")+', content)]
            # Correction regex to handle quotes properly
            parts = [p.strip('"') for p in re.findall(r'(?:[^\s"]+|"[^"]*")+', content)]
            
            if not parts:
                continue

            command = parts[0]
            args = parts[1:]

            self._dispatch_command(command, args)

    def execute_events(self, events: List[Dict]):
        """Exécute une liste d'événements structurés."""
        if not events:
            return

        for event in events:
            if not isinstance(event, dict):
                continue
            
            ev_type = event.get("type")
            params = event.get("parameters", {})
            
            if ev_type:
                self._dispatch_event(ev_type, params)

    def _dispatch_command(self, command: str, args: list):
        """Dispatche la commande textuelle vers la bonne action."""
        try:
            if command == "setVariable" or command == "set":
                if len(args) >= 2:
                    var_name = args[0]
                    value = self._parse_value(args[1])
                    self.store.set_var(var_name, value)
            
            elif command == "addItem":
                if len(args) >= 1:
                    item_id = args[0]
                    qty = int(args[1]) if len(args) > 1 else 1
                    self.store.add_item(item_id, qty)

            elif command == "removeItem":
                if len(args) >= 1:
                    item_id = args[0]
                    qty = int(args[1]) if len(args) > 1 else 1
                    self.store.remove_item(item_id, qty)

            elif command == "startQuest":
                if len(args) >= 1:
                    quest_id = args[0]
                    self.store.start_quest(quest_id)
                    
            elif command == "completeQuest":
                if len(args) >= 1:
                    quest_id = args[0]
                    self.store.complete_quest(quest_id)

            elif command == "showQuest":
                if len(args) >= 1:
                    quest_id = args[0]
                    self.store.show_quest(quest_id)

            elif command == "returnQuest":
                if len(args) >= 1:
                    quest_id = args[0]
                    self._handle_return_quest(quest_id)
                    
            else:
                print(f"[ScriptParser] Commande inconnue : {command}")

        except Exception as e:
            print(f"[ScriptParser] Erreur exécution commande '{command}': {e}")

    def _dispatch_event(self, ev_type: str, params: Dict[str, Any]):
        """Dispatche l'événement structuré vers la bonne action."""
        try:
            if ev_type == "set" or ev_type == "set_variable":
                var_name = params.get("name")
                value = params.get("value")
                if var_name:
                    self.store.set_var(var_name, value)
            
            elif ev_type == "addItem" or ev_type == "add_item":
                item_id = params.get("item_id")
                qty = params.get("qty", params.get("quantity", 1))
                if item_id:
                    self.store.add_item(item_id, qty)
            
            elif ev_type == "removeItem" or ev_type == "remove_item":
                item_id = params.get("item_id")
                qty = params.get("qty", params.get("quantity", 1))
                if item_id:
                    self.store.remove_item(item_id, qty)
            
            elif ev_type == "startQuest" or ev_type == "start_quest":
                quest_id = params.get("quest_id")
                if quest_id:
                    self.store.start_quest(quest_id)
            
            elif ev_type == "completeQuest" or ev_type == "complete_quest":
                quest_id = params.get("quest_id")
                if quest_id:
                    self.store.complete_quest(quest_id)

            elif ev_type == "advanceQuest" or ev_type == "advance_quest":
                quest_id = params.get("quest_id")
                if quest_id:
                    self.store.advance_quest_step(quest_id)

            elif ev_type == "showQuest" or ev_type == "show_quest":
                quest_id = params.get("quest_id")
                if quest_id:
                    self.store.show_quest(quest_id)

            elif ev_type == "returnQuest" or ev_type == "return_quest":
                quest_id = params.get("quest_id")
                if quest_id:
                    self._handle_return_quest(quest_id)
                    
            else:
                print(f"[ScriptParser] Événement inconnu : {ev_type}")

        except Exception as e:
            print(f"[ScriptParser] Erreur exécution événement '{ev_type}': {e}")

    def _handle_return_quest(self, quest_id: str):
        """Gère la logique de rendu de quête (Loot + État)."""
        # 1. Update State
        self.store.return_quest(quest_id)
        
        # 2. Give Loot
        if not self.project:
            print("[ScriptParser] Warning: Project not set, cannot give quest loot.")
            return

        quest = self.project.quests.get(quest_id)
        if not quest:
            print(f"[ScriptParser] Warning: Quest {quest_id} not found.")
            return

        loot = quest.loot
        if not loot: return

        # XP
        xp = loot.get("xp", 0)
        if xp > 0:
            current_xp = self.store.get_var("xp", 0)
            self.store.set_var("xp", current_xp + xp)
            print(f"[Jeu] Gain XP : {xp}")

        # Gold
        gold = loot.get("gold", 0)
        if gold > 0:
            current_gold = self.store.get_var("gold", 0)
            self.store.set_var("gold", current_gold + gold)
            print(f"[Jeu] Gain Or : {gold}")

        # Items
        items = loot.get("items", {})
        for item_id, qty in items.items():
            self.store.add_item(item_id, qty)

    def _parse_value(self, val_str: str) -> Any:
        """Tente de convertir une string en int/float/bool, sinon garde string."""
        if val_str.lower() == "true":
            return True
        if val_str.lower() == "false":
            return False
        
        try:
            return int(val_str)
        except ValueError:
            try:
                return float(val_str)
            except ValueError:
                return val_str