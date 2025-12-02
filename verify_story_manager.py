import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.engine.story_manager import StoryManager
from src.core.models import ProjectModel

def test_story_manager_init():
    print("--- Testing StoryManager Initialization ---")
    try:
        manager = StoryManager()
        print("SUCCESS: StoryManager initialized without error.")
    except Exception as e:
        print(f"FAILURE: StoryManager initialization failed: {e}")
        return

    print("--- Testing load_project ---")
    try:
        project = ProjectModel()
        manager.load_project(project)
        print("SUCCESS: load_project called without error.")
    except Exception as e:
        print(f"FAILURE: load_project failed: {e}")

if __name__ == "__main__":
    test_story_manager_init()
