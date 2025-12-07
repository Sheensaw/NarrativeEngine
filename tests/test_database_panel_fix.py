import sys
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QUndoStack
from src.core.models import ProjectModel
from src.editor.panels.database_panel import DatabasePanel

# App needed for widgets
app = QApplication(sys.argv)

class TestDatabasePanelFix(unittest.TestCase):
    def setUp(self):
        self.undo_stack = QUndoStack()
        self.panel = DatabasePanel(undo_stack=self.undo_stack)
        self.project = ProjectModel()
        self.panel.set_project(self.project)

    def test_add_quest_refresh(self):
        # Initial state: 0 quests
        self.assertEqual(self.panel.quests_tree.topLevelItemCount(), 0)
        
        # Action: Add Quest
        self.panel._add_quest()
        
        # Check Model
        self.assertEqual(len(self.project.quests), 1)
        
        # Check View (Should be 1 if refresh worked)
        self.assertEqual(self.panel.quests_tree.topLevelItemCount(), 1)
        print("View updated successfully with count: 1")
        
        # Action: Undo
        self.undo_stack.undo()
        
        # Check Model
        self.assertEqual(len(self.project.quests), 0)
        
        # Check View (Should be 0)
        self.assertEqual(self.panel.quests_tree.topLevelItemCount(), 0)
        print("Undo successful, view count: 0")

    def test_styling_applied(self):
        style = self.panel.styleSheet()
        self.assertTrue("background-color: #2b2b2b" in style)
        print("Styles applied.")

    def test_refresh_quest_steps(self):
        # Create a quest with steps
        from src.core.models import QuestModel
        from PyQt6.QtCore import Qt
        
        q = QuestModel(id="test_q", title="Test Quest")
        q.steps = ["Step 1", "Step 2"]
        print(f"Init steps: {q.steps}")
        self.project.quests["test_q"] = q
        
        self.panel._refresh_quests_list()
        print(f"After refresh steps: {self.project.quests['test_q'].steps}")
        
        # Select it
        item = self.panel.quests_tree.topLevelItem(0)
        self.panel._on_quest_selected(item, 0)
        
        # Check steps list
        print(f"Quest steps inside verify: {q.steps}")
        print(f"List count: {self.panel.quest_steps_list.count()}")
        
        self.assertEqual(self.panel.quest_steps_list.count(), 2)
        self.assertEqual(self.panel.quest_steps_list.item(0).text(), "Step 1")
        print("Quest steps refreshed successfully.")

if __name__ == '__main__':
    unittest.main()
