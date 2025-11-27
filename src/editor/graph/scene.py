# src/editor/graph/scene.py
import math
from typing import Optional

from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtCore import Qt, QRectF, QLineF
from PyQt6.QtGui import QColor, QPen, QPainter

from src.core.definitions import COLORS, SocketType
from src.core.models import ProjectModel, NodeModel, EdgeModel
from src.editor.graph.node_item import NodeItem
from src.editor.graph.edge_item import EdgeItem
from src.editor.graph.socket_item import SocketItem


class NodeScene(QGraphicsScene):
    """
    Gère le contenu du graphe : Nœuds, Liens et Grille de fond.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project: Optional[ProjectModel] = None

        # Configuration de la scène
        self.scene_width = 64000
        self.scene_height = 64000
        self.setSceneRect(-self.scene_width // 2, -self.scene_height // 2, self.scene_width, self.scene_height)

        # Style de la grille
        self.grid_size = 20
        self.grid_squares = 5  # Lignes fortes tous les 5 carrés
        self._color_bg = QColor(COLORS["grid_bg"])
        self._pen_light = QPen(QColor(COLORS["grid_lines_light"]))
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(QColor(COLORS["grid_lines_dark"]))
        self._pen_dark.setWidth(2)

        self.setBackgroundBrush(self._color_bg)

    def set_project(self, project: ProjectModel):
        """Charge un projet et peuple la scène."""
        self.clear()
        self.project = project

        # Dictionnaire temporaire pour relier les sockets lors de la création des liens
        # Structure: {node_id: NodeItem}
        self.node_map = {}

        # 1. Créer les nœuds
        for node_model in project.nodes.values():
            self.add_node_item(node_model)

        # 2. Créer les liens
        for edge_model in project.edges:
            self.add_edge_item(edge_model)

    def add_node_item(self, model: NodeModel):
        """Crée et ajoute un item de nœud."""
        item = NodeItem(model)
        self.addItem(item)
        self.node_map[model.id] = item
        return item

    def add_edge_item(self, model: EdgeModel):
        """Crée et ajoute un item de lien (connecte visuellement les sockets)."""
        source_item = self.node_map.get(model.start_node_id)
        target_item = self.node_map.get(model.end_node_id)

        if not source_item or not target_item:
            return

        # Récupération des sockets spécifiques par index
        # Sécurité : on vérifie que l'index existe
        if model.start_socket_index < len(source_item.outputs):
            src_sock = source_item.outputs[model.start_socket_index]
        else:
            return  # Index invalide

        if model.end_socket_index < len(target_item.inputs):
            dst_sock = target_item.inputs[model.end_socket_index]
        else:
            return

        # Création visuelle
        edge = EdgeItem(src_sock, dst_sock)
        self.addItem(edge)

        # Enregistrement logique dans les sockets
        src_sock.add_edge(edge)
        dst_sock.add_edge(edge)

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