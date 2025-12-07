from PyQt6.QtGui import QUndoCommand
from src.core.models import NodeModel, NodeType
import uuid

class MoveNodeCommand(QUndoCommand):
    """Commande pour déplacer un ou plusieurs items (Nœuds ou Groupes)."""
    def __init__(self, items, new_positions, old_positions):
        super().__init__("Déplacer élément(s)")
        self.items = items # List of QGraphicsItem (NodeItem or GroupItem)
        self.new_positions = new_positions # List of QPointF
        self.old_positions = old_positions # List of QPointF

    def redo(self):
        for i, item in enumerate(self.items):
            pos = self.new_positions[i]
            item.setPos(pos)
            item.model.pos_x = pos.x()
            item.model.pos_y = pos.y()

    def undo(self):
        for i, item in enumerate(self.items):
            pos = self.old_positions[i]
            item.setPos(pos)
            item.model.pos_x = pos.x()
            item.model.pos_y = pos.y()

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

class AddGroupCommand(QUndoCommand):
    """Commande pour ajouter un groupe (commentaire)."""
    def __init__(self, scene, group_model):
        super().__init__("Ajouter groupe")
        self.scene = scene
        self.group_model = group_model
        self.group_item = None

    def redo(self):
        if self.scene.project:
            self.scene.project.add_group(self.group_model)
        self.group_item = self.scene.add_group_item(self.group_model)

    def undo(self):
        if self.group_item:
            self.scene.removeItem(self.group_item)
        if self.scene.project:
            self.scene.project.remove_group(self.group_model.id)

class RemoveGroupCommand(QUndoCommand):
    """Commande pour supprimer un ou plusieurs groupes."""
    def __init__(self, scene, group_items):
        super().__init__("Supprimer groupe(s)")
        self.scene = scene
        self.group_items = group_items
        self.group_models = [item.model for item in group_items]

    def redo(self):
        for item in self.group_items:
            if self.scene.project:
                self.scene.project.remove_group(item.model.id)
            self.scene.removeItem(item)

    def undo(self):
        for model in self.group_models:
            if self.scene.project:
                self.scene.project.add_group(model)
            self.scene.add_group_item(model)

class BatchEditNodePropertyCommand(QUndoCommand):
    """Commande pour modifier une propriété sur plusieurs nœuds (ex: Lieu)."""
    def __init__(self, nodes, property_path, new_value, old_values, signal=None):
        super().__init__("Modifier propriété (Batch)")
        self.nodes = nodes # List of NodeItems
        self.property_path = property_path # e.g. "content.coordinates"
        self.new_value = new_value
        self.old_values = old_values # Dict {node_id: old_value}
        self.signal = signal

    def redo(self):
        keys = self.property_path.split(".")
        for node in self.nodes:
            target = node.model
            for k in keys[:-1]:
                target = getattr(target, k) if hasattr(target, k) else target.get(k)
            
            last_key = keys[-1]
            if isinstance(target, dict):
                target[last_key] = self.new_value
            else:
                setattr(target, last_key, self.new_value)
            
            # Update visual if needed
            if hasattr(node, 'update_location_display'):
                node.update_location_display()

    def undo(self):
        keys = self.property_path.split(".")
        for node in self.nodes:
            old_val = self.old_values.get(node.model.id)
            target = node.model
            for k in keys[:-1]:
                target = getattr(target, k) if hasattr(target, k) else target.get(k)
            
            last_key = keys[-1]
            if isinstance(target, dict):
                target[last_key] = old_val
            else:
                setattr(target, last_key, old_val)

            if hasattr(node, 'update_location_display'):
                node.update_location_display()

class AddDictItemCommand(QUndoCommand):
    """Generic command to add an item to a dictionary (Items, Quests, Locations, Variables)."""
    def __init__(self, target_dict, key, value, description="Ajouter élément", signal=None):
        super().__init__(description)
        self.target_dict = target_dict
        self.key = key
        self.value = value
        self.signal = signal

    def redo(self):
        self.target_dict[self.key] = self.value
        if self.signal: self.signal.emit()

    def undo(self):
        if self.key in self.target_dict:
            del self.target_dict[self.key]
        if self.signal: self.signal.emit()

class RemoveDictItemCommand(QUndoCommand):
    """Generic command to remove an item from a dictionary."""
    def __init__(self, target_dict, key, description="Supprimer élément", signal=None):
        super().__init__(description)
        self.target_dict = target_dict
        self.key = key
        self.old_value = target_dict.get(key)
        self.signal = signal

    def redo(self):
        if self.key in self.target_dict:
            del self.target_dict[self.key]
        if self.signal: self.signal.emit()

    def undo(self):
        if self.old_value is not None:
            self.target_dict[self.key] = self.old_value
        if self.signal: self.signal.emit()

class EditObjectPropertyCommand(QUndoCommand):
    """Generic command to edit an attribute of an object."""
    def __init__(self, obj, property_name, new_value, old_value, description="Modifier propriété", signal=None):
        super().__init__(description)
        self.obj = obj
        self.property_name = property_name
        self.new_value = new_value
        self.old_value = old_value
        self.signal = signal

    def redo(self):
        setattr(self.obj, self.property_name, self.new_value)
        if self.signal: self.signal.emit()

    def undo(self):
        setattr(self.obj, self.property_name, self.old_value)
        if self.signal: self.signal.emit()

class ReplaceDictItemCommand(QUndoCommand):
    """Generic command to replace an item in a dictionary (for edits)."""
    def __init__(self, target_dict, key, new_value, old_value, description="Remplacer élément", signal=None):
        super().__init__(description)
        self.target_dict = target_dict
        self.key = key
        self.new_value = new_value
        self.old_value = old_value
        self.signal = signal

    def redo(self):
        self.target_dict[self.key] = self.new_value
        if self.signal: self.signal.emit()

    def undo(self):
        self.target_dict[self.key] = self.old_value
        if self.signal: self.signal.emit()

class EditNodeDictKeyCommand(QUndoCommand):
    """Commande générique pour modifier une clé d'un dictionnaire du nœud (ex: content['choices'])."""
    def __init__(self, node_model, dict_name, key, new_value, old_value, signal=None):
        super().__init__(f"Modifier {key}")
        self.node_model = node_model
        self.dict_name = dict_name # "content" or "logic"
        self.key = key
        self.new_value = new_value
        self.old_value = old_value
        self.signal = signal

    def redo(self):
        target_dict = getattr(self.node_model, self.dict_name)
        target_dict[self.key] = self.new_value
        if self.signal:
            self.signal.emit()

    def undo(self):
        target_dict = getattr(self.node_model, self.dict_name)
        target_dict[self.key] = self.old_value
        if self.signal:
            self.signal.emit()
