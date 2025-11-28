import sys
import os
import unittest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.models import ProjectModel, NodeModel
from src.engine.story_manager import StoryManager

class TestChoiceEvents(unittest.TestCase):
    def setUp(self):
        self.sm = StoryManager()
        self.project = ProjectModel()
        self.sm.load_project(self.project)
        
        # Create a test node
        self.node = NodeModel(id="node_1", title="Test Node")
        self.project.add_node(self.node)
        
        # Create a target node
        self.target = NodeModel(id="node_2", title="Target Node")
        self.project.add_node(self.target)
        
        self.sm.set_current_node("node_1")

    def test_choice_events(self):
        # Define a choice with an event (add item)
        choice_data = {
            "id": "choice_event_1",
            "text": "Get Gold",
            "target_node_id": "node_1", # Stay on same node
            "events": [
                {"type": "addItem", "parameters": {"item_id": "gold_coin", "qty": 10}}
            ]
        }
        self.node.content["choices"] = [choice_data]
        
        # Verify choice is available
        choices = self.sm.get_available_choices()
        self.assertEqual(len(choices), 1)
        
        # Make choice
        self.sm.make_choice(0)
        
        # Verify event execution (check inventory)
        inv = self.sm.variables.get_var("inventory")
        self.assertEqual(inv.get("gold_coin"), 10)

    def test_oneshot_delete(self):
        # Define a one-shot choice that deletes itself
        choice_data = {
            "id": "choice_oneshot_1",
            "text": "One Shot Choice",
            "target_node_id": "node_2",
            "is_one_shot": True,
            "after_use": "delete"
        }
        self.node.content["choices"] = [choice_data]
        
        # 1. Verify available initially
        choices = self.sm.get_available_choices()
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["text"], "One Shot Choice")
        
        # 2. Make choice
        self.sm.make_choice(0)
        
        # Verify marked as used
        self.assertTrue(self.sm.variables.is_choice_used("choice_oneshot_1"))
        
        # 3. Return to node and verify choice is gone
        self.sm.set_current_node("node_1")
        choices = self.sm.get_available_choices()
        self.assertEqual(len(choices), 0)

    def test_oneshot_replace(self):
        # Define a one-shot choice that replaces itself
        choice_data = {
            "id": "choice_oneshot_2",
            "text": "Take Sword",
            "target_node_id": "node_2",
            "is_one_shot": True,
            "after_use": "replace",
            "replacement_data": {
                "text": "Sword Taken",
                "target_node_id": "node_1"
            }
        }
        self.node.content["choices"] = [choice_data]
        
        # 1. Verify available initially
        choices = self.sm.get_available_choices()
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["text"], "Take Sword")
        
        # 2. Make choice
        self.sm.make_choice(0)
        
        # 3. Return to node and verify replacement
        self.sm.set_current_node("node_1")
        choices = self.sm.get_available_choices()
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["text"], "Sword Taken")
        self.assertTrue(choices[0].get("is_replacement"))

if __name__ == '__main__':
    unittest.main()
