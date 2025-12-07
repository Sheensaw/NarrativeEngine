import unittest
from src.core.models import ProjectModel, QuestModel, ItemModel
from src.engine.story_manager import StoryManager

class TestQuestSystem(unittest.TestCase):
    def setUp(self):
        self.project = ProjectModel()
        
        # Create an Item
        self.sword = ItemModel(id="sword_01", name="Épée en fer", type="weapon")
        self.project.items["sword_01"] = self.sword
        
        # Create a Quest
        self.quest = QuestModel(id="quest_01", title="Tuer les rats")
        self.quest.presentation_text = "Aidez-moi à tuer les rats !"
        self.quest.loot = {
            "xp": 100,
            "gold": 50,
            "items": {"sword_01": 1}
        }
        self.project.quests["quest_01"] = self.quest
        
        # Init Manager
        self.manager = StoryManager()
        self.manager.load_project(self.project)

    def test_show_quest(self):
        # Execute macro
        self.manager.parser.execute_script(["<<showQuest quest_01>>"])
        
        # Check variable
        self.assertEqual(self.manager.variables.get_var("active_quest_offer"), "quest_01")
        
        # Simulate Hide
        self.manager.variables.hide_quest_offer()
        self.assertIsNone(self.manager.variables.get_var("active_quest_offer"))

    def test_start_quest(self):
        self.manager.parser.execute_script(["<<startQuest quest_01>>"])
        
        active = self.manager.variables.get_var("active_quests")
        self.assertIn("quest_01", active)

    def test_complete_quest(self):
        # Start first
        self.manager.variables.start_quest("quest_01")
        
        # Complete
        self.manager.parser.execute_script(["<<completeQuest quest_01>>"])
        
        active = self.manager.variables.get_var("active_quests")
        completed = self.manager.variables.get_var("completed_quests")
        
        self.assertNotIn("quest_01", active)
        self.assertIn("quest_01", completed)

    def test_return_quest_loot(self):
        # Setup: Quest completed
        self.manager.variables.start_quest("quest_01")
        self.manager.variables.complete_quest("quest_01")
        
        # Initial State
        self.assertEqual(self.manager.variables.get_var("xp", 0), 0)
        self.assertEqual(self.manager.variables.get_var("gold", 0), 0)
        self.assertEqual(self.manager.variables.get_var("inventory", {}), {})
        
        # Execute Return
        self.manager.parser.execute_script(["<<returnQuest quest_01>>"])
        
        # Check State
        returned = self.manager.variables.get_var("returned_quests")
        self.assertIn("quest_01", returned)
        
        # Check Loot
        self.assertEqual(self.manager.variables.get_var("xp"), 100)
        self.assertEqual(self.manager.variables.get_var("gold"), 50)
        
        inv = self.manager.variables.get_var("inventory")
        self.assertIn("sword_01", inv)
        self.assertEqual(inv["sword_01"], 1)

if __name__ == '__main__':
    unittest.main()
