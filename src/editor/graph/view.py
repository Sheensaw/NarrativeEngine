# src/editor/graph/view.py
from PyQt6.QtWidgets import QGraphicsView, QMenu
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPainter, QMouseEvent, QAction, QCursor

from src.editor.graph.scene import NodeScene
from src.editor.graph.node_item import NodeItem

MODE_NOOP = 1
MODE_PANNING = 3

class NodeGraphView(QGraphicsView):
    """
    Vue interactive (Viewport). Gère le zoom, le pan et la sélection.
    """

    def __init__(self, scene: NodeScene, parent=None):
        super().__init__(parent)
        self.setScene(scene)

        # Configuration du rendu pour la qualité
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.TextAntialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )

        # UX
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # État interne
        self.mode = MODE_NOOP
        self.zoom_level = 1.0
        self.pan_start_pos = None

    def wheelEvent(self, event):
        """Zoom avec la molette."""
        zoom_in_factor = 1.15  # Plus doux
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        # Clamp zoom
        new_zoom = self.zoom_level * zoom_factor
        if 0.2 < new_zoom < 3.0:
            self.scale(zoom_factor, zoom_factor)
            self.zoom_level = new_zoom

    def mousePressEvent(self, event: QMouseEvent):
        """Détection du clic pour Pan."""
        # 1. Middle Button -> PAN
        if event.button() == Qt.MouseButton.MiddleButton:
            self.mode = MODE_PANNING
            self.pan_start_pos = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            # Important: on accepte l'event pour ne pas propager
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Mise à jour du Pan ou du Lien."""
        if self.mode == MODE_PANNING:
            delta = event.position().toPoint() - self.pan_start_pos
            self.pan_start_pos = event.position().toPoint()
            
            # Scroll manuel
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Fin du pan."""
        if self.mode == MODE_PANNING:
            self.mode = MODE_NOOP
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        """Menu contextuel pour supprimer des nœuds."""
        item = self.itemAt(event.pos())
        
        # Si on clique sur un nœud ou si des nœuds sont sélectionnés
        selected_items = self.scene().selectedItems()
        
        if not selected_items and not isinstance(item, NodeItem):
            return

        menu = QMenu(self)
        delete_action = QAction("Supprimer la sélection", self)
        delete_action.triggered.connect(self.delete_selection)
        menu.addAction(delete_action)
        
        menu.exec(event.globalPos())

    def delete_selection(self):
        """Supprime les éléments sélectionnés de la scène et du modèle."""
        for item in self.scene().selectedItems():
            if isinstance(item, NodeItem):
                # Supprimer du modèle
                if self.scene().project:
                    self.scene().project.remove_node(item.model.id)
                # Supprimer de la scène
                self.scene().removeItem(item)
        
        # Refresh connections after deletion
        self.scene().refresh_connections()