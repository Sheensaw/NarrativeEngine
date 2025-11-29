
# src/editor/graph/node_item.py
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPen, QBrush, QFont, QPainterPath

from src.core.definitions import NodeType, COLORS, NODE_WIDTH, NODE_HEIGHT
from src.core.models import NodeModel


class NodeItem(QGraphicsItem):
    """
    Représentation graphique d'un nœud (NodeModel).
    Gère le dessin, les interactions souris et les connexions dynamiques.
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
        self.radius = 8.0 

        # Initialisation UI
        self._title_item = QGraphicsTextItem(self)
        self._preview_item = QGraphicsTextItem(self)
        self._init_ui()
        
        # Track connected edges to update them when moving
        self.edges = []

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

        # Preview Content
        self.update_preview()
        self._preview_item.setDefaultTextColor(QColor("#aaaaaa"))
        self._preview_item.setFont(QFont("Segoe UI", 9))
        self._preview_item.setPos(10, 40)
        self._preview_item.setTextWidth(self.width - 20)

        # Couleur header selon le type
        self.header_color = QColor(COLORS.get(self.model.type, COLORS[NodeType.DIALOGUE]))
        self.bg_color = QColor(COLORS["node_bg"])

    def update_preview(self):
        """Met à jour le texte de prévisualisation (Contenu + Choix)."""
        content_text = self.model.content.get("text", "")
        # Truncate content
        preview_text = (content_text[:50] + '...') if len(content_text) > 50 else content_text
        
        # Add Choices
        choices = self.model.content.get("choices", [])
        if choices:
            preview_text += "\n\n"
            for i, c in enumerate(choices[:3]): # Max 3 choices in preview
                target = c.get("target_node_id", "?")
                preview_text += f"[{i+1}] {c.get('text', 'Choix')} -> {target}\n"
            if len(choices) > 3:
                preview_text += "..."
        
        self._preview_item.setPlainText(preview_text)
        
        # Update title if model changed
        if self._title_item.toPlainText() != self.model.title:
            self._title_item.setPlainText(self.model.title)

    def add_edge(self, edge):
        if edge not in self.edges:
            self.edges.append(edge)

    def remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget=None):
        """Dessine le nœud."""
        # 1. Corps (Body) - Fond général
        path_body = QPainterPath()
        path_body.addRoundedRect(0, 0, self.width, self.height, self.radius, self.radius)
        
        # Gradient background? For now simple flat color is cleaner
        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path_body)

        # 2. En-tête (Header)
        path_header = QPainterPath()
        path_header.setFillRule(Qt.FillRule.WindingFill)
        path_header.addRoundedRect(0, 0, self.width, 30, self.radius, self.radius)
        path_header.addRect(0, 20, self.width, 10) # Cover bottom corners of header

        painter.setBrush(QBrush(self.header_color))
        painter.drawPath(path_header)

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
            # Mettre à jour le modèle de données (Data sync)
            self.model.pos_x = value.x()
            self.model.pos_y = value.y()
            
            # Update connected edges
            for edge in self.edges:
                edge.update_path()

        return super().itemChange(change, value)
