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
        # Regex pour trouver les motifs ${nom_variable}
        self.var_pattern = re.compile(r'\$\{([a-zA-Z0-9_]+)\}')

    def parse_text(self, text: str) -> str:
        """
        Remplace les variables dans le texte.
        Ex: "Bonjour ${player_name}" -> "Bonjour Arthur"
        """
        if not text:
            return ""

        def replacer(match):
            var_name = match.group(1)
            val = self.store.get_var(var_name, f"ERR:{var_name}")
            return str(val)

        return self.var_pattern.sub(replacer, text)

    def evaluate_condition(self, condition: str) -> bool:
        """
        Évalue une expression conditionnelle (ex: "gold >= 10 and not is_dead").
        Retourne True ou False.
        """
        if not condition or condition.strip() == "":
            return True

        # On crée un contexte local contenant uniquement les variables du jeu
        # Cela permet d'utiliser "gold" directement au lieu de "variables['gold']"
        context = self.store.get_all()

        try:
            # ATTENTION : eval() est puissant mais dangereux.
            # Ici, nous limitons le contexte aux seules variables du jeu.
            # Pour une sécurité totale en prod, il faudrait un parser custom,
            # mais pour un outil desktop créateur, eval restreint est acceptable.
            result = eval(condition, {"__builtins__": {}}, context)
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
            if command == "setVariable":
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
                    
            else:
                print(f"[ScriptParser] Commande inconnue : {command}")

        except Exception as e:
            print(f"[ScriptParser] Erreur exécution commande '{command}': {e}")

    def _dispatch_event(self, ev_type: str, params: dict):
        """Dispatche l'événement structuré vers la bonne action."""
        try:
            print(f"[ScriptParser] Dispatching event: {ev_type} with params: {params}")
            
            if ev_type == "set":
                var = params.get("variable")
                val = params.get("value")
                if var:
                    self.store.set_var(var, val)
                    
            elif ev_type == "addItem":
                item = params.get("item_id")
                # Check 'quantity' then 'qty', default to 1
                raw_qty = params.get("quantity") or params.get("qty") or 1
                try:
                    qty = int(raw_qty)
                except:
                    qty = 1
                    
                if item:
                    self.store.add_item(item, qty)
            
            elif ev_type == "spawn":
                pnj_id = params.get("pnjId")
                x = params.get("x")
                y = params.get("y")
                print(f"[ScriptParser] Spawning NPC {pnj_id} at ({x}, {y})")
                
            elif ev_type == "movePnj":
                pnj_id = params.get("pnjId")
                target = params.get("targetPassage")
                x = params.get("x")
                y = params.get("y")
                print(f"[ScriptParser] Moving NPC {pnj_id} to {target} at ({x}, {y})")
                
            elif ev_type == "setrelation":
                pnj_id = params.get("pnjId")
                val = params.get("value")
                print(f"[ScriptParser] Setting relation for {pnj_id} to {val}")
                
            elif ev_type == "changemood":
                pnj_id = params.get("pnjId")
                val = params.get("value")
                print(f"[ScriptParser] Changing mood for {pnj_id} to {val}")
                
            # Add other NPC macros here as needed
            
            else:
                print(f"[ScriptParser] Event inconnu ou non implémenté : {ev_type}")
                
        except Exception as e:
            print(f"[ScriptParser] Erreur exécution event '{ev_type}': {e}")

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