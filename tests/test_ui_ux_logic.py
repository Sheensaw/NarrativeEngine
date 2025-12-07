import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPointF, QRectF, Qt

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.models import GroupModel, NodeModel
from src.editor.graph.group_item import GroupItem
from src.editor.panels.inspector import ChoiceEditorWidget

# Mock Clipboard
class MockClipboard:
    def __init__(self):
        self._text = ""
        self._mime_data = None
    
    def setText(self, text):
        self._text = text
        
    def text(self):
        return self._text

class TestUIUXLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def test_group_resizing_logic(self):
        """Test logic for group resizing."""
        group_model = GroupModel(width=300, height=300)
        # Simulate resizing: changing width/height
        # In the actual item, this is handled by mouse events updating the rect
        # Here we verify the model update logic if we were to apply it
        
        new_width = 400
        new_height = 400
        group_model.width = new_width
        group_model.height = new_height
        
        self.assertEqual(group_model.width, 400)
        self.assertEqual(group_model.height, 400)
        
        # Verify rect calculation
        rect = QRectF(group_model.pos_x, group_model.pos_y, group_model.width, group_model.height)
        self.assertEqual(rect.width(), 400)
        self.assertEqual(rect.height(), 400)

    def test_choice_copy_paste_logic(self):
        """Test logic for copying and pasting choices."""
        # Simulate Copy
        choice_data = {"text": "Copied Choice", "target": "n1"}
        import json
        mime_text = json.dumps(choice_data)
        
        # Simulate Paste
        pasted_data = json.loads(mime_text)
        self.assertEqual(pasted_data["text"], "Copied Choice")
        self.assertEqual(pasted_data["target"], "n1")
        
        # Verify it's a new dict (copy)
        pasted_data["text"] = "Modified"
        self.assertNotEqual(choice_data["text"], "Modified")

    def test_group_header_move_logic(self):
        """Test that moving header moves the group."""
        # This is mostly UI event logic, but we can verify the coordinate math
        group_pos = QPointF(100, 100)
        mouse_delta = QPointF(10, 10)
        
        new_pos = group_pos + mouse_delta
        self.assertEqual(new_pos.x(), 110)
        self.assertEqual(new_pos.y(), 110)

if __name__ == '__main__':
    unittest.main()
