# src/editor/graph/node_item.py
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsProxyWidget
from PyQt6.QtCore import QRectF, Qt, QPointF
from PyQt6.QtGui import QColor, QPen, QBrush, QFont, QPainterPath

from src.core.definitions import NodeType, SocketType, COLORS, NODE_WIDTH, NODE_HEIGHT
from src.core.models import NodeModel
from src.editor.graph.socket_item import SocketItem


class NodeItem(QGraphicsItem):
    """
    Représentation graphique d'un nœud (NodeModel).
    Gère le dessin, les interactions souris et les sockets enfants.
    """

    def __init__(self, model: NodeModel):
        super().__init__()
        self.model = model

        # Drapeaux PyQt pour l'interaction
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.width = NODE_WIDTH
        self.height = NODE_HEIGHT
        self.radius = 10.0  # Coins arrondis

        # Initialisation UI
        self._title_item = QGraphicsTextItem(self)
        self._init_ui()
        self._init_sockets()

        # Position initiale
        self.setPos(self.model.pos_x, self.model.pos_y)

    def _init_ui(self):
        """Configure les éléments internes (titre, couleurs)."""
        # Titre
        self._title_item.setPlainText(self.model.title)
        self._title_item.setDefaultTextColor(QColor("#ffffff"))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self._title_item.setFont(font)
        self._title_item.setPos(10, 5)

        # Couleur header selon le type
        self.header_color = QColor(COLORS.get(self.model.type, COLORS[NodeType.DIALOGUE]))
        self.bg_color = QColor(COLORS["node_bg"])

    def _init_sockets(self):
        """Crée les sockets d'entrée/sortie."""
        self.inputs = []
        self.outputs = []

        # Par défaut, 1 Entrée
        self.add_socket(SocketType.INPUT)

        # Par défaut, 1 Sortie (plus pour les nœuds de dialogue avec choix multiples)
        # Note: Pour un vrai système dynamique, le nombre de sorties dépendrait des choix
        self.add_socket(SocketType.OUTPUT)

    def add_socket(self, socket_type: SocketType):
        socket = SocketItem(self, socket_type, index=len(self.outputs) if socket_type == SocketType.OUTPUT else 0)

        if socket_type == SocketType.INPUT:
            self.inputs.append(socket)
        else:
            self.outputs.append(socket)

        self._layout_sockets()
        return socket

    def _layout_sockets(self):
        """Place géométriquement les sockets sur les bords."""
        # Inputs à gauche
        y_start = 40  # Sous le header
        spacing = 25

        for i, sock in enumerate(self.inputs):
            sock.setPos(0, y_start + i * spacing + spacing / 2)

        # Outputs à droite
        for i, sock in enumerate(self.outputs):
            sock.setPos(self.width, y_start + i * spacing + spacing / 2)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget=None):
        """Dessine le nœud (Fond, Header, Bordure)."""

        # 1. Corps (Body)
        path_body = QPainterPath()
        path_body.addRoundedRect(0, 0, self.width, self.height, self.radius, self.radius)
        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path_body)

        # 2. En-tête (Header)
        path_header = QPainterPath()
        path_header.setFillRule(Qt.FillRule.WindingFill)
        path_header.addRoundedRect(0, 0, self.width, 30, self.radius, self.radius)
        # Astuce: On redessine le bas du header en rectangle pour "effacer" l'arrondi du bas
        path_header.addRect(0, 20, self.width, 10)

        painter.setBrush(QBrush(self.header_color))
        painter.drawPath(path_header.simplified())  # simplified fusionne le rect et le rounded

        # 3. Bordure (Sélection)
        if self.isSelected():
            painter.setPen(QPen(QColor(COLORS["node_border_selected"]), 2.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(0, 0, self.width, self.height, self.radius, self.radius)
        else:
            painter.setPen(QPen(QColor(COLORS["node_border_default"]), 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(0, 0, self.width, self.height, self.radius, self.radius)

    def itemChange(self, change, value):
        """Callback QT quand l'item change (ex: déplacement)."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Mettre à jour les liens connectés
            self._update_connected_edges()

            # Mettre à jour le modèle de données (Data sync)
            self.model.pos_x = value.x()
            self.model.pos_y = value.y()

        return super().itemChange(change, value)

    def _update_connected_edges(self):
        """Force le redessin de tous les câbles attachés."""
        for sock in self.inputs + self.outputs:
            for edge in sock.edges:
                edge.update_path()