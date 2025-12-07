# src/engine/story_manager.py
from typing import Optional, List, Dict, Any
import math
import os
import json
import glob
from src.core.models import ProjectModel, NodeModel, EdgeModel
from src.core.definitions import NodeType, KEY_LOGIC
from src.engine.variable_store import VariableStore
from src.engine.script_parser import ScriptParser
from src.core.lore_manager import LoreManager


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
        self.history = []
        
        # Lore Manager
        # Hardcoded path for now as per view.py
        if not self.project:
            return

        # Chercher un nœud de type START
        start_node = next((n for n in self.project.nodes.values() if n.type == NodeType.START), None)

        # Sinon, prendre le premier nœud de la liste (fallback)
        if not start_node and self.project.nodes:
            start_node = list(self.project.nodes.values())[0]

        if start_node:
            self.set_current_node(start_node.id)

    def load_project(self, project: ProjectModel):
        """Charge un projet et initialise l'état."""
        self.project = project
        self.variables.load_state(project.variables)
        self.parser.set_project(project)
        
        # Initialize LoreManager if it exists
        if hasattr(self, 'lore_manager'):
             self.lore_manager.set_project(project)

        self.current_node = None
        self.history.clear()
        
        # Find start node
        start_node = next((n for n in self.project.nodes.values() if n.type == NodeType.START), None)
        if not start_node and self.project.nodes:
            start_node = list(self.project.nodes.values())[0]
            
        if start_node:
            self.set_current_node(start_node.id)

    def start_game(self):
        """Démarre le jeu en trouvant le nœud de départ."""
        if not self.project: return

        # Find start node
        start_node = next((n for n in self.project.nodes.values() if n.type == NodeType.START), None)
        if not start_node and self.project.nodes:
            start_node = list(self.project.nodes.values())[0]
            
        if start_node:
            self.set_current_node(start_node.id)
        else:
            print("[StoryManager] Aucun nœud de départ trouvé.")

    def set_current_node(self, node_id: str):
        """
        Transition vers un nouveau nœud.
        Exécute les scripts de sortie de l'ancien et d'entrée du nouveau.
        """
        if not self.project:
            return

        new_node = self.project.nodes.get(node_id)
        if not new_node:
            print(f"[StoryManager] Erreur: Nœud {node_id} introuvable.")
            return

        # 1. Quitter l'ancien nœud
        if self.current_node:
            exit_scripts = self.current_node.logic.get("on_exit", [])
            # Support Legacy
            if isinstance(exit_scripts, list) and exit_scripts and isinstance(exit_scripts[0], str):
                self.parser.execute_script(exit_scripts)
            # Support New (Structured Events)
            elif isinstance(exit_scripts, list):
                self.parser.execute_events(exit_scripts)
            
            self.history.append(self.current_node.id)

        # 2. Changer de nœud
        self.current_node = new_node
        
        # Increment Visit Count
        self.variables.increment_visit_count(new_node.id)

        # Sync Player Coordinates (if present in node)
        coords = new_node.content.get("coordinates")
        if coords and isinstance(coords, dict):
            x = coords.get("x", 0)
            y = coords.get("y", 0)
            continent = coords.get("continent", "Eldaron")
            city = coords.get("city")
            location_name = coords.get("location_name")
            
            # Update VariableStore
            current_coords = self.variables.get_var("player_coordinates", {})
            current_coords["x"] = x
            current_coords["y"] = y
            current_coords["continent"] = continent
            self.variables.set_var("player_coordinates", current_coords)
            
            # Update Location Description (Near/At)
            self._update_location_description(x, y, continent, city, location_name)

        # 3. Entrer dans le nouveau nœud
        enter_scripts = self.current_node.logic.get("on_enter", [])
        # Support Legacy
        if isinstance(enter_scripts, list) and enter_scripts and isinstance(enter_scripts[0], str):
            self.parser.execute_script(enter_scripts)
        # Support New (Structured Events)
        elif isinstance(enter_scripts, list):
            self.parser.execute_events(enter_scripts)

    def _update_location_description(self, x: float, y: float, continent: str, explicit_city=None, explicit_name=None):
        """Calcule la description du lieu en se basant sur les données Lore (JSON) ou les données explicites."""
        
        # 1. Use Explicit Data if available
        if explicit_city and explicit_name:
            self.variables.set_var("location_text", f"{continent} - {explicit_name}")
            self.variables.set_var("location_continent", continent)
            self.variables.set_var("location_city", explicit_city)
            self.variables.set_var("location_name", explicit_name)
            return

        # 2. Fallback to Lore Calculation
        closest_node = None
        min_dist = float('inf')

        # Use Lore Manager Locations
        if self.lore_manager:
            closest_node = self.lore_manager.get_location_at(x, y, continent)
            if closest_node:
                nx = closest_node.get("x", 0)
                ny = closest_node.get("y", 0)
                min_dist = math.sqrt((x - nx)**2 + (y - ny)**2)

        location_text = f"{continent} - Terres Sauvages"
        city_name = "Terres Sauvages"
        loc_name = "Inconnu"
        
        if closest_node:
            # New Structure: explicit 'city' and 'place' fields
            city_field = closest_node.get("city")
            place_field = closest_node.get("place")
            
            # Fallback to 'main_location_name' if 'city' is missing
            if not city_field:
                city_field = closest_node.get("main_location_name")
            
            # Fallback to 'name' if 'place' is missing
            if not place_field:
                place_field = closest_node.get("name", "Lieu Inconnu")

            if city_field:
                city_name = city_field
            
            if place_field:
                loc_name = place_field

            # Determine HUD Text based on distance
            if min_dist < 0.1:
                # Exact match
                location_text = f"{continent} - {city_name}"
            elif min_dist < 20.0:
                # Nearby
                location_text = f"{continent} - Proche de {city_name}"
                if not loc_name.startswith("Proche de"):
                    loc_name = f"Proche de {loc_name}"
            else:
                # Too far
                location_text = f"{continent} - Terres Sauvages"
                city_name = "Terres Sauvages"
                loc_name = "Nature"
        
        self.variables.set_var("location_text", location_text)
        self.variables.set_var("location_continent", continent)
        self.variables.set_var("location_city", city_name)
        self.variables.set_var("location_name", loc_name)

    def get_parsed_text(self) -> str:
        """Retourne le texte du nœud actuel avec les variables remplacées."""
        if not self.current_node:
            return ""
            
        # Prepare context (e.g. local variables like 'visits')
        context = {
            "visits": self.variables.get_visit_count(self.current_node.id)
        }
            
        # Priority 1: Runtime Override (One-Shot)
        override = self.variables.get_node_text(self.current_node.id)
        if override:
            return self.parser.parse_text(override, context)
            
        # Priority 2: Text Variants
        variants = self.current_node.content.get("text_variants", [])
        if variants:
            for variant in variants:
                condition = variant.get("condition", "")
                if self.parser.evaluate_condition(condition, context):
                    return self.parser.parse_text(variant.get("text", ""), context)
        
        # Priority 3: Default Text
        raw_text = self.current_node.content.get("text", "")
        return self.parser.parse_text(raw_text, context)

    def get_available_choices(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste des choix valides pour le nœud actuel.
        Vérifie les conditions et trouve les nœuds cibles via les liens (Edges).
        """
        if not self.current_node or not self.project:
            return []

        choices = []
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
                        rep_data = choice_data.get("replacement_data", {})
                        choices.append({
                            "text": rep_data.get("text", "Choix (Remplacement)"),
                            "target_id": rep_data.get("target_node_id"),
                            "original_data": choice_data,
                            "is_replacement": True,
                            "disabled": False
                        })
                        continue
                    elif after_use == "disable":
                        choices.append({
                            "text": choice_data.get("text", "Choix (Désactivé)"),
                            "target_id": None,
                            "data": choice_data,
                            "disabled": True
                        })
                        continue
                    elif after_use == "none":
                        pass

                # Condition Check
                condition = choice_data.get("condition", "")
                if not self.parser.evaluate_condition(condition):
                    continue
                
                # --- NEW: Filter startQuest/showQuest events if quest active/done ---
                events = choice_data.get("events", [])
                quest_event = next((e for e in events if e.get("type") in ["startQuest", "start_quest", "showQuest", "show_quest"]), None)
                if quest_event:
                    qid = quest_event.get("parameters", {}).get("quest_id")
                    if qid:
                        active_q = self.variables.get_var("active_quests", [])
                        completed_q = self.variables.get_var("completed_quests", [])
                        returned_q = self.variables.get_var("returned_quests", [])
                        if qid in active_q or qid in completed_q or qid in returned_q:
                            continue

                # Add Choice
                disable_choice = False
                
                choices.append({
                    "text": choice_data.get("text", "Choix"),
                    "target_id": choice_data.get("target_node_id"),
                    "data": choice_data,
                    "disabled": disable_choice
                })

        else:
            # Mode Legacy (Déduction depuis les Edges)
            outgoing_edges = [
                e for e in self.project.edges
                if e.start_node_id == self.current_node.id
            ]
            outgoing_edges.sort(key=lambda x: x.start_socket_index)

            for edge in outgoing_edges:
                target_node = self.project.nodes.get(edge.end_node_id)
                if not target_node:
                    continue

                node_choices_data = self.current_node.content.get("choices_legacy", [])
                choice_data = {}
                if len(node_choices_data) > edge.start_socket_index:
                    choice_data = node_choices_data[edge.start_socket_index]

                choices.append({
                    "text": choice_data.get("text", f"Vers {target_node.title}"),
                    "target_id": target_node.id,
                    "edge": edge,
                    "disabled": False
                })

        # --- NEW: Inject Return Quest Choices ---
        # Check all completed quests (ready to return)
        completed_quests = self.variables.get_var("completed_quests", [])
        returned_quests = self.variables.get_var("returned_quests", [])
        
        if self.project:
            for q_id in completed_quests:
                if q_id in returned_quests: continue
                
                quest = self.project.quests.get(q_id)
                if not quest: continue
                
                # Check if we are at the return scene
                if quest.return_scene_id and quest.return_scene_id == self.current_node.id:
                    choices.append({
                        "text": f"Rendre la quête : {quest.title}",
                        "target_id": None, 
                        "data": {
                            "id": f"return_{q_id}",
                            "text": f"Rendre la quête : {quest.title}",
                            "events": [
                                { "type": "returnQuest", "parameters": { "quest_id": q_id } }
                            ]
                        },
                        "disabled": False
                    })

        return choices

    def make_choice(self, index: int):
        """Le joueur clique sur un choix."""
        choices = self.get_available_choices()
        if 0 <= index < len(choices):
            choice = choices[index]
            
            # Ignore disabled choices
            if choice.get("disabled"):
                print("[StoryManager] Choice is disabled.")
                return {"navigated": False, "text_modified": False}

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
                    
            # 3. Handle Text Modification (Independent of Action)
            if choice_data.get("modify_text_enabled"):
                new_text = choice_data.get("new_scene_text")
                if new_text and self.current_node:
                    print(f"[StoryManager] Modifying text for node {self.current_node.id}")
                    self.variables.set_node_text(self.current_node.id, new_text)
            
            # 4. Navigation
            target_id = choice.get("target_id")
            print(f"[StoryManager] Navigating to target_id: {target_id}")
            
            navigated = False
            if target_id:
                self.set_current_node(target_id)
                navigated = True
            else:
                 print("[StoryManager] No target_id for this choice.")
                 
            return {
                "navigated": navigated,
                "text_modified": choice_data.get("modify_text_enabled", False)
            }
        return {"navigated": False, "text_modified": False}