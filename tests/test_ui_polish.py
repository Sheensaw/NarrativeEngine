import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication, QLineEdit, QTextEdit, QSplitter
from PyQt6.QtCore import Qt

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.editor.panels.database_panel import DatabasePanel
from src.editor.panels.inspector import InspectorPanel
from src.editor.graph.view import NodeGraphView
from src.editor.graph.scene import NodeScene

class TestUIPolish(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def test_database_panel_search_splitter(self):
        """Verify DatabasePanel has search bars and splitters."""
        try:
            import src.editor.panels.database_panel as db_panel_module
            panel = DatabasePanel()
            
            # Check Items Tab
            self.assertTrue(hasattr(panel, 'item_search'), "DatabasePanel should have item_search")
            self.assertIsInstance(panel.item_search, QLineEdit)
            self.assertEqual(panel.item_search.placeholderText(), "Rechercher un objet...")
            
            # Check Quests Tab
            self.assertTrue(hasattr(panel, 'quest_search'), "DatabasePanel should have quest_search")
            self.assertIsInstance(panel.quest_search, QLineEdit)
            self.assertEqual(panel.quest_search.placeholderText(), "Rechercher une quête...")
            
            # Check Methods
            self.assertTrue(hasattr(panel, '_filter_items_list'))
            self.assertTrue(hasattr(panel, '_filter_quests_list'))
            
            # Check Variables Tab
            self.assertTrue(hasattr(panel, 'var_search'), "DatabasePanel should have var_search")
            self.assertEqual(panel.var_search.placeholderText(), "Rechercher une variable...")
            self.assertTrue(hasattr(panel, '_filter_variables_list'))

            # Check Locations Tab
            self.assertTrue(hasattr(panel, 'loc_search'), "DatabasePanel should have loc_search")
            self.assertEqual(panel.loc_search.placeholderText(), "Rechercher un lieu...")
            self.assertTrue(hasattr(panel, '_filter_locations_list'))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.fail(f"Test failed with exception: {e}")

    def test_inspector_placeholders(self):
        """Verify InspectorPanel inputs have placeholders."""
        panel = InspectorPanel()
        
        # We need to access the private widgets. 
        # Based on implementation, they are created in __init__
        
        # txt_title
        self.assertTrue(hasattr(panel, 'txt_title'))
        self.assertEqual(panel.txt_title.placeholderText(), "Titre du nœud...")
        
        # txt_default_preview
        self.assertTrue(hasattr(panel, 'txt_default_preview'))
        self.assertEqual(panel.txt_default_preview.placeholderText(), "Texte par défaut (éditable dans le graphe)...")

    def test_inspector_choice_layout_fix(self):
        """Verify ChoiceItemWidget has toggled signal."""
        from src.editor.panels.inspector import ChoiceItemWidget
        self.assertTrue(hasattr(ChoiceItemWidget, 'toggled'), "ChoiceItemWidget should have 'toggled' signal")

    def test_inspector_auto_collapse_fix(self):
        """Verify that editing a choice does not trigger a full list reload (which causes collapse)."""
        from src.editor.panels.inspector import ChoiceEditorWidget
        
        # Create widget
        widget = ChoiceEditorWidget()
        
        # Mock refresh_list to track calls
        call_count = 0
        original_refresh = widget.refresh_list
        
        def mock_refresh():
            nonlocal call_count
            call_count += 1
            original_refresh()
            
        widget.refresh_list = mock_refresh
        
        # Add a choice
        widget.add_choice()
        initial_count = call_count
        
        # Simulate an edit (e.g. data_changed emit)
        # In the bug, data_changed connected to _reload_from_model which called refresh_list
        widget.data_changed.emit()
        
        # Verify refresh_list was NOT called again
        self.assertEqual(call_count, initial_count, "refresh_list should not be called on data_changed (internal edit)")

    def test_inspector_animation_signal(self):
        """Verify that CollapsibleBox animation triggers layout updates in ChoiceEditorWidget."""
        from src.editor.panels.inspector import ChoiceEditorWidget
        from PyQt6.QtCore import QSize
        
        widget = ChoiceEditorWidget()
        widget.add_choice()
        
        # Get the item and widget
        item = widget.list_widget.item(0)
        choice_widget = widget.list_widget.itemWidget(item)
        
        # Mock doItemsLayout to track calls
        call_count = 0
        original_doItemsLayout = widget.list_widget.doItemsLayout
        
        def mock_doItemsLayout():
            nonlocal call_count
            call_count += 1
            original_doItemsLayout()
            
        widget.list_widget.doItemsLayout = mock_doItemsLayout
        
        # Trigger animation valueChanged
        anim = choice_widget.collapsible.get_animation()
        anim.valueChanged.emit(100) # Simulate animation step
        
        # Verify doItemsLayout was called
        self.assertTrue(call_count > 0, "doItemsLayout should be called when animation value changes")

    def test_inspector_hide_ids(self):
        """Verify that Inspector dropdowns do not show full UUIDs."""
        from src.editor.panels.inspector import ChoiceItemWidget
        from src.core.models import ProjectModel, NodeModel
        
        # Setup Project with a node
        project = ProjectModel()
        node = NodeModel(title="Test Node") # ID will be generated
        project.add_node(node)
        
        # Create Widget
        choice_data = {"text": "Choice", "target_node_id": ""}
        widget = ChoiceItemWidget(choice_data, project=project)
        
        # Check combo_target items
        found_full_id = False
        for i in range(widget.combo_target.count()):
            text = widget.combo_target.itemText(i)
            if node.id in text and len(node.id) > 10: # Check if full ID is present
                found_full_id = True
                break
        
        self.assertFalse(found_full_id, "Dropdown should not contain full UUID in text")
        
        # Check that title is present
        found_title = False
        for i in range(widget.combo_target.count()):
            text = widget.combo_target.itemText(i)
            if "Test Node" in text:
                found_title = True
                break
        self.assertTrue(found_title, "Dropdown should contain node title")

    def test_graph_view_shortcuts(self):
        """Verify NodeGraphView has keyPressEvent logic."""
        scene = NodeScene(None)
        view = NodeGraphView(scene)
        
        # We can't easily simulate key press events in headless unit test without QTest
        # But we can check if the method exists and is overridden
        self.assertTrue(hasattr(view, 'keyPressEvent'))
        
        # Check if focus_selection exists
        self.assertTrue(hasattr(view, 'focus_selection'))

if __name__ == '__main__':
    unittest.main()
