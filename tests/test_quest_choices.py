import unittest
from unittest.mock import MagicMock
from src.engine.story_manager import StoryManager
from src.core.models import ProjectModel, NodeModel
from src.core.definitions import NodeType

class TestQuestChoices(unittest.TestCase):
    def setUp(self):
        self.manager = StoryManager()
        self.project = ProjectModel()
        self.manager.load_project(self.project)
        
        # Setup Quest
        # We don't strictly need a QuestModel because the logic checks variable store, 
        # BUT the event parameters are what matters.
        
        # Setup Node with Choice containing showQuest event
        self.node = NodeModel(id="node1", type=NodeType.DIALOGUE)
        self.manager.project.nodes["node1"] = self.node
        self.manager.current_node = self.node
        
        # Define Choice Data structure
        self.choice_data = {
            "id": "c1",
            "text": "Accepter la Quête",
            "target_node_id": "node2",
            "events": [
                {
                    "type": "showQuest",
                    "parameters": {"quest_id": "quest1"}
                }
            ]
        }
        
        # Mock ScriptParser evaluate_condition to always true
        self.manager.parser.evaluate_condition = MagicMock(return_value=True)

    def test_new_quest_choice(self):
        # 0. Mock structure choices retrieval
        # Since get_available_choices iterates 'structured_choices' if present.
        # Currently StoryManager relies on `parser.get_choices_from_node` OR internal logic?
        # Let's check StoryManager again. It iterates `structured_choices = self.current_node.content.get("choices", [])`.
        self.node.content["choices"] = [self.choice_data]
        
        choices = self.manager.get_available_choices()
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["text"], "Accepter la Quête")
        self.assertFalse(choices[0].get("disabled", False))

    def test_started_quest_choice(self):
        self.node.content["choices"] = [self.choice_data]
        
        # 1. Start Quest
        self.manager.variables.set_var("active_quests", ["quest1"])
        
        choices = self.manager.get_available_choices()
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["text"], "Rendre la quête")
        self.assertTrue(choices[0]["disabled"]) # Started but not completed -> Disabled

    def test_completed_quest_choice(self):
        self.node.content["choices"] = [self.choice_data]
        
        # 1. Complete Quest (Implies active + completed)
        self.manager.variables.set_var("active_quests", ["quest1"])
        self.manager.variables.set_var("completed_quests", ["quest1"])
        
        choices = self.manager.get_available_choices()
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["text"], "Rendre la quête")
        self.assertFalse(choices[0]["disabled"]) # Completed -> Enabled

    def test_returned_quest_choice(self):
        self.node.content["choices"] = [self.choice_data]
        
        # 1. Returned Quest
        self.manager.variables.set_var("returned_quests", ["quest1"])
        
        choices = self.manager.get_available_choices()
        self.assertEqual(len(choices), 0) # Should be hidden

if __name__ == '__main__':
    unittest.main()
