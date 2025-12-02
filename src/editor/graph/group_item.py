# src/editor/graph/group_item.py
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsTextItem, QInputDialog
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPen, QBrush, QFont

from src.core.models import GroupModel

class ResizeHandle(QGraphicsRectItem):
    """Poignée de redimensionnement."""
    def __init__(self, parent=None):
        super().__init__(0, 0, 15, 15, parent) # Increased size
        self.setBrush(QBrush(QColor("#ffffff")))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable) # Make selectable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setZValue(10) # Ensure on top
        self.parent_item = parent

    def mousePressEvent(self, event):
        """Accept event explicitly."""
        event.accept()
        super().mousePressEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.parent_item:
                # Limit movement to stay "connected" or just signal parent
                # Actually, simpler: Parent updates handle pos, Handle updates parent size?
                # Let's let handle move freely but constrain it to be > min size relative to parent origin
                new_pos = value
                if new_pos.x() < 50: new_pos.setX(50)
                if new_pos.y() < 50: new_pos.setY(50)
                
                # Update Parent Size
                self.parent_item.resize_to(new_pos.x(), new_pos.y())
                return new_pos
                
        return super().itemChange(change, value)

class GroupItem(QGraphicsRectItem):
    """
    Représentation visuelle d'un groupe de nœuds (Zone).
    """
    HEADER_HEIGHT = 30

    def __init__(self, model: GroupModel, scene=None):
        super().__init__()
        self.model = model
        self.scene_ref = scene
        
        # Flags
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        
        # Geometry
        self.setRect(0, 0, model.width, model.height)
        self.setPos(model.pos_x, model.pos_y)
        self.setZValue(-1) # Behind nodes
        
        # Style
        self.color = QColor(model.color)
        self.color.setAlpha(40) # Semi-transparent background
        self.setBrush(QBrush(self.color))
        
        pen = QPen(QColor(model.color))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        self.setPen(pen)
        
        # Header Text
        self.title_item = QGraphicsTextItem(self)
        self.update_label()
        self.title_item.setDefaultTextColor(QColor("#ffffff"))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self.title_item.setFont(font)
        self.title_item.setPos(5, 2) # Inside header

        # Resize Handle
        self.handle = ResizeHandle(self)
        self.handle.setPos(model.width, model.height)

    def resize_to(self, width, height):
        """Redimensionne le groupe."""
        self.setRect(0, 0, width, height)
        self.model.width = width
        self.model.height = height

    def update_label(self):
        """Met à jour le label affiché (Titre uniquement pour les commentaires)."""
        self.title_item.setPlainText(self.model.title)

    def paint(self, painter, option, widget=None):
        """Dessin personnalisé pour afficher la barre d'en-tête."""
        # 1. Draw Body (Transparent/Dashed)
        super().paint(painter, option, widget)
        
        # 2. Draw Header Bar
        header_rect = QRectF(0, 0, self.rect().width(), self.HEADER_HEIGHT)
        
        # Header Color (Opaque version of group color)
        header_color = QColor(self.model.color)
        header_color.setAlpha(200)
        
        painter.setBrush(QBrush(header_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(header_rect)

    def mousePressEvent(self, event):
        """Capture les nœuds contenus au début du déplacement."""
        # Logic:
        # - If clicking Header -> Move Group (and captured nodes)
        # - If clicking Body -> Ignore event (Pass through to Scene for rubberband selection)
        
        if event.pos().y() > self.HEADER_HEIGHT:
            # Click in Body
            event.ignore()
            return

        # Click in Header -> Start Move
        if self.scene():
            # Find nodes strictly inside the group rect
            rect = self.sceneBoundingRect()
            self.captured_nodes = []
            
            items = self.scene().items(rect, Qt.ItemSelectionMode.ContainsItemShape)
            
            for item in items:
                from src.editor.graph.node_item import NodeItem
                if isinstance(item, NodeItem):
                    # Capture ALL contained nodes
                    self.captured_nodes.append(item)
            
        super().mousePressEvent(event)

    def itemChange(self, change, value):
        """Gère les changements de position/taille."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Calculate delta
            old_pos = self.pos()
            new_pos = value
            delta = new_pos - old_pos
            
            # Update model
            self.model.pos_x = new_pos.x()
            self.model.pos_y = new_pos.y()
            
            # Move captured nodes
            if hasattr(self, 'captured_nodes') and self.captured_nodes:
                for node in self.captured_nodes:
                    if not node.isSelected():
                        node.moveBy(delta.x(), delta.y())
                    
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        """Libère les nœuds capturés."""
        if hasattr(self, 'captured_nodes'):
            self.captured_nodes = []
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Éditer le titre/propriétés au double-clic (Header uniquement)."""
        if event.pos().y() <= self.HEADER_HEIGHT:
            new_title, ok = QInputDialog.getText(None, "Renommer le Groupe", "Nom du lieu:", text=self.model.title)
            if ok and new_title:
                self.model.title = new_title
                self.update_label()
        
        super().mouseDoubleClickEvent(event)
