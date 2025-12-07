import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QUndoStack
from PyQt6.QtCore import QPointF

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.models import ProjectModel, NodeModel, ItemModel, NodeType
from src.core.commands import (
    MoveNodeCommand, AddNodeCommand, RemoveNodeCommand,
    EditNodePropertyCommand, EditChoiceCommand,
    AddDictItemCommand, RemoveDictItemCommand, ReplaceDictItemCommand
)
from src.editor.graph.node_item import NodeItem

# Mock Scene for testing commands that require it
class MockScene:
    def __init__(self, project):
        self.project = project
        self.items = []
        self.undo_stack = QUndoStack()

    def add_node_item(self, node_model):
        item = NodeItem(node_model)
        self.items.append(item)
        return item

    def removeItem(self, item):
        if item in self.items:
            self.items.remove(item)

    def refresh_connections(self):
        pass

class TestUndoRedo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.project = ProjectModel()
        self.scene = MockScene(self.project)
        self.undo_stack = self.scene.undo_stack

    def test_move_node_undo(self):
        """Test Undo/Redo for moving a node."""
        node = NodeModel(id="n1", pos_x=0, pos_y=0)
        self.project.add_node(node)
        item = self.scene.add_node_item(node)
        
        # Move
        old_pos = [QPointF(0, 0)]
        new_pos = [QPointF(100, 100)]
        cmd = MoveNodeCommand([item], new_pos, old_pos)
        self.undo_stack.push(cmd)
        
        self.assertEqual(node.pos_x, 100)
        self.assertEqual(node.pos_y, 100)
        
        # Undo
        self.undo_stack.undo()
        self.assertEqual(node.pos_x, 0)
        self.assertEqual(node.pos_y, 0)
        
        # Redo
        self.undo_stack.redo()
        self.assertEqual(node.pos_x, 100)
        self.assertEqual(node.pos_y, 100)

    def test_add_remove_node_undo(self):
        """Test Undo/Redo for adding/removing nodes."""
        node = NodeModel(id="n1")
        
        # Add
        cmd = AddNodeCommand(self.scene, node)
        self.undo_stack.push(cmd)
        self.assertIn("n1", self.project.nodes)
        
        # Undo Add
        self.undo_stack.undo()
        self.assertNotIn("n1", self.project.nodes)
        
        # Redo Add
        self.undo_stack.redo()
        self.assertIn("n1", self.project.nodes)
        
        # Remove
        item = self.scene.items[0] # The added item
        cmd_rem = RemoveNodeCommand(self.scene, [item])
        self.undo_stack.push(cmd_rem)
        self.assertNotIn("n1", self.project.nodes)
        
        # Undo Remove
        self.undo_stack.undo()
        self.assertIn("n1", self.project.nodes)

    def test_edit_property_undo(self):
        """Test Undo/Redo for editing node properties."""
        node = NodeModel(title="Old Title")
        
        cmd = EditNodePropertyCommand(node, "title", "New Title", "Old Title")
        self.undo_stack.push(cmd)
        self.assertEqual(node.title, "New Title")
        
        self.undo_stack.undo()
        self.assertEqual(node.title, "Old Title")
        
        self.undo_stack.redo()
        self.assertEqual(node.title, "New Title")

    def test_edit_choices_undo(self):
        """Test Undo/Redo for editing choices."""
        node = NodeModel()
        old_choices = []
        new_choices = [{"text": "Choice 1", "target": "n2"}]
        
        cmd = EditChoiceCommand(node, new_choices, old_choices)
        self.undo_stack.push(cmd)
        self.assertEqual(node.content["choices"], new_choices)
        
        self.undo_stack.undo()
        self.assertEqual(node.content["choices"], old_choices)
        
        self.undo_stack.redo()
        self.assertEqual(node.content["choices"], new_choices)

    def test_database_add_item_undo(self):
        """Test Undo/Redo for adding database items."""
        item = ItemModel(id="i1", name="Sword")
        
        cmd = AddDictItemCommand(self.project.items, item.id, item, "Add Item")
        self.undo_stack.push(cmd)
        self.assertIn("i1", self.project.items)
        
        self.undo_stack.undo()
        self.assertNotIn("i1", self.project.items)
        
        self.undo_stack.redo()
        self.assertIn("i1", self.project.items)

    def test_database_edit_item_undo(self):
        """Test Undo/Redo for editing database items (ReplaceDictItemCommand)."""
        item = ItemModel(id="i1", name="Sword")
        self.project.items["i1"] = item
        
        old_state = item # In real app we deepcopy, but here we simulate replacement
        # Actually ReplaceDictItemCommand replaces the OBJECT in the dict
        # So we need two different objects
        import copy
        item_v1 = ItemModel(id="i1", name="Sword")
        item_v2 = ItemModel(id="i1", name="Super Sword")
        
        self.project.items["i1"] = item_v1
        
        cmd = ReplaceDictItemCommand(self.project.items, "i1", item_v2, item_v1, "Edit Item")
        self.undo_stack.push(cmd)
        self.assertEqual(self.project.items["i1"].name, "Super Sword")
        
        self.undo_stack.undo()
        self.assertEqual(self.project.items["i1"].name, "Sword")
        
        self.undo_stack.redo()
        self.assertEqual(self.project.items["i1"].name, "Super Sword")

if __name__ == '__main__':
    unittest.main()
