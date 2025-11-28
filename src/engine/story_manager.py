# src/engine/story_manager.py
from typing import Optional, List, Dict, Any
from src.core.models import ProjectModel, NodeModel, EdgeModel
from src.core.definitions import NodeType, KEY_LOGIC
from src.engine.variable_store import VariableStore
from src.engine.script_parser import ScriptParser


class StoryManager:
    """
    Contrôleur principal du Runtime (Jeu).
    Gère la navigation entre les nœuds et le cycle de vie du jeu.
    """

    def __init__(self):
        self.project: Optional[ProjectModel] = None
        self.current_node: Optional[NodeModel] = None

        # Sous-systèmes
        self.variables = VariableStore()
        self.parser = ScriptParser(self.variables)

        # Historique pour le bouton "Retour" (Stack)
        self.history: List[str] = []

    def load_project(self, project: ProjectModel):
        """Initialise le moteur avec un projet."""
        self.project = project
        self.variables.load_state(project.variables)  # Charge les valeurs par défaut
        self.current_node = None
        self.history.clear()

    def start_game(self):
        """Lance le jeu en trouvant le premier nœud."""
        if not self.project:
            return

        # Chercher un nœud de type START
        start_node = next((n for n in self.project.nodes.values() if n.type == NodeType.START), None)

        # Sinon, prendre le premier nœud de la liste (fallback)
        if not start_node and self.project.nodes:
            start_node = list(self.project.nodes.values())[0]

        if start_node:
            self.set_current_node(start_node.id)

    def set_current_node(self, node_id: str):
        """
        Transition vers un nouveau nœud.
        Exécute logic.on_exit de l'ancien et logic.on_enter du nouveau.
        """
        if not self.project or node_id not in self.project.nodes:
            print(f"[StoryManager] Nœud introuvable : {node_id}")
            return

        new_node = self.project.nodes[node_id]
        current_title = self.current_node.title if self.current_node else "None"
        print(f"[StoryManager] Navigation: '{current_title}' --> '{new_node.title}'")

        # 1. Quitter le nœud actuel
        if self.current_node:
            # Support Legacy (Text Scripts)
            exit_scripts = self.current_node.logic.get("on_exit", [])
            if isinstance(exit_scripts, list) and exit_scripts and isinstance(exit_scripts[0], str):
                self.parser.execute_script(exit_scripts)
            # Support New (Structured Events)
            elif isinstance(exit_scripts, list):
                self.parser.execute_events(exit_scripts)
            
            self.history.append(self.current_node.id)

        # 2. Changer de nœud
        self.current_node = new_node

        # 3. Entrer dans le nouveau nœud
        enter_scripts = self.current_node.logic.get("on_enter", [])
        # Support Legacy
        if isinstance(enter_scripts, list) and enter_scripts and isinstance(enter_scripts[0], str):
            self.parser.execute_script(enter_scripts)
        # Support New
        elif isinstance(enter_scripts, list):
            self.parser.execute_events(enter_scripts)

        # (L'interface graphique écoutera le changement via current_node et se mettra à jour)

    def get_parsed_text(self) -> str:
        """Retourne le texte du nœud actuel avec les variables remplacées."""
        if not self.current_node:
            return ""
        raw_text = self.current_node.content.get("text", "")
        return self.parser.parse_text(raw_text)

    def get_available_choices(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste des choix valides pour le nœud actuel.
        Vérifie les conditions et trouve les nœuds cibles via les liens (Edges).
        """
        if not self.current_node or not self.project:
            return []

        choices = []

        # Stratégie : 
        # 1. Si le nœud a des choix définis explicitement dans content['choices'], on les utilise.
        # 2. Sinon, on déduit les choix depuis les liens sortants (Legacy/Fallback).

        structured_choices = self.current_node.content.get("choices", [])
        
        if structured_choices:
            # Mode Structuré
            for choice_data in structured_choices:
                choice_id = choice_data.get("id")
                
                # Check One-Shot Logic
                if choice_id and self.variables.is_choice_used(choice_id):
                    after_use = choice_data.get("after_use", "delete")
                    if after_use == "delete":
                        continue
                    elif after_use == "replace":
                        # Use replacement data
                        rep_data = choice_data.get("replacement_data", {})
                        choices.append({
                            "text": rep_data.get("text", "Choix (Remplacement)"),
                            "target_id": rep_data.get("target_node_id"),
                            "original_data": choice_data, # Keep ref if needed
                            "is_replacement": True
                        })
                        continue

                # Normal Choice Logic
                condition = choice_data.get("condition", "")
                if not self.parser.evaluate_condition(condition):
                    continue

                target_id = choice_data.get("target_node_id")
                
                choices.append({
                    "text": choice_data.get("text", "Choix"),
                    "target_id": target_id,
                    "data": choice_data # Pass full data for make_choice
                })
        else:
            # Mode Legacy (Déduction depuis les Edges)
            # Trouver tous les liens partant de ce nœud
            outgoing_edges = [
                e for e in self.project.edges
                if e.start_node_id == self.current_node.id
            ]
            outgoing_edges.sort(key=lambda x: x.start_socket_index)

            for edge in outgoing_edges:
                target_node = self.project.nodes.get(edge.end_node_id)
                if not target_node:
                    continue

                # On essaie de récupérer des infos de choix legacy si elles existent
                node_choices_data = self.current_node.content.get("choices_legacy", [])
                choice_data = {}
                if len(node_choices_data) > edge.start_socket_index:
                    choice_data = node_choices_data[edge.start_socket_index]

                choices.append({
                    "text": choice_data.get("text", f"Vers {target_node.title}"),
                    "target_id": target_node.id,
                    "edge": edge
                })

        return choices

    def make_choice(self, index: int):
        """Le joueur clique sur un choix."""
        choices = self.get_available_choices()
        if 0 <= index < len(choices):
            choice = choices[index]
            
            print(f"[StoryManager] Choice clicked: {choice.get('text')}")
            
            # 1. Execute Events (if any)
            choice_data = choice.get("data", {})
            events = choice_data.get("events", [])
            if events:
                print(f"[StoryManager] Executing choice events: {events}")
                self.parser.execute_events(events)
                
            # 2. Handle One-Shot
            if choice_data.get("is_one_shot"):
                choice_id = choice_data.get("id")
                if choice_id:
                    self.variables.mark_choice_used(choice_id)
            
            # 3. Navigation
            target_id = choice.get("target_id")
            print(f"[StoryManager] Navigating to target_id: {target_id}")
            if target_id:
                self.set_current_node(target_id)
            else:
                 print("[StoryManager] No target_id for this choice.")