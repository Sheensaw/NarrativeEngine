from PyQt6.QtGui import QUndoCommand
from src.core.models import NodeModel, NodeType
import uuid

class MoveNodeCommand(QUndoCommand):
    """Commande pour déplacer un ou plusieurs nœuds."""
    def __init__(self, nodes, new_positions, old_positions):
        super().__init__("Déplacer nœud(s)")
        self.nodes = nodes # List of NodeItems
        self.new_positions = new_positions # List of QPointF
        self.old_positions = old_positions # List of QPointF

    def redo(self):
        for i, node in enumerate(self.nodes):
            pos = self.new_positions[i]
            node.setPos(pos)
            node.model.pos_x = pos.x()
            node.model.pos_y = pos.y()

    def undo(self):
        for i, node in enumerate(self.nodes):
            pos = self.old_positions[i]
            node.setPos(pos)
            node.model.pos_x = pos.x()
            node.model.pos_y = pos.y()

class AddNodeCommand(QUndoCommand):
    """Commande pour ajouter un nœud."""
    def __init__(self, scene, node_model):
        super().__init__("Ajouter nœud")
        self.scene = scene
        self.node_model = node_model
        self.node_item = None

    def redo(self):
        # Add to project
        if self.scene.project:
            self.scene.project.add_node(self.node_model)
        # Add to scene
        self.node_item = self.scene.add_node_item(self.node_model)
        self.scene.refresh_connections()

    def undo(self):
        # Remove from scene
        if self.node_item:
            self.scene.removeItem(self.node_item)
        # Remove from project
        if self.scene.project:
            self.scene.project.remove_node(self.node_model.id)
        self.scene.refresh_connections()

class RemoveNodeCommand(QUndoCommand):
    """Commande pour supprimer un ou plusieurs nœuds."""
    def __init__(self, scene, node_items):
        super().__init__("Supprimer nœud(s)")
        self.scene = scene
        self.node_items = node_items
        self.node_models = [item.model for item in node_items]

    def redo(self):
        for item in self.node_items:
            if self.scene.project:
                self.scene.project.remove_node(item.model.id)
            self.scene.removeItem(item)
        self.scene.refresh_connections()

    def undo(self):
        for model in self.node_models:
            if self.scene.project:
                self.scene.project.add_node(model)
            self.scene.add_node_item(model)
        self.scene.refresh_connections()

class EditNodePropertyCommand(QUndoCommand):
    """Commande générique pour modifier une propriété d'un nœud."""
    def __init__(self, node_model, property_name, new_value, old_value, signal=None):
        super().__init__(f"Modifier {property_name}")
        self.node_model = node_model
        self.property_name = property_name
        self.new_value = new_value
        self.old_value = old_value
        self.signal = signal # Signal to emit after change (e.g. data_changed)

    def redo(self):
        setattr(self.node_model, self.property_name, self.new_value)
        if self.signal:
            self.signal.emit()

    def undo(self):
        setattr(self.node_model, self.property_name, self.old_value)
        if self.signal:
            self.signal.emit()

class ReorderChoicesCommand(QUndoCommand):
    """Commande pour réorganiser les choix."""
    def __init__(self, node_model, new_choices, old_choices, signal=None):
        super().__init__("Réorganiser choix")
        self.node_model = node_model
        self.new_choices = new_choices
        self.old_choices = old_choices
        self.signal = signal

    def redo(self):
        self.node_model.content["choices"] = self.new_choices
        if self.signal:
            self.signal.emit()

    def undo(self):
        self.node_model.content["choices"] = self.old_choices
        if self.signal:
            self.signal.emit()

class EditChoiceCommand(QUndoCommand):
    """Commande pour modifier un choix (ajout/suppression/modif)."""
    def __init__(self, node_model, new_choices, old_choices, signal=None):
        super().__init__("Modifier choix")
        self.node_model = node_model
        self.new_choices = new_choices
        self.old_choices = old_choices
        self.signal = signal

    def redo(self):
        self.node_model.content["choices"] = self.new_choices
        if self.signal:
            self.signal.emit()

    def undo(self):
        self.node_model.content["choices"] = self.old_choices
        if self.signal:
            self.signal.emit()
