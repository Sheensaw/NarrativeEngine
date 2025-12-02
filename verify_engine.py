import sys
import os
import uuid

# Add src to path
sys.path.append(os.getcwd())

from src.core.models import ProjectModel, NodeModel, EdgeModel
from src.engine.story_manager import StoryManager
from src.core.definitions import NodeType

def test_one_shot_text_modification():
    print("Testing One-Shot Text Modification...")
    
    # Setup Project
    project = ProjectModel()
    
    # Node A (Start)
    node_a = NodeModel(id="node_a", type=NodeType.START, title="Node A")
    node_a.content["text"] = "Original Text A"
    
    # Choice 1: One-Shot Modify Text
    choice_id = str(uuid.uuid4())
    choice_data = {
        "id": choice_id,
        "text": "Modify Text Choice",
        "target_node_id": "node_b", # Go to B
        "is_one_shot": True,
        "after_use": "modify_text",
        "new_scene_text": "Modified Text A"
    }
    node_a.content["choices"] = [choice_data]
    project.nodes["node_a"] = node_a
    
    # Node B
    node_b = NodeModel(id="node_b", type=NodeType.DIALOGUE, title="Node B")
    node_b.content["text"] = "Text B"
    project.nodes["node_b"] = node_b
    
    # Init Engine
    manager = StoryManager()
    manager.load_project(project)
    manager.start_game()
    
    # Verify Initial State
    print(f"Current Node: {manager.current_node.id}")
import sys
import os
import uuid

# Add src to path
sys.path.append(os.getcwd())

from src.core.models import ProjectModel, NodeModel, EdgeModel
from src.engine.story_manager import StoryManager
from src.core.definitions import NodeType

def test_one_shot_text_modification():
    print("Testing One-Shot Text Modification...")
    
    # Setup Project
    project = ProjectModel()
    
    # Node A (Start)
    node_a = NodeModel(id="node_a", type=NodeType.START, title="Node A")
    node_a.content["text"] = "Original Text A"
    
    # Choice 1: One-Shot Modify Text
    choice_id = str(uuid.uuid4())
    choice_data = {
        "id": choice_id,
        "text": "Modify Text Choice",
        "target_node_id": "node_b", # Go to B
        "is_one_shot": True,
        "after_use": "modify_text",
        "new_scene_text": "Modified Text A"
    }
    node_a.content["choices"] = [choice_data]
    project.nodes["node_a"] = node_a
    
    # Node B
    node_b = NodeModel(id="node_b", type=NodeType.DIALOGUE, title="Node B")
    node_b.content["text"] = "Text B"
    project.nodes["node_b"] = node_b
    
    # Init Engine
    manager = StoryManager()
    manager.load_project(project)
    manager.start_game()
    
    # Verify Initial State
    print(f"Current Node: {manager.current_node.id}")
    text = manager.get_parsed_text()
    print(f"Initial Text: {text}")
    if text != "Original Text A":
        print("FAIL: Initial text incorrect.")
        return
        
    # --- Test Case 1: Delete + Modify Text ---
    print("\n--- Test Case 1: Delete + Modify Text ---")
    manager.set_current_node("node_a")
    
    # Setup Choice 1: Delete + Modify Text
    choice1 = {
        "id": "c1",
        "text": "Choice 1 (Delete + Mod)",
        "target_node_id": "node_b",
        "is_one_shot": True,
        "after_use": "delete",
        "modify_text_enabled": True,
        "new_scene_text": "Text A Modified by C1"
    }
    node_a.content["choices"] = [choice1]
    
    print(f"Initial Text: {manager.get_parsed_text()}")
    manager.make_choice(0) # Select Choice 1
    
    # Check Text Modification
    manager.set_current_node("node_a")
    text_after = manager.get_parsed_text()
    print(f"Text after C1: {text_after}")
    if text_after != "Text A Modified by C1":
        print("FAILURE: Text was not modified correctly by C1.")
        exit(1)
        
    # Check Choice Deletion
    choices = manager.get_available_choices()
    if len(choices) != 0:
        print("FAILURE: Choice 1 should be deleted.")
        exit(1)
    print("SUCCESS: C1 (Delete + Mod) passed.")

    # --- Test Case 2: Replace + Modify Text ---
    print("\n--- Test Case 2: Replace + Modify Text ---")
    # Reset Node A Text override for clarity (optional, but good for isolation)
    manager.variables.set_node_text("node_a", "Original Text A")
    
    # Setup Choice 2: Replace + Modify Text
    choice2 = {
        "id": "c2",
        "text": "Choice 2 (Replace + Mod)",
        "target_node_id": "node_b",
        "is_one_shot": True,
        "after_use": "replace",
        "replacement_data": {"text": "Replacement Choice", "target_node_id": "node_b"},
        "modify_text_enabled": True,
        "new_scene_text": "Text A Modified by C2"
    }
    node_a.content["choices"] = [choice2]
    
    manager.set_current_node("node_a")
    print(f"Initial Text: {manager.get_parsed_text()}")
    manager.make_choice(0) # Select Choice 2
    
    # Check Text Modification
    manager.set_current_node("node_a")
    text_after = manager.get_parsed_text()
    print(f"Text after C2: {text_after}")
    if text_after != "Text A Modified by C2":
        print("FAILURE: Text was not modified correctly by C2.")
        exit(1)
        
    # Check Choice Replacement
    choices = manager.get_available_choices()
    if len(choices) != 1 or choices[0]["text"] != "Replacement Choice":
        print(f"FAILURE: Choice 2 should be replaced. Got: {choices}")
        exit(1)
    print("SUCCESS: C2 (Replace + Mod) passed.")

    # --- Test Case 3: Disable + Modify Text ---
    print("\n--- Test Case 3: Disable + Modify Text ---")
    manager.variables.set_node_text("node_a", "Original Text A")
    
    # Setup Choice 3: Disable + Modify Text
    choice3 = {
        "id": "c3",
        "text": "Choice 3 (Disable + Mod)",
        "target_node_id": "node_b",
        "is_one_shot": True,
        "after_use": "disable",
        "modify_text_enabled": True,
        "new_scene_text": "Text A Modified by C3"
    }
    node_a.content["choices"] = [choice3]
    
    manager.set_current_node("node_a")
    print(f"Initial Text: {manager.get_parsed_text()}")
    manager.make_choice(0) # Select Choice 3
    
    # Check Text Modification
    manager.set_current_node("node_a")
    text_after = manager.get_parsed_text()
    print(f"Text after C3: {text_after}")
    if text_after != "Text A Modified by C3":
        print("FAILURE: Text was not modified correctly by C3.")
        exit(1)
        
    # Check Choice Disabling
    choices = manager.get_available_choices()
    if len(choices) != 1 or not choices[0].get("disabled"):
        print(f"FAILURE: Choice 3 should be disabled. Got: {choices}")
        exit(1)
        
    # Try to click disabled choice
    print("Attempting to click disabled choice...")
    manager.make_choice(0)
    if manager.current_node.id != "node_a":
         print("FAILURE: Clicking disabled choice should not navigate.")
         exit(1)
         
    print("SUCCESS: C3 (Disable + Mod) passed.")

if __name__ == "__main__":
    test_one_shot_text_modification()
