
import unittest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication
from src.engine.variable_store import VariableStore
from src.core.models import ProjectModel, QuestModel
from src.ui.sliding_menu import SlidingMenu, QuestItemWidget

app = QApplication([])

class TestQuestSteps(unittest.TestCase):
    def setUp(self):
        self.store = VariableStore()
        
    def test_variable_store_steps(self):
        """Verify storage logic for steps."""
        qid = "test_q"
        
        # Start
        self.store.start_quest(qid)
        self.assertIn(qid, self.store.get_var("active_quests", []))
        self.assertEqual(self.store.get_var("quest_steps", {}).get(qid), 0)
        
        # Advance
        self.store.advance_quest_step(qid)
        self.assertEqual(self.store.get_var("quest_steps", {}).get(qid), 1)
        
        # Advance again
        self.store.advance_quest_step(qid)
        self.assertEqual(self.store.get_var("quest_steps", {}).get(qid), 2)
        
    def test_ui_display(self):
        """Verify SlidingMenu logic for selecting step text."""
        sm = MagicMock()
        sm.variables.get_var.side_effect = self.store.get_var
        
        qid = "q1"
        quest = QuestModel(id=qid, title="Q1", steps=["Step 1: Go", "Step 2: Fight"])
        
        project = MagicMock()
        project.quests = {qid: quest}
        sm.project = project
        
        # Case 1: Start (Step 0)
        self.store.start_quest(qid)
        
        # Mock add_quest_item to capture call args
        menu = SlidingMenu(story_manager=sm)
        # We need to spy on internal method or check results. 
        # Easier to check refresh logic isolation or check widget result
        
        # Let's override _add_quest_item to store args
        calls = []
        def mock_add(q, status, step_text):
            calls.append((q.id, status, step_text))
            
        menu._add_quest_item = mock_add
        
        # Refresh -> Expect "Step 1: Go"
        menu.refresh_quests()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][2], "Step 1: Go")
        
        # Case 2: Advance (Step 1)
        self.store.advance_quest_step(qid)
        calls.clear()
        menu.refresh_quests()
        self.assertEqual(calls[0][2], "Step 2: Fight")
        
        # Case 3: Overflow (Step 2, but only 2 steps 0,1)
        # Assuming we just keep showing last step or handle it. Current logic: Fallback to last step.
        self.store.advance_quest_step(qid)
        calls.clear()
        menu.refresh_quests()
        self.assertEqual(calls[0][2], "Step 2: Fight")

if __name__ == '__main__':
    unittest.main()
