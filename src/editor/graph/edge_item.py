# src/editor/graph/edge_item.py
from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPen, QColor, QPainterPath

from src.core.definitions import COLORS


class EdgeItem(QGraphicsPathItem):
    """
    Représente visuellement une connexion entre deux Sockets (Courbe de Bézier).
    """

    def __init__(self, source_socket, target_socket=None):
        super().__init__()
        self.source_socket = source_socket
        self.target_socket = target_socket

        # Configuration visuelle
        self._color = QColor(COLORS["connection"])
        self._pen = QPen(self._color)
        self._pen.setWidthF(2.0)
        self.setPen(self._pen)
        self.setZValue(-1)  # En arrière-plan derrière les nœuds

        # Position temporaire pour le drag & drop (si pas encore de cible)
        self.pos_destination = QPointF(0, 0)

        self.update_path()

    def set_destination(self, pos: QPointF):
        """Utilisé lors du tracé manuel du lien (suivre la souris)."""
        self.pos_destination = pos
        self.update_path()

    def set_target(self, socket):
        """Connecte définitivement à un socket cible."""
        self.target_socket = socket
        self.update_path()

    def update_path(self):
        """Recalcule la courbe de Bézier."""
        if not self.source_socket:
            return

        source_pos = self.source_socket.get_scene_pos()

        if self.target_socket:
            end_pos = self.target_socket.get_scene_pos()
        else:
            end_pos = self.pos_destination

        path = QPainterPath(source_pos)

        # Calcul des points de contrôle pour une courbe fluide (Tangente horizontale)
        dist_x = end_pos.x() - source_pos.x()
        dist_y = end_pos.y() - source_pos.y()

        # On force la courbure en fonction de la distance
        tangent_length = min(abs(dist_x) * 0.5 + abs(dist_y) * 0.1, 150.0)
        # Si les points sont très proches, on évite les boucles bizarres
        if abs(dist_x) < 50: tangent_length = 50

        ctrl1 = QPointF(source_pos.x() + tangent_length, source_pos.y())
        ctrl2 = QPointF(end_pos.x() - tangent_length, end_pos.y())

        path.cubicTo(ctrl1, ctrl2, end_pos)
        self.setPath(path)