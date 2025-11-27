# src/editor/graph/socket_item.py
from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QBrush, QPen

from src.core.definitions import SocketType, COLORS


class SocketItem(QGraphicsItem):
    """
    Représente un point de connexion (entrée ou sortie) sur un nœud.
    """

    def __init__(self, parent_node, socket_type: SocketType, index: int = 0):
        super().__init__(parent_node)
        self.parent_node = parent_node
        self.socket_type = socket_type
        self.index = index

        # Style
        self.radius = 6.0
        self.outline_width = 1.0
        self._color = QColor(COLORS["socket"])
        self._pen = QPen(QColor("#000000"))
        self._pen.setWidthF(self.outline_width)
        self._brush = QBrush(self._color)

        # Liste des liens connectés (EdgeItems)
        self.edges = []

        # Positionnement local par rapport au nœud parent
        # Sera calculé par le NodeItem lors du layout
        self.setAcceptHoverEvents(True)

    def boundingRect(self) -> QRectF:
        """Zone de dessin du socket."""
        return QRectF(
            -self.radius - self.outline_width,
            -self.radius - self.outline_width,
            2 * (self.radius + self.outline_width),
            2 * (self.radius + self.outline_width)
        )

    def paint(self, painter, option, widget=None):
        """Dessine le cercle."""
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawEllipse(
            -self.radius,
            -self.radius,
            2 * self.radius,
            2 * self.radius
        )

    def get_scene_pos(self):
        """Retourne la position absolue dans la scène (utile pour dessiner les liens)."""
        return self.scenePos()

    def add_edge(self, edge):
        self.edges.append(edge)

    def remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)