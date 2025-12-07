
# src/editor/graph/scene.py
import math
from typing import Optional

from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtCore import Qt, QRectF, QLineF
from PyQt6.QtGui import QColor, QPen, QPainter, QUndoStack

from src.core.definitions import COLORS
from src.editor.graph.node_item import NodeItem
from src.editor.graph.edge_item import EdgeItem
from src.editor.graph.group_item import GroupItem
from src.core.models import ProjectModel, NodeModel, GroupModel
from src.core.commands import MoveNodeCommand


class NodeScene(QGraphicsScene):
    """
    Gère le contenu du graphe : Nœuds, Liens dynamiques et Grille de fond.
    """

    def __init__(self, parent=None, undo_stack: QUndoStack = None):
        super().__init__(parent)
        self.project: Optional[ProjectModel] = None
        self.undo_stack = undo_stack

        # Configuration de la scène
        self.scene_width = 64000
        self.scene_height = 64000
        self.setSceneRect(-self.scene_width // 2, -self.scene_height // 2, self.scene_width, self.scene_height)
        
        # Optimization: NoIndex is faster for dynamic scenes (moving items)
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # Style de la grille
        self.grid_size = 20
        self.grid_squares = 5
        self._color_bg = QColor(COLORS["grid_bg"])
        self._pen_light = QPen(QColor(COLORS["grid_lines_light"]))
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(QColor(COLORS["grid_lines_dark"]))
        self._pen_dark.setWidth(2)

        self.setBackgroundBrush(self._color_bg)
        
        # Map node_id -> NodeItem
        self.node_map = {}
        # List of current edges
        self.edges = []
        
        # Undo/Redo state
        self._start_move_positions = {}

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_move_positions = {}
            for item in self.selectedItems():
                if isinstance(item, (NodeItem, GroupItem)):
                    self._start_move_positions[item] = item.pos()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and hasattr(self, '_start_move_positions') and self._start_move_positions:
            nodes = []
            old_pos_list = []
            new_pos_list = []
            
            for item, old_pos in self._start_move_positions.items():
                # Check if item still exists in scene (it might have been deleted)
                if item.scene() == self and item.pos() != old_pos:
                    nodes.append(item)
                    old_pos_list.append(old_pos)
                    new_pos_list.append(item.pos())
            
            if nodes and self.undo_stack is not None:
                cmd = MoveNodeCommand(nodes, new_pos_list, old_pos_list)
                self.undo_stack.push(cmd)
            
            self._start_move_positions = {}

    def set_project(self, project: ProjectModel):
        """Charge un projet et peuple la scène."""
        self.clear()
        self.project = project
        self.node_map = {}
        self.edges = []

        # 1. Créer les groupes (Background)
        for group_model in project.groups.values():
            self.add_group_item(group_model)

        # 2. Créer les nœuds
        for node_model in project.nodes.values():
            self.add_node_item(node_model)

        # 2. Créer les liens dynamiques
        self.refresh_connections()
        
        # 3. Mettre à jour les prévisualisations (pour résoudre les noms des cibles)
        for item in self.node_map.values():
            item.update_preview()

    def add_node_item(self, model: NodeModel):
        """Crée et ajoute un item de nœud."""
        item = NodeItem(model)
        self.addItem(item)
        self.node_map[model.id] = item
        return item

    def add_group_item(self, model: GroupModel):
        """Crée et ajoute un item de groupe."""
        item = GroupItem(model, self)
        self.addItem(item)
        return item

    def refresh_connections(self):
        """
        Reconstruit tous les liens en fonction des choix des nœuds.
        Gère les liens bidirectionnels.
        """
        # 1. Supprimer les liens existants
        for edge in self.edges:
            self.removeItem(edge)
            # Clean up references in nodes
            if edge.source_node: edge.source_node.remove_edge(edge)
            if edge.target_node: edge.target_node.remove_edge(edge)
        self.edges = []

        if not self.project:
            return

        # 2. Analyser les connexions requises
        # Set of (id1, id2) tuples to track created connections and avoid duplicates
        connections = set()
        
        # Helper to get sorted pair
        def get_pair(id1, id2):
            return tuple(sorted((id1, id2)))

        # Collect all directed links: A -> B
        directed_links = [] # List of (source_id, target_id)
        
        for node_id, node_model in self.project.nodes.items():
            choices = node_model.content.get("choices", [])
            for choice in choices:
                target_id = choice.get("target_node_id")
                if target_id and target_id in self.project.nodes:
                    directed_links.append((node_id, target_id))

        # Process links
        processed_pairs = set()
        
        for src_id, dst_id in directed_links:
            if src_id == dst_id: continue # Ignore self-loops for now or handle differently
            
            pair = get_pair(src_id, dst_id)
            if pair in processed_pairs:
                continue
            
            # Check if it's bidirectional
            # It is if there is also a link dst_id -> src_id
            is_bi = (dst_id, src_id) in directed_links and (src_id, dst_id) in directed_links
            
            src_item = self.node_map.get(src_id)
            dst_item = self.node_map.get(dst_id)
            
            if src_item and dst_item:
                edge = EdgeItem(src_item, dst_item, is_bidirectional=is_bi)
                self.addItem(edge)
                self.edges.append(edge)
                
                src_item.add_edge(edge)
                dst_item.add_edge(edge)
            
            processed_pairs.add(pair)
            

            
        # 3. Update all node previews (to reflect potential title changes in targets)
        for item in self.node_map.values():
            item.update_preview()
            
        self.update()

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Dessine une grille infinie performante."""
        super().drawBackground(painter, rect)

        # Optimisation : on ne dessine que ce qui est visible (rect)
        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        first_left = left - (left % self.grid_size)
        first_top = top - (top % self.grid_size)

        # Lignes verticales et horizontales
        lines_light, lines_dark = [], []

        # Verticales
        for x in range(first_left, right, self.grid_size):
            line = QLineF(x, top, x, bottom)
            if x % (self.grid_size * self.grid_squares) == 0:
                lines_dark.append(line)
            else:
                lines_light.append(line)

        # Horizontales
        for y in range(first_top, bottom, self.grid_size):
            line = QLineF(left, y, right, y)
            if y % (self.grid_size * self.grid_squares) == 0:
                lines_dark.append(line)
            else:
                lines_light.append(line)

        # Dessin
        painter.setPen(self._pen_light)
        painter.drawLines(lines_light)

        painter.setPen(self._pen_dark)
        painter.drawLines(lines_dark)
