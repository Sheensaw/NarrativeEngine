
# src/editor/graph/node_item.py
from PyQt6.QtWidgets import (QGraphicsItem, QGraphicsTextItem, QGraphicsProxyWidget, 
                             QTextEdit, QPushButton, QVBoxLayout, QWidget)
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
        # Position initiale
        self.setPos(self.model.pos_x, self.model.pos_y)

        # Expanded Mode State
        self.is_expanded = False
        self.proxy_widget = None
        self.original_z = 0

    def _init_ui(self):
        """Configure les éléments internes (titre, couleurs)."""
        # Location Item (Aesthetic, subtle) - Init first because update_preview uses it
        self._location_item = QGraphicsTextItem(self)
        self._location_item.setDefaultTextColor(QColor("#888888"))
        self._location_item.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal, True)) # Italic
        self._location_item.setVisible(False)

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
                target_id = c.get("target_node_id", "?")
                target_name = target_id
                
                # Try to resolve ID to Title
                if self.scene() and hasattr(self.scene(), "project") and self.scene().project:
                    target_node = self.scene().project.nodes.get(target_id)
                    if target_node:
                        target_name = target_node.title
                    elif target_id:
                        # Shorten ID if not found or no project yet
                        target_name = target_id[:8] + "..."
                elif target_id and len(target_id) > 8:
                     target_name = target_id[:8] + "..."

                preview_text += f"[{i+1}] {c.get('text', 'Choix')} -> {target_name}\n"
            if len(choices) > 3:
                preview_text += "..."
        
        self._preview_item.setPlainText(preview_text)
        
        # Tooltip with full content
        self.setToolTip(content_text)
        
        # Update title if model changed
        if self._title_item.toPlainText() != self.model.title:
            self._title_item.setPlainText(self.model.title)

        # Update Location Display
        self.update_location_display()

    def update_location_display(self):
        """Met à jour l'affichage du lieu."""
        coords = self.model.content.get("coordinates", {})
        loc_name = coords.get("location_name")
        city = coords.get("city")
        
        display_text = ""
        if loc_name:
            display_text = loc_name
            if city:
                display_text = f"{city} - {loc_name}"
        
        if display_text:
            self._location_item.setPlainText(display_text)
            self._location_item.setVisible(True)
            # Position: Bottom Right inside the node
            # Recalculate position based on text width
            rect = self._location_item.boundingRect()
            self._location_item.setPos(self.width - rect.width() - 5, self.height - rect.height() - 5)
        else:
            self._location_item.setVisible(False)

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
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        """Double-clic pour étendre/réduire le nœud."""
        self.toggle_expanded_mode()
        super().mouseDoubleClickEvent(event)

    def toggle_expanded_mode(self):
        """Bascule entre le mode normal et le mode étendu (édition de texte)."""
        if self.is_expanded:
            # Collapse
            self._collapse_node()
        else:
            # Expand
            self._expand_node()

    def _expand_node(self):
        self.is_expanded = True
        self.original_z = self.zValue()
        self.setZValue(100) # Bring to front
        
        # Resize
        self.width = 400
        self.height = 300
        self.update() # Trigger repaint
        
        # Create Editor Widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 35, 5, 5) # Leave space for header
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.model.content.get("text", ""))
        self.text_edit.setStyleSheet("background-color: #333; color: white; border: 1px solid #555;")
        layout.addWidget(self.text_edit)
        
        btn_save = QPushButton("Sauvegarder & Fermer")
        btn_save.setStyleSheet("background-color: #4a90e2; color: white; padding: 5px;")
        btn_save.clicked.connect(self.toggle_expanded_mode)
        layout.addWidget(btn_save)
        
        self.proxy_widget = QGraphicsProxyWidget(self)
        self.proxy_widget.setWidget(container)
        self.proxy_widget.setGeometry(QRectF(0, 0, self.width, self.height))
        
        # Hide preview
        self._preview_item.setVisible(False)

    def _collapse_node(self):
        # Save Content
        if self.proxy_widget:
            new_text = self.text_edit.toPlainText()
            self.model.content["text"] = new_text
            
            # Remove widget
            self.proxy_widget.setWidget(None)
            self.scene().removeItem(self.proxy_widget)
            self.proxy_widget = None
            
        self.is_expanded = False
        self.setZValue(self.original_z)
        
        # Restore Size
        self.width = NODE_WIDTH
        self.height = NODE_HEIGHT
        self.update()
        
        # Show and update preview
        self.update_preview()
        self._preview_item.setVisible(True)
        
        # Notify scene/inspector of change (if connected)
        # Ideally we should emit a signal, but for now the model update is enough
        # The inspector might need to refresh if it's open on this node
        if self.scene():
            # Hacky way to force inspector refresh if we had a signal
            pass
