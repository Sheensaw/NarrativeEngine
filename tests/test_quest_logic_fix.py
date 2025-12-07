
import unittest
from src.engine.variable_store import VariableStore

class TestQuestLogic(unittest.TestCase):
    def setUp(self):
        self.store = VariableStore()

    def test_complete_quest_without_start(self):
        """Verify that completing a quest without starting it fails (or checks state)."""
        quest_id = "quest_test_1"
        
        # Ensure initially empty
        self.assertEqual(self.store.get_var("active_quests", []), [])
        self.assertEqual(self.store.get_var("completed_quests", []), [])
        
        # Try to complete without starting
        self.store.complete_quest(quest_id)
        
        # Logic we WANT: It should NOT be in completed if it wasn't active
        completed = self.store.get_var("completed_quests", [])
        self.assertNotIn(quest_id, completed)
        print("Test Passed: Quest was not completed because it was not active.") 

if __name__ == '__main__':
    unittest.main()
