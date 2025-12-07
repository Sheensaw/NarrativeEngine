
import unittest
from unittest.mock import MagicMock
from src.engine.story_manager import StoryManager
from src.core.models import ProjectModel, NodeModel, QuestModel

class TestQuestChoiceLogic(unittest.TestCase):
    def setUp(self):
        self.manager = StoryManager()
        self.manager.project = ProjectModel()
        self.manager.current_node = NodeModel(id="node_1")
        
    def test_filter_active_quest_choice(self):
        """Verify that a choice starting an active quest is hidden."""
        quest_id = "quest_alpha"
        
        # Setup Quest
        self.manager.project.quests[quest_id] = QuestModel(id=quest_id, title="Test Quest")
        
        # Setup Choice starting the quest
        self.manager.current_node.content["choices"] = [{
            "text": "Start Quest",
            "events": [{"type": "startQuest", "parameters": {"quest_id": quest_id}}]
        }]
        
        # Case 1: Quest Not Active -> Choice Visible
        choices = self.manager.get_available_choices()
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["text"], "Start Quest")
        
        # Case 2: Quest Active -> Choice Hidden
        self.manager.variables.set_var("active_quests", [quest_id])
        choices = self.manager.get_available_choices()
        self.assertEqual(len(choices), 0, "Choice should be hidden when quest is active")
        
    def test_inject_return_quest_choice(self):
        """Verify that return quest choice is injected at return scene."""
        quest_id = "quest_beta"
        return_scene = "node_return"
        
        # Setup Quest
        quest = QuestModel(id=quest_id, title="Returnable Quest", return_scene_id=return_scene)
        self.manager.project.quests[quest_id] = quest
        
        # Setup State: Quest Completed (Ready to Return)
        self.manager.variables.set_var("active_quests", [])
        self.manager.variables.set_var("completed_quests", [quest_id])
        
        # Move to Return Scene
        self.manager.current_node = NodeModel(id=return_scene)
        
        # Get Choices
        choices = self.manager.get_available_choices()
        
        # Should have injected choice
        self.assertEqual(len(choices), 1)
        self.assertIn("Rendre la quête", choices[0]["text"])
        self.assertEqual(choices[0]["data"]["events"][0]["type"], "returnQuest")
        
    def test_return_quest_already_returned(self):
        """Verify injection doesn't happen if already returned."""
        quest_id = "quest_gamma"
        return_scene = "node_return"
        
        quest = QuestModel(id=quest_id, return_scene_id=return_scene)
        self.manager.project.quests[quest_id] = quest
        
        self.manager.variables.set_var("completed_quests", [quest_id])
        self.manager.variables.set_var("returned_quests", [quest_id])
        
        self.manager.current_node = NodeModel(id=return_scene)
        choices = self.manager.get_available_choices()
        self.assertEqual(len(choices), 0)

if __name__ == '__main__':
    unittest.main()
