from PyQt6.QtWidgets import QGraphicsView, QMenu, QInputDialog, QApplication, QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox, QGraphicsTextItem, QGraphicsProxyWidget
from PyQt6.QtCore import Qt, QEvent, QRectF
from PyQt6.QtGui import QPainter, QMouseEvent, QAction, QCursor

from src.editor.graph.scene import NodeScene
from src.editor.graph.node_item import NodeItem
from src.editor.graph.group_item import GroupItem
from src.core.models import NodeModel, NodeType, GroupModel
from src.editor.dialogs.location_dialog import LocationDialog
from src.core.database import DatabaseManager
from src.core.commands import (
    AddNodeCommand, RemoveNodeCommand, MoveNodeCommand, 
    AddGroupCommand, RemoveGroupCommand, BatchEditNodePropertyCommand
)
import uuid

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
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # État interne
        self.mode = MODE_NOOP
        self.zoom_level = 1.0
        self.pan_start_pos = None

        # Database Manager
        self.db_manager = DatabaseManager("game.db")

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

            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """Gestion des raccourcis clavier."""
        # Delete
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selection()
            event.accept()
        
        # Focus Selection (F)
        elif event.key() == Qt.Key.Key_F:
            # 1. Check Widget Focus
            fw = QApplication.focusWidget()
            print(f"DEBUG: 'F' pressed. View: {self} | Focus Widget: {fw} ({type(fw)}) | Viewport: {self.viewport()}")
            
            # If focus is NOT the view/viewport, ignore F.
            if fw is not None and fw is not self and fw is not self.viewport():
                super().keyPressEvent(event)
                return
                # One exception: If the focus widget is a child of the view but NOT an editor?
                # Generally, if focus is elsewhere, don't pan/focus graph.
                super().keyPressEvent(event)
                return

            # Keep type checking just in case (e.g. if fw IS self.viewport but editing an item?)
            if isinstance(fw, (QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox)):
                super().keyPressEvent(event)
                return

            # 2. Check Scene Item Focus (Node Titles, Proxy Widgets, etc.)
            # If ANY item has focus on the scene, we should not steal the keystroke.
            fi = self.scene().focusItem()
            if fi is not None:
                super().keyPressEvent(event)
                return

            self.focus_selection()
            event.accept()
            
        # Select All (Ctrl+A)
        elif event.key() == Qt.Key.Key_A and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            path = QPainterPath()
            path.addRect(self.scene().itemsBoundingRect())
            self.scene().setSelectionArea(path)
            event.accept()
            
        else:
            super().keyPressEvent(event)

    def focus_selection(self):
        """Centre la vue sur la sélection ou sur tout si rien n'est sélectionné."""
        selected = self.scene().selectedItems()
        if selected:
            # Calculate bounding rect of selection
            rect = QRectF()
            for item in selected:
                rect = rect.united(item.sceneBoundingRect())
            self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
            # Zoom out a bit if too close
            if self.transform().m11() > 1.5:
                self.scale(1/self.transform().m11() * 1.5, 1/self.transform().m11() * 1.5)
        else:
            # Fit all
            self.fitInView(self.scene().itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def contextMenuEvent(self, event):
        """Menu contextuel pour supprimer des nœuds."""
        item = self.itemAt(event.pos())
        selected_items = self.scene().selectedItems()
        node_items = [i for i in selected_items if isinstance(i, NodeItem)]
        
        menu = QMenu(self)

        # 1. Actions sur la sélection
        if node_items:
            # Delete
            delete_action = QAction("Supprimer la sélection", self)
            delete_action.triggered.connect(self.delete_selection)
            menu.addAction(delete_action)
            
            menu.addSeparator()
            
            # Alignement (si > 1 nœud)
            if len(node_items) > 1:
                align_h = QAction("Aligner Horizontalement", self)
                align_h.triggered.connect(lambda: self.align_selection("horizontal"))
                menu.addAction(align_h)
                
                align_v = QAction("Aligner Verticalement", self)
                align_v.triggered.connect(lambda: self.align_selection("vertical"))
                menu.addAction(align_v)
            
            menu.addSeparator()
            
            # Logic Exclusif: Groupe OU Lieu Unique
            if len(node_items) >= 1:
                # Set Location (Batch)
                set_location_action = QAction("Définir le lieu (Sélection)", self)
                set_location_action.triggered.connect(self.open_location_dialog)
                menu.addAction(set_location_action)
                
                menu.addSeparator()
                
                # Add Comment (Visual Group)
                comment_action = QAction("Ajouter un commentaire", self)
                comment_action.setShortcut("C")
                comment_action.triggered.connect(self.create_comment_from_selection)
                menu.addAction(comment_action)

        # 2. Actions globales (clic dans le vide ou sur un nœud)
        if not item:
            menu.addSeparator()
            add_action = QAction("Ajouter une Scène ici", self)
            # Capture position for the action
            scene_pos = self.mapToScene(event.pos())
            add_action.triggered.connect(lambda: self.add_node_at_mouse(scene_pos))
            menu.addAction(add_action)
        
        menu.exec(event.globalPos())

    def add_node_at_mouse(self, scene_pos):
        """Crée un nouveau nœud à la position de la souris."""
        if not self.scene().project:
            return
            
        new_id = str(uuid.uuid4())[:8]
        new_node = NodeModel(
            id=new_id,
            title="Nouvelle Scène",
            type=NodeType.DIALOGUE,
            pos_x=scene_pos.x(),
            pos_y=scene_pos.y()
        )
        
        if self.scene().undo_stack is not None:
            cmd = AddNodeCommand(self.scene(), new_node)
            self.scene().undo_stack.push(cmd)
        else:
            self.scene().project.add_node(new_node)
            self.scene().add_node_item(new_node)

    def align_selection(self, direction):
        """Aligne les nœuds sélectionnés."""
        selected_items = self.scene().selectedItems()
        nodes = [i for i in selected_items if isinstance(i, NodeItem)]
        
        if len(nodes) < 2:
            return
            
        if direction == "horizontal":
            # Align to the average Y
            avg_y = sum(n.y() for n in nodes) / len(nodes)
            new_positions = [n.pos() for n in nodes]
            for i, n in enumerate(nodes):
                new_positions[i].setY(avg_y)
                
        elif direction == "vertical":
            # Align to the average X
            avg_x = sum(n.x() for n in nodes) / len(nodes)
            new_positions = [n.pos() for n in nodes]
            for i, n in enumerate(nodes):
                new_positions[i].setX(avg_x)
                
        if self.scene().undo_stack is not None:
            old_positions = [n.pos() for n in nodes]
            cmd = MoveNodeCommand(nodes, new_positions, old_positions)
            self.scene().undo_stack.push(cmd)
        else:
            # Fallback
            for i, n in enumerate(nodes):
                n.setPos(new_positions[i])
                n.model.pos_x = new_positions[i].x()
                n.model.pos_y = new_positions[i].y()
            self.scene().refresh_connections()

    def delete_selection(self):
        """Supprime les éléments sélectionnés de la scène et du modèle."""
        selected = self.scene().selectedItems()
        nodes = [i for i in selected if isinstance(i, NodeItem)]
        groups = [i for i in selected if isinstance(i, GroupItem)]
        
        if self.scene().undo_stack is not None:
            if nodes:
                cmd = RemoveNodeCommand(self.scene(), nodes)
                self.scene().undo_stack.push(cmd)
            if groups:
                cmd = RemoveGroupCommand(self.scene(), groups)
                self.scene().undo_stack.push(cmd)
        else:
            for item in nodes:
                if self.scene().project:
                    self.scene().project.remove_node(item.model.id)
                self.scene().removeItem(item)
            for item in groups:
                if self.scene().project:
                    self.scene().project.remove_group(item.model.id)
                self.scene().removeItem(item)
            
            self.scene().refresh_connections()

    def create_comment_from_selection(self):
        """Crée un groupe visuel (Commentaire) autour des nœuds sélectionnés."""
        selected_items = self.scene().selectedItems()
        nodes = [i for i in selected_items if isinstance(i, NodeItem)]
        
        if not nodes:
            return

        # 1. Calculate Bounding Box
        min_x = min(n.x() for n in nodes)
        min_y = min(n.y() for n in nodes)
        max_x = max(n.x() + n.boundingRect().width() for n in nodes)
        max_y = max(n.y() + n.boundingRect().height() for n in nodes)
        
        padding = 40
        rect = QRectF(min_x - padding, min_y - padding, 
                      (max_x - min_x) + padding*2, (max_y - min_y) + padding*2)

        # 2. Ask for Title
        title, ok = QInputDialog.getText(self, "Nouveau Commentaire", "Titre du groupe :")
        if not ok or not title:
            title = "Commentaire"

        # 3. Create Model
        group_model = GroupModel(
            title=title,
            pos_x=rect.x(),
            pos_y=rect.y(),
            width=rect.width(),
            height=rect.height(),
            color="#444444", # Default comment color
            properties={}
        )
        
        # 4. Add to Project & Scene
        if self.scene().undo_stack is not None:
            cmd = AddGroupCommand(self.scene(), group_model)
            self.scene().undo_stack.push(cmd)
        else:
            if self.scene().project:
                self.scene().project.add_group(group_model)
                self.scene().add_group_item(group_model)
            
        print(f"Comment group created: {title}")

    def open_location_dialog(self):
        """Ouvre le dialogue pour définir le lieu des nœuds sélectionnés."""
        selected_items = self.scene().selectedItems()
        nodes = [i for i in selected_items if isinstance(i, NodeItem)]
        
        if not nodes:
            return
            
        # Use data from the first node as default
        first_node = nodes[0].model
        initial_data = first_node.content.get("coordinates", {})
        
        dialog = LocationDialog(self.db_manager, initial_data, self)
        if dialog.exec():
            data = dialog.get_data()
            
            # Update all selected nodes
            # Update all selected nodes
            if self.scene().undo_stack is not None:
                old_values = {}
                for node in nodes:
                    old_values[node.model.id] = node.model.content.get("coordinates", {}).copy()
                
                # Prepare new value (we need to construct the full dict for each, but here we apply same data)
                # BatchEditNodePropertyCommand expects a single value if property_path is simple, 
                # but for nested dicts we might need to be careful.
                # Actually, our command replaces the target key.
                # Let's use a simpler approach: update the whole 'coordinates' dict.
                
                new_coords = {
                    "continent": data["continent"],
                    "x": data["x"],
                    "y": data["y"],
                    "location_name": data["location_name"],
                    "city": data["city"]
                }
                
                cmd = BatchEditNodePropertyCommand(
                    nodes,
                    "content.coordinates",
                    new_coords,
                    old_values,
                    None # No signal needed as we update visual manually in command
                )
                self.scene().undo_stack.push(cmd)
            else:
                for node_item in nodes:
                    coords = node_item.model.content.get("coordinates", {})
                    coords.update(data)
                    node_item.model.content["coordinates"] = coords
                    node_item.update_location_display()
            
            print(f"Location updated for {len(nodes)} nodes: {data['location_name']}")
            return
        
        # If cancelled, just return
        return


