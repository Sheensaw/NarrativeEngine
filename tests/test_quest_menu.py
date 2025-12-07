
import unittest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication
from src.engine.story_manager import StoryManager
from src.core.models import ProjectModel, NodeModel, QuestModel
from src.ui.sliding_menu import SlidingMenu

app = QApplication([])

class TestQuestMenuLogic(unittest.TestCase):
    def setUp(self):
        self.manager = StoryManager()
        self.manager.project = ProjectModel()
        self.manager.current_node = NodeModel(id="node_1")
        
    def test_filter_show_quest(self):
        """Verify that showQuest is hidden if quest is accepted/complete."""
        quest_id = "test_q"
        self.manager.project.quests[quest_id] = QuestModel(id=quest_id, title="Test Quest")
        
        # Choice triggering showQuest
        self.manager.current_node.content["choices"] = [{
            "text": "See Quest",
            "events": [{"type": "showQuest", "parameters": {"quest_id": quest_id}}]
        }]
        
        # 1. Not active -> Visible
        choices = self.manager.get_available_choices()
        self.assertEqual(len(choices), 1)
        
        # 2. Active -> Hidden
        self.manager.variables.set_var("active_quests", [quest_id])
        choices = self.manager.get_available_choices()
        self.assertEqual(len(choices), 0)
        
        # 3. Completed -> Hidden
        self.manager.variables.set_var("active_quests", [])
        self.manager.variables.set_var("completed_quests", [quest_id])
        choices = self.manager.get_available_choices()
        self.assertEqual(len(choices), 0)

    def test_quest_menu_population(self):
        """Verify logic for population quest menu lists."""
        # Setup mocks
        sm = MagicMock()
        sm.variables.get_var.side_effect = lambda k, d=None: {
            "active_quests": ["q1"],
            "completed_quests": ["q2"],
            "returned_quests": ["q3"]
        }.get(k, d)
        
        project = MagicMock()
        project.quests = {
            "q1": QuestModel(id="q1", title="Active Quest"),
            "q2": QuestModel(id="q2", title="Completed Quest"),
            "q3": QuestModel(id="q3", title="Returned Quest")
        }
        sm.project = project
        
        # Create Menu
        menu = SlidingMenu(story_manager=sm)
        
        # Refresh Quests
        menu.refresh_quests()
        
        # Check List Items
        # q3 should be excluded (returned)
        # q1 (active) and q2 (completed) should be present
        
        count = menu.quests_list.count()
        self.assertEqual(count, 2)
        
        titles = []
        for i in range(count):
             w = menu.quests_list.itemWidget(menu.quests_list.item(i))
             # We can't easily read labels from custom widget in unit test without more introspection,
             # but we can check if it ran without error and count items.
             # Accessing child labels:
             layout = w.layout()
             # Header layout
             header = layout.itemAt(0).layout()
             title_lbl = header.itemAt(0).widget()
             titles.append(title_lbl.text())
             
        self.assertIn("Active Quest", titles)
        self.assertIn("Completed Quest", titles)
        self.assertNotIn("Returned Quest", titles)

if __name__ == '__main__':
    unittest.main()
