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

    print("Verification Successful!")

if __name__ == "__main__":
    try:
        verify_editor_logic()
    except Exception as e:
        print(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()
