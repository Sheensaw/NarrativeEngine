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

        # 1. Quitter le nœud actuel
        if self.current_node:
            exit_scripts = self.current_node.logic.get("on_exit", [])
            self.parser.execute_script(exit_scripts)
            self.history.append(self.current_node.id)

        # 2. Changer de nœud
        self.current_node = self.project.nodes[node_id]

        # 3. Entrer dans le nouveau nœud
        enter_scripts = self.current_node.logic.get("on_enter", [])
        self.parser.execute_script(enter_scripts)

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

        # Trouver tous les liens partant de ce nœud
        # On suppose que output_socket_index correspond à l'index du choix
        outgoing_edges = [
            e for e in self.project.edges
            if e.start_node_id == self.current_node.id
        ]

        # Trier par index de socket pour garder l'ordre visuel
        outgoing_edges.sort(key=lambda x: x.start_socket_index)

        for edge in outgoing_edges:
            target_node = self.project.nodes.get(edge.end_node_id)
            if not target_node:
                continue

            # Ici, dans une implémentation avancée, le texte du choix serait stocké
            # soit sur le lien, soit dans une liste "choices" interne au nœud source.
            # Pour ce modèle simplifié, nous allons chercher le texte du choix
            # dans les propriétés du nœud source si disponible, ou utiliser le titre de la cible.

            # Exemple de structure interne de choices dans NodeModel pour Dialogue :
            # "choices": [{"text": "Ouvrir la porte", "condition": "has_key"}, ...]

            node_choices_data = self.current_node.content.get("choices", [])
            choice_data = {}

            # Essayer de mapper l'edge à une donnée de choix
            if len(node_choices_data) > edge.start_socket_index:
                choice_data = node_choices_data[edge.start_socket_index]

            # Vérifier la condition
            condition = choice_data.get("condition", "")
            if not self.parser.evaluate_condition(condition):
                continue  # Choix masqué si condition non remplie

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
            target_id = choices[index]["target_id"]
            self.set_current_node(target_id)