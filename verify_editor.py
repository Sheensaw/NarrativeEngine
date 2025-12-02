import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPointF

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.core.models import ProjectModel, NodeModel, NodeType
from src.editor.graph.scene import NodeScene
from src.editor.graph.node_item import NodeItem
from src.editor.graph.edge_item import EdgeItem

def verify_editor_logic():
    app = QApplication(sys.argv)
    
    # 1. Create Project
    project = ProjectModel()
    node_a = NodeModel(id="A", title="Node A", type=NodeType.DIALOGUE, pos_x=0, pos_y=0)
    node_b = NodeModel(id="B", title="Node B", type=NodeType.DIALOGUE, pos_x=200, pos_y=0)
    project.add_node(node_a)
    project.add_node(node_b)
    
    # 2. Create Scene
    scene = NodeScene()
    scene.set_project(project)
    
    print(f"Nodes in scene: {len(scene.items())}")
    assert len(scene.node_map) == 2, "Should have 2 nodes"
    assert len(scene.edges) == 0, "Should have 0 edges initially"
    
    # 3. Add Choice A -> B
    print("Adding choice A -> B...")
    node_a.content["choices"] = [{"text": "Go to B", "target_node_id": "B"}]
    
    # 4. Refresh Connections
    scene.refresh_connections()
    
    print(f"Edges after refresh: {len(scene.edges)}")
    assert len(scene.edges) == 1, "Should have 1 edge A->B"
    edge = scene.edges[0]
    assert edge.source_node.model.id == "A"
    assert edge.target_node.model.id == "B"
    assert not edge.is_bidirectional, "Should be single direction"
    
    # 5. Add Choice B -> A (Bi-directional)
    print("Adding choice B -> A...")
    node_b.content["choices"] = [{"text": "Go back to A", "target_node_id": "A"}]
    
    scene.refresh_connections()
    
    print(f"Edges after bidirectional add: {len(scene.edges)}")
    assert len(scene.edges) == 1, "Should still be 1 edge (merged)"
    edge = scene.edges[0]
    assert edge.is_bidirectional, "Should be bi-directional now"
    
    # 6. Move Node (Check for crash)
    print("Moving Node A...")
    item_a = scene.node_map["A"]
    item_a.setPos(100, 100)
    
    # 7. Remove Choice
    print("Removing choice A -> B...")
    node_a.content["choices"] = []
    scene.refresh_connections()
    
    print(f"Edges after removal: {len(scene.edges)}")
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPointF

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.core.models import ProjectModel, NodeModel, NodeType
from src.editor.graph.scene import NodeScene
from src.editor.graph.node_item import NodeItem
from src.editor.graph.edge_item import EdgeItem

def verify_editor_logic():
    app = QApplication(sys.argv)
    
    # 1. Create Project
    project = ProjectModel()
    node_a = NodeModel(id="A", title="Node A", type=NodeType.DIALOGUE, pos_x=0, pos_y=0)
    node_b = NodeModel(id="B", title="Node B", type=NodeType.DIALOGUE, pos_x=200, pos_y=0)
    project.add_node(node_a)
    project.add_node(node_b)
    
    # 2. Create Scene
    scene = NodeScene()
    scene.set_project(project)
    
    print(f"Nodes in scene: {len(scene.items())}")
    assert len(scene.node_map) == 2, "Should have 2 nodes"
    assert len(scene.edges) == 0, "Should have 0 edges initially"
    
    # 3. Add Choice A -> B
    print("Adding choice A -> B...")
    node_a.content["choices"] = [{"text": "Go to B", "target_node_id": "B"}]
    
    # 4. Refresh Connections
    scene.refresh_connections()
    
    print(f"Edges after refresh: {len(scene.edges)}")
    assert len(scene.edges) == 1, "Should have 1 edge A->B"
    edge = scene.edges[0]
    assert edge.source_node.model.id == "A"
    assert edge.target_node.model.id == "B"
    assert not edge.is_bidirectional, "Should be single direction"
    
    # 5. Add Choice B -> A (Bi-directional)
    print("Adding choice B -> A...")
    node_b.content["choices"] = [{"text": "Go back to A", "target_node_id": "A"}]
    
    scene.refresh_connections()
    
    print(f"Edges after bidirectional add: {len(scene.edges)}")
    assert len(scene.edges) == 1, "Should still be 1 edge (merged)"
    edge = scene.edges[0]
    assert edge.is_bidirectional, "Should be bi-directional now"
    
    # 6. Move Node (Check for crash)
    print("Moving Node A...")
    item_a = scene.node_map["A"]
    item_a.setPos(100, 100)
    
    # 7. Remove Choice
    print("Removing choice A -> B...")
    node_a.content["choices"] = []
    scene.refresh_connections()
    
    print(f"Edges after removal: {len(scene.edges)}")
    assert len(scene.edges) == 1, "Should still be 1 edge (B->A only)"
    edge = scene.edges[0]
    assert not edge.is_bidirectional, "Should revert to single direction B->A"
    assert edge.source_node.model.id == "B"
    assert edge.target_node.model.id == "A"

    # 8. Test Node Expansion (In-Scene Editing)
    print("Testing Node Expansion...")
    item_a.toggle_expanded_mode()
    if not item_a.is_expanded:
        print("Error: Node A did not expand.")
        sys.exit(1)
    
    if not item_a.proxy_widget:
        print("Error: Proxy widget not created.")
        sys.exit(1)
        
    # Simulate text edit
    item_a.text_edit.setPlainText("New Content from Editor")
    
    # Collapse and Save
    item_a.toggle_expanded_mode()
    if item_a.is_expanded:
        print("Error: Node A did not collapse.")
        sys.exit(1)
        
    if item_a.model.content["text"] != "New Content from Editor":
        print(f"Error: Content not saved. Expected 'New Content from Editor', got '{item_a.model.content['text']}'")
        sys.exit(1)

    # 9. Test Alignment Logic
    print("Testing Alignment Logic...")
    from src.editor.graph.view import NodeGraphView
    view = NodeGraphView(scene)
    
    # Select A and B
    item_b = scene.node_map["B"]
    item_a.setSelected(True)
    item_b.setSelected(True)
    
    # Align Horizontal (should align Y)
    # Move B to different Y first
    item_b.setY(50)
    assert item_a.y() != item_b.y()
    
    view.align_selection("horizontal")
    
    # Check if Y is same (or close enough)
    print(f"Node A Y: {item_a.y()}, Node B Y: {item_b.y()}")
    assert abs(item_a.y() - item_b.y()) < 0.1, "Nodes should be aligned horizontally (same Y)"
    
    # Align Vertical (should align X)
    # Move B to different X
    item_b.setX(300)
    assert item_a.x() != item_b.x()
    
    view.align_selection("vertical")
    
    print(f"Node A X: {item_a.x()}, Node B X: {item_b.x()}")
    assert abs(item_a.x() - item_b.x()) < 0.1, "Nodes should be aligned vertically (same X)"

    # 10. Test Preview Text Resolution
    print("Testing Preview Text Resolution...")
    
    # Add choice back to A -> B
    item_a.model.content["choices"] = [{"text": "Go to B", "target_node_id": "B"}]
    
    # Force update preview (simulating scene load or change)
    item_a.update_preview()
    preview_text = item_a._preview_item.toPlainText()
    print(f"Preview Text for A: {preview_text}")
    
    if "Node B" not in preview_text:
        print("Error: Preview text does not contain target node title 'Node B'.")
        print(f"Got: {preview_text}")
        sys.exit(1)
        
    # 11. Test Inspector 2.0 Structure
    print("Testing Inspector 2.0 Structure...")
    from src.editor.panels.inspector import InspectorPanel
    inspector = InspectorPanel()
    
    # Check Tabs
    if not hasattr(inspector, "tabs"):
        print("Error: InspectorPanel does not have 'tabs' attribute.")
        sys.exit(1)
        
    if inspector.tabs.count() != 3:
        print(f"Error: Expected 3 tabs, got {inspector.tabs.count()}")
        sys.exit(1)
        
    print("Tabs verified.")
    
    # Check Collapsible Cards (Add an event to check)
    inspector.editor_on_enter.add_event()
    event_widget = inspector.editor_on_enter.container_layout.itemAt(0).widget()
    
    if not hasattr(event_widget, "collapsible"):
        print("Error: EventItemWidget does not have 'collapsible' attribute.")
        sys.exit(1)
        
    print("Collapsible Cards verified.")
    
    # 12. Test One-Shot Text Modification Data
    print("Testing One-Shot Text Modification Data...")
    inspector.editor_choices.add_choice()
    choice_widget = inspector.editor_choices.container_layout.itemAt(0).widget()
    
    # Simulate user interaction
    choice_widget.chk_oneshot.setChecked(True)
    choice_widget.combo_action.setCurrentIndex(0) # "delete"
    choice_widget.chk_modify_text.setChecked(True)
    choice_widget.inp_scene_text.setPlainText("New Scene Text Content")
    
    # Verify Data
    choice_data = choice_widget.choice_data
    if not choice_data.get("is_one_shot"):
        print("Error: is_one_shot not set.")
        sys.exit(1)
    if choice_data.get("after_use") != "delete":
        print(f"Error: after_use is {choice_data.get('after_use')}, expected 'delete'")
        sys.exit(1)
    if not choice_data.get("modify_text_enabled"):
        print("Error: modify_text_enabled is False")
        sys.exit(1)
    if choice_data.get("new_scene_text") != "New Scene Text Content":
        print(f"Error: new_scene_text mismatch. Got '{choice_data.get('new_scene_text')}'")
        sys.exit(1)
        
    print("One-Shot Text Modification verified.")

    print("Verification Successful!")
    sys.exit(0)

if __name__ == "__main__":
    try:
        verify_editor_logic()
    except Exception as e:
        print(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()
