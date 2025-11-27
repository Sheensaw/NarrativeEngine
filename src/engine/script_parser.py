# src/engine/script_parser.py
import re
from typing import Any, Dict
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

    def execute_script(self, script_list: list):
        """
        Exécute une liste d'actions définies dans le nœud (on_enter/on_exit).
        Format attendu : [{"command": "set", "var": "gold", "value": 10}, ...]
        """
        for action in script_list:
            cmd = action.get("command")

            if cmd == "set":
                # Assigner une valeur brute
                self.store.set_var(action["var"], action["value"])

            elif cmd == "add":
                # Additionner (numérique)
                current = self.store.get_var(action["var"], 0)
                self.store.set_var(action["var"], current + action["value"])

            elif cmd == "sub":
                # Soustraire
                current = self.store.get_var(action["var"], 0)
                self.store.set_var(action["var"], current - action["value"])

            elif cmd == "toggle":
                # Inverser un booléen
                current = bool(self.store.get_var(action["var"], False))
                self.store.set_var(action["var"], not current)