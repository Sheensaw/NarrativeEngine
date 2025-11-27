# src/editor/graph/view.py
from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPainter, QMouseEvent

from src.core.models import EdgeModel
from src.core.definitions import SocketType
from src.editor.graph.scene import NodeScene
from src.editor.graph.socket_item import SocketItem
from src.editor.graph.edge_item import EdgeItem

MODE_NOOP = 1
MODE_EDGE_DRAG = 2


class NodeGraphView(QGraphicsView):
    """
    Vue interactive (Viewport). Gère le zoom, le pan et la création de liens à la souris.
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

        # Gestion du Drag & Drop de lien
        self.drag_edge: EdgeItem = None
        self.drag_start_socket: SocketItem = None

    def wheelEvent(self, event):
        """Zoom avec la molette."""
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        # Sauvegarde de la position souris pour zoomer vers le curseur
        old_pos = self.mapToScene(event.position().toPoint())

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)
        self.zoom_level *= zoom_factor

        # Clamp zoom (optionnel)
        # if self.zoom_level < 0.2: ...

    def mousePressEvent(self, event: QMouseEvent):
        """Détection du clic sur un socket pour commencer un lien."""
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.position().toPoint())

            # Si on clique sur un Socket, on passe en mode Création de Lien
            if isinstance(item, SocketItem):
                self.mode = MODE_EDGE_DRAG
                self.drag_start_socket = item
                self.drag_edge = EdgeItem(item, None)  # Edge fantôme
                self.scene().addItem(self.drag_edge)
                # On désactive le drag de sélection standard de la vue
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
                return  # On consomme l'événement

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Mise à jour du lien fantôme."""
        if self.mode == MODE_EDGE_DRAG and self.drag_edge:
            pos = self.mapToScene(event.position().toPoint())
            self.drag_edge.set_destination(pos)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Fin du drag : validation ou annulation du lien."""
        if self.mode == MODE_EDGE_DRAG and self.drag_edge:
            # On cherche ce qu'il y a sous la souris au relâchement
            item = self.itemAt(event.position().toPoint())

            # Validation de la connexion
            if isinstance(item, SocketItem) and self.is_connection_valid(self.drag_start_socket, item):
                self.create_connection(self.drag_start_socket, item)

            # Nettoyage du lien fantôme
            self.scene().removeItem(self.drag_edge)
            self.drag_edge = None
            self.drag_start_socket = None
            self.mode = MODE_NOOP
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            return

        super().mouseReleaseEvent(event)

    def is_connection_valid(self, start: SocketItem, end: SocketItem) -> bool:
        """Règles logiques de connexion."""
        if start == end: return False
        if start.parent_node == end.parent_node: return False  # Pas de boucle sur soi-même
        if start.socket_type == end.socket_type: return False  # Pas de Input -> Input
        return True

    def create_connection(self, start: SocketItem, end: SocketItem):
        """Crée le lien final (Modèle + Visuel)."""
        # 1. Normaliser : toujours du Output vers Input pour le modèle
        if start.socket_type == SocketType.OUTPUT:
            output_sock, input_sock = start, end
        else:
            output_sock, input_sock = end, start

        # 2. Créer le modèle de données
        edge_model = EdgeModel(
            start_node_id=output_sock.parent_node.model.id,
            end_node_id=input_sock.parent_node.model.id,
            start_socket_index=output_sock.index,
            end_socket_index=input_sock.index
        )

        # 3. Ajouter au Projet (Modèle)
        # Note: self.scene().project est accessible car on l'a défini dans scene.py
        if self.scene().project:
            self.scene().project.add_edge(edge_model)

        # 4. Ajouter à la Scène (Visuel)
        # On délègue à la scène pour garder la cohérence
        self.scene().add_edge_item(edge_model)