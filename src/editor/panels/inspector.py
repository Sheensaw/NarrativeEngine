import sys
import uuid
import copy
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QComboBox, QPushButton, 
    QScrollArea, QFrame, QCheckBox, QSpinBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QTabWidget, QToolButton, QSizePolicy, QApplication, QListWidget, QListWidgetItem, QAbstractItemView, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QAbstractAnimation, QSize
from PyQt6.QtGui import QUndoStack, QAction, QIcon

from src.core.commands import ReorderChoicesCommand, EditChoiceCommand, EditNodePropertyCommand, EditNodeDictKeyCommand

from src.editor.graph.node_item import NodeItem
from src.core.definitions import MACRO_DEFINITIONS


class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.toggle_button = QToolButton(text=title, checkable=True, checked=False)
        self.toggle_button.setStyleSheet("""
            QToolButton { 
                border: 1px solid #3d3d3d; 
                background-color: #2d2d2d; 
                color: #eee; 
                padding: 8px; 
                text-align: left; 
                font-weight: bold; 
                font-size: 13px;
                border-radius: 4px;
            } 
            QToolButton:hover { 
                background-color: #3d3d3d; 
                border-color: #4d4d4d;
            }
            QToolButton:checked { 
                background-color: #404040; 
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
            }
        """)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self.toggle_button.clicked.connect(self.on_pressed)

        self.content_area = QWidget()
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        self.content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Add a subtle border/background to content area to match header
        self.content_area.setStyleSheet("""
            QWidget {
                background-color: #262626;
                border: 1px solid #3d3d3d;
                border-top: none;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
            }
        """)

        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def get_animation(self):
        return self.animation

    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        self.animation.setDirection(QAbstractAnimation.Direction.Forward if checked else QAbstractAnimation.Direction.Backward)
        self.animation.setStartValue(0)
        self.animation.setEndValue(self.content_area.layout().sizeHint().height())
        self.animation.start()

    def setContentLayout(self, layout):
        old_layout = self.content_area.layout()
        if old_layout:
            QWidget().setLayout(old_layout)
        self.content_area.setLayout(layout)


class MacroEditorWidget(QWidget):
    """
    Widget dynamique pour éditer les paramètres d'une macro spécifique.
    Génère les champs en fonction de MACRO_DEFINITIONS.
    """
    data_changed = pyqtSignal()

    def __init__(self, project=None):
        super().__init__()
        self.current_macro_type = None
        self.params = {}
        self.project = project
        
        self.layout = QFormLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.inputs = {}

    def set_project(self, project):
        self.project = project

    def set_macro_type(self, macro_type, params=None):
        self.current_macro_type = macro_type
        self.params = params if params else {}
        
        # Clear layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.inputs = {}

        definition = MACRO_DEFINITIONS.get(macro_type)
        if not definition:
            return

        for arg in definition.get("args", []):
            arg_name = arg["name"]
            arg_label = arg["label"]
            arg_type = arg["type"]
            current_val = self.params.get(arg_name, arg.get("default", ""))

            if arg_type == "select":
                inp = QComboBox()
                inp.addItems(arg.get("options", []))
                inp.setCurrentText(str(current_val))
                inp.currentTextChanged.connect(lambda t, n=arg_name: self.update_param(n, t))
            
            elif arg_type == "item_select":
                inp = QComboBox()
                inp.setEditable(True) # Allow manual entry if needed
                inp.addItem("", "")
                if self.project:
                    for item in self.project.items.values():
                        # AFFICHER SEULEMENT LE NOM
                        inp.addItem(item.name, item.id)
                        # Tooltip pour l'ID
                        inp.setItemData(inp.count()-1, f"ID: {item.id}", Qt.ItemDataRole.ToolTipRole)
                
                # Set current
                index = inp.findData(current_val)
                if index >= 0:
                    inp.setCurrentIndex(index)
                else:
                    inp.setEditText(str(current_val))
                
                inp.currentIndexChanged.connect(lambda idx, n=arg_name, i=inp: self.update_param(n, i.itemData(idx) if i.itemData(idx) else i.currentText()))
                inp.editTextChanged.connect(lambda t, n=arg_name: self.update_param(n, t))

            elif arg_type == "quest_select":
                inp = QComboBox()
                inp.setEditable(True)
                inp.addItem("", "")
                if self.project:
                    for quest in self.project.quests.values():
                        # AFFICHER SEULEMENT LE TITRE
                        inp.addItem(quest.title, quest.id)
                        inp.setItemData(inp.count()-1, f"ID: {quest.id}", Qt.ItemDataRole.ToolTipRole)
                
                index = inp.findData(current_val)
                if index >= 0:
                    inp.setCurrentIndex(index)
                else:
                    inp.setEditText(str(current_val))
                
                inp.currentIndexChanged.connect(lambda idx, n=arg_name, i=inp: self.update_param(n, i.itemData(idx) if i.itemData(idx) else i.currentText()))
                inp.editTextChanged.connect(lambda t, n=arg_name: self.update_param(n, t))

            elif arg_type == "node_select":
                inp = QComboBox()
                inp.setEditable(True)
                inp.addItem("", "")
                if self.project:
                    for node in self.project.nodes.values():
                        inp.addItem(node.title, node.id)
                        inp.setItemData(inp.count()-1, f"ID: {node.id}", Qt.ItemDataRole.ToolTipRole)
                
                index = inp.findData(current_val)
                if index >= 0:
                    inp.setCurrentIndex(index)
                else:
                    inp.setEditText(str(current_val))
                
                inp.currentIndexChanged.connect(lambda idx, n=arg_name, i=inp: self.update_param(n, i.itemData(idx) if i.itemData(idx) else i.currentText()))
                inp.editTextChanged.connect(lambda t, n=arg_name: self.update_param(n, t))

            elif arg_type == "bool":
                inp = QCheckBox()
                inp.setChecked(bool(current_val))
                inp.stateChanged.connect(lambda s, n=arg_name: self.update_param(n, bool(s)))
            elif arg_type == "text":
                inp = QTextEdit()
                inp.setPlainText(str(current_val))
                inp.setMaximumHeight(60)
                inp.textChanged.connect(lambda n=arg_name, i=inp: self.update_param(n, i.toPlainText()))
            else: # string, int, etc.
                inp = QLineEdit()
                inp.setText(str(current_val))
                inp.textChanged.connect(lambda t, n=arg_name: self.update_param(n, t))
            
            self.layout.addRow(arg_label, inp)
            self.inputs[arg_name] = inp

    def update_param(self, name, value):
        self.params[name] = value
        self.data_changed.emit()
    
    def get_params(self):
        return self.params


class EventItemWidget(QFrame):
    """Représente un événement individuel dans la liste (Card UI)."""
    removed = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, event_data, project=None):
        super().__init__()
        self.event_data = event_data
        self.project = project
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("QFrame { background-color: #444; border-radius: 5px; margin-bottom: 5px; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header_layout = QHBoxLayout()
        macro_type = event_data.get('type', 'unknown')
        label_text = MACRO_DEFINITIONS.get(macro_type, {}).get("label", macro_type)
        
        lbl_type = QLabel(f"<b>{label_text}</b>")
        header_layout.addWidget(lbl_type)
        
        # Remove button
        btn_remove = QPushButton("X")
        btn_remove.setFixedSize(20, 20)
        btn_remove.setStyleSheet("background-color: #d9534f; color: white; border: none; border-radius: 3px;")
        btn_remove.clicked.connect(self.remove_self)
        header_layout.addWidget(btn_remove)
        
        layout.addLayout(header_layout)
        
        # Body (Collapsible)
        self.collapsible = CollapsibleBox("Paramètres")
        body_layout = QVBoxLayout()
        
        self.macro_editor = MacroEditorWidget(project=self.project)
        self.macro_editor.set_macro_type(macro_type, event_data.get("parameters", {}))
        self.macro_editor.data_changed.connect(self.on_params_changed)
        body_layout.addWidget(self.macro_editor)
        
        self.collapsible.setContentLayout(body_layout)
        layout.addWidget(self.collapsible)

    def remove_self(self):
        self.removed.emit()
        self.deleteLater()

    def on_params_changed(self):
        self.event_data['parameters'] = self.macro_editor.get_params()
        self.changed.emit()
    
    def get_data(self):
        return self.event_data


class EventEditorWidget(QWidget):
    """Widget pour éditer une liste d'événements (macros) avec une UI ergonomique."""
    
    data_changed = pyqtSignal()
    structure_changed = pyqtSignal()

    def __init__(self, title="Événements", undo_stack=None):
        super().__init__()
        self.events = []
        self.project = None
        self.undo_stack = undo_stack
        self.node_model = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Signal for structural changes (Add/Remove)
        self.structure_changed.connect(self._reload_from_model)
        self.structure_changed.connect(self.data_changed.emit)
        
        # Signal for structural changes (Add/Remove)
        self.structure_changed.connect(self._reload_from_model)
        self.structure_changed.connect(self.data_changed.emit)
        
        # layout is already defined above, but we can just continue using it.
        # Actually, let's look at lines 291 and 298.
        # 291: layout = QVBoxLayout(self)
        # 292: layout.setContentsMargins(0, 0, 0, 0)
        # ...
        # 298: layout = QVBoxLayout(self) <-- ERROR
        
        # We will remove the first assignment logic block if it's redundant or just keep one.
        # Line 291 initiates it. Lines 294-297 do connections. Line 298 initiates it AGAIN.
        # Clean solution: Remove line 298.
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Zone de défilement pour les événements
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: transparent;")
        
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background-color: transparent;")
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.container_layout.setSpacing(5)
        
        self.scroll_area.setWidget(self.container_widget)
        layout.addWidget(self.scroll_area)
        
        # Contrôles d'ajout
        add_layout = QHBoxLayout()
        
        self.combo_type = QComboBox()
        # Populate from definitions
        for key, val in MACRO_DEFINITIONS.items():
            self.combo_type.addItem(val["label"], key)
            
        add_layout.addWidget(self.combo_type)
        
        self.btn_add = QPushButton("Ajouter")
        self.btn_add.setStyleSheet("background-color: #5cb85c; padding: 5px;")
        self.btn_add.clicked.connect(self.add_event)
        add_layout.addWidget(self.btn_add)
        
        layout.addLayout(add_layout)

    def set_events(self, events, project=None, node_model=None):
        self.events = events if events else []
        self.project = project
        self.node_model = node_model
        self.refresh_list()
        
    def _reload_from_model(self):
        if self.node_model:
            # Assuming "logic" dict and "on_enter" key based on usage in Inspector
            self.events = self.node_model.logic.get("on_enter", [])
            self.refresh_list()

    def refresh_list(self):
        # Clear existing items
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        for ev in self.events:
            self._create_event_widget(ev)

    def _create_event_widget(self, event_data):
        item = EventItemWidget(event_data, project=self.project)
        item.removed.connect(lambda: self.remove_event(item))
        item.changed.connect(self.data_changed.emit)
        self.container_layout.addWidget(item)

    def add_event(self):
        macro_key = self.combo_type.currentData()
        new_event = {"type": macro_key, "parameters": {}}
        
        if self.undo_stack is not None and self.node_model:
            new_list = self.events + [new_event]
            cmd = EditNodeDictKeyCommand(self.node_model, "logic", "on_enter", new_list, self.events, self.structure_changed)
            self.undo_stack.push(cmd)
            self.events = new_list
            self.refresh_list()
            self.structure_changed.emit()
        else:
            self.events.append(new_event)
            self._create_event_widget(new_event)
            self.structure_changed.emit()

    def remove_event(self, item_widget):
        if item_widget.event_data in self.events:
            if self.undo_stack is not None and self.node_model:
                new_list = self.events.copy()
                new_list.remove(item_widget.event_data)
                cmd = EditNodeDictKeyCommand(self.node_model, "logic", "on_enter", new_list, self.events, self.structure_changed)
                self.undo_stack.push(cmd)
                self.events = new_list
                self.refresh_list()
                self.structure_changed.emit()
            else:
                self.events.remove(item_widget.event_data)
                self.structure_changed.emit()


class ChoiceItemWidget(QFrame):
    removed = pyqtSignal()
    changed = pyqtSignal()
    toggled = pyqtSignal(bool)
    copy_requested = pyqtSignal(dict)
    paste_requested = pyqtSignal()

    def __init__(self, choice_data, project=None):
        super().__init__()
        self.choice_data = choice_data
        self.project = project
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("QFrame { background-color: #444; border-radius: 5px; margin-bottom: 5px; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header (Text + Remove)
        header_layout = QHBoxLayout()
        
        self.inp_text = QLineEdit(choice_data.get("text", ""))
        self.inp_text.setPlaceholderText("Texte du choix...")
        self.inp_text.textChanged.connect(self.on_change)
        header_layout.addWidget(self.inp_text, 2)
        
        btn_remove = QPushButton("X")
        btn_remove.setFixedSize(20, 20)
        btn_remove.setStyleSheet("background-color: #d9534f; color: white; border: none; border-radius: 3px;")
        btn_remove.clicked.connect(self.remove_self)
        header_layout.addWidget(btn_remove)
        
        layout.addLayout(header_layout)

        # Body (Collapsible)
        self.collapsible = CollapsibleBox("Détails")
        self.collapsible.toggle_button.toggled.connect(self.toggled.emit)
        body_layout = QVBoxLayout()
        
        # Target
        row_target = QHBoxLayout()
        row_target.addWidget(QLabel("Cible:"))
        self.combo_target = QComboBox()
        self.combo_target.setEditable(True)
        self.combo_target.addItem("", "")
        if self.project:
            for node in self.project.nodes.values():
                display_text = node.title if node.title else f"Node {node.id[:8]}"
                self.combo_target.addItem(display_text, node.id)
        
        current_target = choice_data.get("target_node_id", "")
        idx = self.combo_target.findData(current_target)
        if idx >= 0:
            self.combo_target.setCurrentIndex(idx)
        self.combo_target.currentIndexChanged.connect(self.on_change)
        row_target.addWidget(self.combo_target)
        body_layout.addLayout(row_target)
        
        # Condition
        row_cond = QHBoxLayout()
        row_cond.addWidget(QLabel("Condition:"))
        self.inp_condition = QLineEdit(choice_data.get("condition", ""))
        self.inp_condition.setPlaceholderText("Ex: $gold >= 10")
        self.inp_condition.textChanged.connect(self.on_change)
        row_cond.addWidget(self.inp_condition)
        body_layout.addLayout(row_cond)
        
        # One Shot
        self.chk_oneshot = QCheckBox("Unique (One-Shot)")
        self.chk_oneshot.setChecked(choice_data.get("is_one_shot", False))
        self.chk_oneshot.toggled.connect(self.on_oneshot_toggled)
        body_layout.addWidget(self.chk_oneshot)
        
        # One Shot Options Group
        self.group_oneshot = QWidget()
        group_layout = QVBoxLayout(self.group_oneshot)
        group_layout.setContentsMargins(10, 0, 0, 0)
        
        # Action (Delete, Replace, Disable, None)
        row_action = QHBoxLayout()
        row_action.addWidget(QLabel("Action après usage:"))
        self.combo_action = QComboBox()
        self.combo_action.addItem("Supprimer (Disparait)", "delete")
        self.combo_action.addItem("Remplacer (Autre choix)", "replace")
        self.combo_action.addItem("Désactiver (Grisé)", "disable")
        self.combo_action.addItem("Aucune (Reste visible)", "none")
        
        current_action = choice_data.get("after_use", "delete")
        if current_action == "modify_text":
            current_action = "delete"
            choice_data["modify_text_enabled"] = True
            
        idx_action = self.combo_action.findData(current_action)
        if idx_action >= 0:
            self.combo_action.setCurrentIndex(idx_action)
        self.combo_action.currentIndexChanged.connect(self.on_action_changed)
        row_action.addWidget(self.combo_action)
        group_layout.addLayout(row_action)
        
        # Replacement Group
        self.group_replacement = QWidget()
        rep_layout = QVBoxLayout(self.group_replacement)
        rep_layout.setContentsMargins(0, 0, 0, 0)
        
        rep_data = choice_data.get("replacement_data", {})
        self.inp_rep_text = QLineEdit(rep_data.get("text", ""))
        self.inp_rep_text.setPlaceholderText("Texte du remplacement")
        self.inp_rep_text.textChanged.connect(self.on_change)
        rep_layout.addWidget(self.inp_rep_text)
        
        self.combo_rep_target = QComboBox()
        self.combo_rep_target.setEditable(True)
        self.combo_rep_target.addItem("", "")
        if self.project:
            for node in self.project.nodes.values():
                display_text = node.title if node.title else f"Node {node.id[:8]}"
                self.combo_rep_target.addItem(display_text, node.id)
        idx_rep = self.combo_rep_target.findData(rep_data.get("target_node_id", ""))
        if idx_rep >= 0:
            self.combo_rep_target.setCurrentIndex(idx_rep)
        self.combo_rep_target.currentIndexChanged.connect(self.on_change)
        rep_layout.addWidget(self.combo_rep_target)
        
        group_layout.addWidget(self.group_replacement)

        # Text Modification Checkbox
        self.chk_modify_text = QCheckBox("Modifier le texte de la scène")
        self.chk_modify_text.setChecked(choice_data.get("modify_text_enabled", False))
        self.chk_modify_text.toggled.connect(self.on_modify_text_toggled)
        group_layout.addWidget(self.chk_modify_text)

        # Text Modification Editor
        self.inp_scene_text = QTextEdit()
        self.inp_scene_text.setPlaceholderText("Nouveau texte de la scène...")
        self.inp_scene_text.setMaximumHeight(100)
        self.inp_scene_text.setText(choice_data.get("new_scene_text", ""))
        self.inp_scene_text.textChanged.connect(self.on_scene_text_changed)
        group_layout.addWidget(self.inp_scene_text)
        
        body_layout.addWidget(self.group_oneshot)
        
        # Events
        self.editor_events = EventEditorWidget("Événements au clic")
        self.editor_events.set_events(choice_data.get("events", []), project=self.project)
        self.editor_events.data_changed.connect(self.on_change)
        body_layout.addWidget(self.editor_events)
        
        self.collapsible.setContentLayout(body_layout)
        layout.addWidget(self.collapsible)
        
        # Initial State
        self.on_oneshot_toggled()
        self.on_action_changed()
        self.on_modify_text_toggled()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        action_copy = QAction("Copier", self)
        action_copy.triggered.connect(lambda: self.copy_requested.emit(self.choice_data))
        menu.addAction(action_copy)
        
        action_paste = QAction("Coller", self)
        action_paste.triggered.connect(self.paste_requested.emit)
        menu.addAction(action_paste)
        
        menu.addSeparator()

        action_delete = QAction("Supprimer", self)
        action_delete.triggered.connect(self.remove_self)
        menu.addAction(action_delete)
        
        menu.exec(event.globalPos())

    def on_oneshot_toggled(self):
        is_oneshot = self.chk_oneshot.isChecked()
        self.group_oneshot.setVisible(is_oneshot)
        self.on_change()

    def on_action_changed(self):
        action = self.combo_action.currentData()
        self.group_replacement.setVisible(action == "replace")
        self.on_change()

    def on_modify_text_toggled(self):
        enabled = self.chk_modify_text.isChecked()
        self.inp_scene_text.setVisible(enabled)
        self.on_change()

    def on_scene_text_changed(self):
        self.choice_data["new_scene_text"] = self.inp_scene_text.toPlainText()
        self.changed.emit()

    def on_change(self):
        self.choice_data["text"] = self.inp_text.text()
        self.choice_data["target_node_id"] = self.combo_target.currentData()
        self.choice_data["condition"] = self.inp_condition.text()
        self.choice_data["is_one_shot"] = self.chk_oneshot.isChecked()
        self.choice_data["after_use"] = self.combo_action.currentData()
        self.choice_data["modify_text_enabled"] = self.chk_modify_text.isChecked()
        
        if self.combo_action.currentData() == "replace":
            self.choice_data["replacement_data"] = {
                "text": self.inp_rep_text.text(),
                "target_node_id": self.combo_rep_target.currentData()
            }
            
        if hasattr(self, 'editor_events'):
            self.choice_data["events"] = self.editor_events.events
        self.changed.emit()

    def remove_self(self):
        self.removed.emit()


class ChoiceListWidget(QListWidget):
    """QListWidget personnalisé pour gérer le Drag & Drop des choix."""
    order_changed = pyqtSignal()
    paste_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setStyleSheet("QListWidget { background: transparent; border: none; } QListWidget::item { border-bottom: 1px solid #555; }")

    def dropEvent(self, event):
        super().dropEvent(event)
        self.order_changed.emit()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        action_paste = QAction("Coller", self)
        action_paste.triggered.connect(self.paste_requested.emit)
        menu.addAction(action_paste)
        menu.exec(event.globalPos())


class ChoiceEditorWidget(QWidget):
    """Widget pour éditer les choix avec Drag & Drop et Context Menu."""
    
    data_changed = pyqtSignal()
    structure_changed = pyqtSignal()
    
    def __init__(self, title="Choix", undo_stack=None):
        super().__init__()
        self.choices = []
        self.project = None
        self.undo_stack = undo_stack
        self.node_model = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with Copy/Paste (Global)
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Choix</b>"))
        
        layout.addLayout(header_layout)
        
        # List Widget for Drag & Drop
        self.list_widget = ChoiceListWidget()
        self.list_widget.order_changed.connect(self.on_order_changed)
        self.list_widget.paste_requested.connect(self.paste_choices)
        layout.addWidget(self.list_widget)
        
        # Add Button
        self.btn_add = QPushButton("Ajouter un Choix")
        self.btn_add.setStyleSheet("background-color: #5cb85c; padding: 5px;")
        self.btn_add.clicked.connect(self.add_choice)
        layout.addWidget(self.btn_add)
        
        # Signal for structural changes (Add/Remove/Reorder) that require UI reload
        self.structure_changed.connect(self._reload_from_model)
        # Propagate structural changes to data_changed for scene updates
        self.structure_changed.connect(self.data_changed.emit)

        # Connect self signal to reload (for Undo/Redo)
        # FIX: We now use structure_changed for this, keeping data_changed for text edits only.
        # self.data_changed.connect(self._reload_from_model)

    def _reload_from_model(self):
        if self.node_model:
            # Reload choices from model to ensure UI is in sync (esp. after Undo)
            self.choices = self.node_model.content.get("choices", [])
            self.refresh_list()

    def set_choices(self, choices, project=None, node_model=None):
        self.choices = choices if choices else []
        self.project = project
        self.node_model = node_model
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        for c in self.choices:
            self._create_choice_item(c)

    def _create_choice_item(self, choice_data):
        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(0, 0)) # Will be adjusted by widget
        
        widget = ChoiceItemWidget(choice_data, self.project)
        widget.removed.connect(lambda: self.remove_choice(choice_data)) # Pass data, not widget
        widget.changed.connect(self.data_changed.emit)
        widget.toggled.connect(lambda c: self.on_item_toggled(item, widget, c))
        
        # Connect animation valueChanged to real-time resize
        anim = widget.collapsible.get_animation()
        anim.valueChanged.connect(lambda val: self._update_item_size(item, widget))
        
        widget.copy_requested.connect(self.copy_choice)
        widget.paste_requested.connect(self.paste_choices)
        
        self.list_widget.setItemWidget(item, widget)
        # Adjust size hint based on widget
        item.setSizeHint(widget.sizeHint())
        
        # Store data reference in item
        item.setData(Qt.ItemDataRole.UserRole, choice_data)

    def on_order_changed(self):
        # Reconstruct choices list from list_widget order
        new_choices = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            new_choices.append(data)
            
        if new_choices == self.choices:
            return

        if self.undo_stack is not None and self.node_model:
            # Use structure_changed signal so Undo/Redo reloads the list
            cmd = ReorderChoicesCommand(self.node_model, new_choices, self.choices, self.structure_changed)
            self.undo_stack.push(cmd)
            self.choices = new_choices
            # No need to refresh list manually right now, but signal will handle future sync
            self.structure_changed.emit()
        else:
            self.choices = new_choices
            self.structure_changed.emit()

    def add_choice(self):
        new_choice = {
            "id": str(uuid.uuid4()),
            "text": "Nouveau Choix", 
            "target_node_id": "", 
            "condition": "",
            "is_one_shot": False,
            "after_use": "delete",
            "events": []
        }
        
        if self.undo_stack is not None and self.node_model:
            new_list = self.choices + [new_choice]
            cmd = EditChoiceCommand(self.node_model, new_list, self.choices, self.structure_changed)
            self.undo_stack.push(cmd)
            self.choices = new_list
            self.refresh_list()
            self.structure_changed.emit()
        else:
            self.choices.append(new_choice)
            self.refresh_list()
            self.structure_changed.emit()

    def remove_choice(self, choice_data):
        if choice_data in self.choices:
            if self.undo_stack is not None and self.node_model:
                new_list = self.choices.copy()
                new_list.remove(choice_data)
                cmd = EditChoiceCommand(self.node_model, new_list, self.choices, self.structure_changed)
                self.undo_stack.push(cmd)
                self.choices = new_list
                self.refresh_list()
                self.structure_changed.emit()
            else:
                self.choices.remove(choice_data)
                self.refresh_list()
                self.structure_changed.emit()

    def copy_choice(self, choice_data):
        import json
        clipboard = QApplication.clipboard()
        # Wrap in list for consistency with multi-copy
        data = json.dumps([choice_data])
        clipboard.setText(data)

    def paste_choices(self):
        import json
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        try:
            new_choices = json.loads(text)
            if isinstance(new_choices, list):
                # Assign new IDs
                for c in new_choices:
                    c["id"] = str(uuid.uuid4())
                
                if self.undo_stack is not None and self.node_model:
                    final_list = self.choices + new_choices
                    cmd = EditChoiceCommand(self.node_model, final_list, self.choices, self.structure_changed)
                    self.undo_stack.push(cmd)
                    self.choices = final_list
                    self.refresh_list()
                    self.structure_changed.emit()
                else:
                    self.choices.extend(new_choices)
                    self.refresh_list()
                    self.structure_changed.emit()
        except Exception as e:
            print(f"Paste error: {e}")

    def on_item_toggled(self, item, widget, checked):
        # We rely on the animation valueChanged signal to update the layout in real-time.
        # However, we also need to ensure the final state is correct.
        
        # If expanding, we might need to set the size hint to a large value initially?
        # No, if we update real-time, it should grow.
        
        # But we need to make sure the CollapsibleBox target height is correct.
        # CollapsibleBox.on_pressed handles the animation start.
        
        # We just need to trigger an initial layout update to start the process?
        # Or maybe just let the animation drive it.
        pass

    def _update_item_size(self, item, widget):
        item.setSizeHint(widget.sizeHint())
        self.list_widget.doItemsLayout()


class TextVariantItemWidget(QFrame):
    removed = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, variant_data):
        super().__init__()
        self.variant_data = variant_data
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("QFrame { background-color: #444; border-radius: 5px; margin-bottom: 5px; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        # Header: Condition + Remove
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Condition:"))
        
        self.inp_condition = QLineEdit(variant_data.get("condition", ""))
        self.inp_condition.setPlaceholderText("Ex: $visits == 0")
        self.inp_condition.textChanged.connect(self.on_change)
        header_layout.addWidget(self.inp_condition)
        
        btn_remove = QPushButton("X")
        btn_remove.setFixedSize(20, 20)
        btn_remove.setStyleSheet("background-color: #d9534f; color: white; border: none; border-radius: 3px;")
        btn_remove.clicked.connect(self.remove_self)
        header_layout.addWidget(btn_remove)
        
        layout.addLayout(header_layout)
        
        # Text Area
        self.inp_text = QTextEdit()
        self.inp_text.setPlaceholderText("Texte de la variante...")
        self.inp_text.setMaximumHeight(80)
        self.inp_text.setPlainText(variant_data.get("text", ""))
        self.inp_text.textChanged.connect(self.on_change)
        layout.addWidget(self.inp_text)

    def on_change(self):
        self.variant_data["condition"] = self.inp_condition.text()
        self.variant_data["text"] = self.inp_text.toPlainText()
        self.changed.emit()

    def remove_self(self):
        self.removed.emit()


class TextVariantEditorWidget(QWidget):
    """Widget pour gérer les variantes de texte."""
    data_changed = pyqtSignal()
    structure_changed = pyqtSignal()
    
    def __init__(self, undo_stack=None):
        super().__init__()
        self.variants = []
        self.undo_stack = undo_stack
        self.node_model = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: transparent;")
        
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background-color: transparent;")
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.container_layout.setSpacing(5)
        
        self.scroll_area.setWidget(self.container_widget)
        layout.addWidget(self.scroll_area)
        
        # Add Button
        self.btn_add = QPushButton("Ajouter une Variante")
        self.btn_add.setStyleSheet("background-color: #5cb85c; padding: 5px;")
        self.btn_add.clicked.connect(self.add_variant)
        layout.addWidget(self.btn_add)
        
        self.structure_changed.connect(self._reload_from_model)
        self.structure_changed.connect(self.data_changed.emit)

    def set_variants(self, variants, node_model=None):
        self.variants = variants if variants else []
        self.node_model = node_model
        self.refresh_list()
        
    def _reload_from_model(self):
        if self.node_model:
            self.variants = copy.deepcopy(self.node_model.content.get("text_variants", []))
            self.refresh_list()

    def refresh_list(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        for v in self.variants:
            self._create_variant_widget(v)

    def _create_variant_widget(self, variant_data):
        item = TextVariantItemWidget(variant_data)
        item.removed.connect(lambda: self.remove_variant(item))
        item.changed.connect(self.data_changed.emit)
        self.container_layout.addWidget(item)

    def add_variant(self):
        new_variant = {
            "condition": "$visits > 0",
            "text": "Nouveau texte..."
        }
        
        if self.undo_stack is not None and self.node_model:
            new_list = self.variants + [new_variant]
            cmd = EditNodeDictKeyCommand(self.node_model, "content", "text_variants", new_list, self.variants, self.structure_changed)
            self.undo_stack.push(cmd)
            self.variants = new_list
            self.refresh_list()
            self.structure_changed.emit()
        else:
            self.variants.append(new_variant)
            self._create_variant_widget(new_variant)
            self.structure_changed.emit()

    def remove_variant(self, item_widget):
        if item_widget.variant_data in self.variants:
            if self.undo_stack is not None and self.node_model:
                new_list = self.variants.copy()
                new_list.remove(item_widget.variant_data)
                cmd = EditNodeDictKeyCommand(self.node_model, "content", "text_variants", new_list, self.variants, self.structure_changed)
                self.undo_stack.push(cmd)
                self.variants = new_list
                self.refresh_list()
                self.structure_changed.emit()
            else:
                self.variants.remove(item_widget.variant_data)
                self.structure_changed.emit()


class InspectorPanel(QWidget):
    """
    Panneau latéral pour éditer les propriétés du nœud sélectionné.
    """
    data_changed = pyqtSignal() # Signal global pour rafraîchir la scène

    def __init__(self, undo_stack=None):
        super().__init__()
        self.current_node_item = None
        self.project = None
        self.undo_stack = undo_stack
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # En-tête
        self.lbl_header = QLabel("Propriétés du Nœud")
        self.lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_header.setStyleSheet("background: #333; color: white; padding: 10px; font-weight: bold;")
        self.layout.addWidget(self.lbl_header)

        # Style CSS pour les sous-panneaux
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox {
                background-color: #3c3c3c;
                border: 1px solid #555;
                color: #ffffff;
                padding: 4px;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                top: -1px; 
            }
            QTabBar::tab {
                background: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
                padding: 8px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background: #505050;
                font-weight: bold;
                border-bottom-color: #505050;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QScrollArea {
                border: none;
            }
        """)

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tab 1: Général
        self.tab_general = QWidget()
        self.layout_general = QVBoxLayout(self.tab_general)
        self.layout_general.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.form_general = QFormLayout()
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Titre du nœud...")
        self.txt_title.editingFinished.connect(self.on_title_changed)
        self.form_general.addRow("Titre :", self.txt_title)
        
        self.layout_general.addLayout(self.form_general)
        self.tabs.addTab(self.tab_general, "Général")

        # Tab 2: Logique
        self.tab_logic = QWidget()
        self.layout_logic = QVBoxLayout(self.tab_logic)
        self.layout_logic.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.editor_on_enter = EventEditorWidget("On Enter", undo_stack=self.undo_stack)
        self.editor_on_enter.data_changed.connect(self.on_logic_changed)
        self.layout_logic.addWidget(QLabel("<b>À l'entrée de la scène :</b>"))
        self.layout_logic.addWidget(self.editor_on_enter)
        
        self.tabs.addTab(self.tab_logic, "Logique")

        # Tab 3: Choix
        self.tab_choices = QWidget()
        self.layout_choices = QVBoxLayout(self.tab_choices)
        self.layout_choices.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.editor_choices = ChoiceEditorWidget(undo_stack=self.undo_stack)
        self.editor_choices.data_changed.connect(self.on_choices_changed)
        self.layout_choices.addWidget(self.editor_choices)
        
        self.tabs.addTab(self.tab_choices, "Choix")

        # Tab 4: Texte (Variantes)
        self.tab_text = QWidget()
        self.layout_text = QVBoxLayout(self.tab_text)
        self.layout_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Default Text (Read-Only View)
        self.layout_text.addWidget(QLabel("<b>Texte par défaut (éditable dans le graphe) :</b>"))
        self.txt_default_preview = QTextEdit()
        self.txt_default_preview.setPlaceholderText("Texte par défaut (éditable dans le graphe)...")
        self.txt_default_preview.setReadOnly(True)
        self.txt_default_preview.setMaximumHeight(80)
        self.txt_default_preview.setStyleSheet("color: #aaa; font-style: italic;")
        self.layout_text.addWidget(self.txt_default_preview)
        
        self.layout_text.addWidget(QLabel("<b>Variantes Conditionnelles :</b>"))
        self.editor_variants = TextVariantEditorWidget(undo_stack=self.undo_stack)
        self.editor_variants.data_changed.connect(self.on_variants_changed)
        self.layout_text.addWidget(self.editor_variants)
        
        self.tabs.addTab(self.tab_text, "Texte")

        # État initial
        self.set_visible_editors(False)
        self._is_loading = False

    def set_project(self, project):
        self.project = project

    def set_visible_editors(self, visible):
        self.tabs.setVisible(visible)
        if not visible:
            self.lbl_header.setText("Aucune sélection")
        else:
            self.lbl_header.setText("Propriétés du Nœud")

    def set_selection(self, selected_items):
        node_items = [i for i in selected_items if isinstance(i, NodeItem)]

        if not node_items:
            self.current_node_item = None
            self.set_visible_editors(False)
            return

        # On prend le premier nœud sélectionné
        self.current_node_item = node_items[0]
        self.set_visible_editors(True)
        self.lbl_header.setText(f"Nœud : {self.current_node_item.model.title}")

        # Charger les données dans les champs
        self._load_data_from_node(self.current_node_item.model)

    def _load_data_from_node(self, node_model):
        self._is_loading = True
        
        # General
        self.txt_title.setText(node_model.title)
        
        # Logic
        self.editor_on_enter.set_events(node_model.logic.get("on_enter", []), project=self.project, node_model=node_model)
        
        # Choices
        self.editor_choices.set_choices(node_model.content.get("choices", []), project=self.project, node_model=node_model)
        
        # Text
        self.txt_default_preview.setPlainText(node_model.content.get("text", ""))
        self.editor_variants.set_variants(copy.deepcopy(node_model.content.get("text_variants", [])), node_model=node_model)
        
        self._is_loading = False

    def on_title_changed(self):
        if self.current_node_item and not self._is_loading:
            new_title = self.txt_title.text().strip()
            old_title = self.current_node_item.model.title
            
            if new_title == old_title:
                return
            
            # Check Uniqueness
            if self.project:
                for node in self.project.nodes.values():
                    if node.id != self.current_node_item.model.id and node.title == new_title:
                        # Duplicate found
                        # Revert to old title
                        self.txt_title.setText(old_title)
                        # Optional: Could show a tooltip or flash red, but revert is safest simple logic
                        print(f"[Inspector] Duplicate scene name '{new_title}' rejected.")
                        return

            if self.undo_stack is not None:
                cmd = EditNodePropertyCommand(
                    self.current_node_item.model, 
                    "title", 
                    new_title, 
                    old_title, 
                    self.data_changed
                )
                self.undo_stack.push(cmd)
            else:
                self.current_node_item.model.title = new_title
                self.data_changed.emit()
            
            self.current_node_item.update_preview()
            self.lbl_header.setText(f"Nœud : {new_title}")

    def on_logic_changed(self):
        if self.current_node_item and not self._is_loading:
            new_logic = self.current_node_item.model.logic.copy()
            new_logic["on_enter"] = self.editor_on_enter.events
            old_logic = self.current_node_item.model.logic
            
            if new_logic == old_logic:
                return

            if self.undo_stack is not None:
                cmd = EditNodePropertyCommand(
                    self.current_node_item.model,
                    "logic",
                    new_logic,
                    old_logic,
                    self.data_changed
                )
                self.undo_stack.push(cmd)
            else:
                self.current_node_item.model.logic = new_logic
                self.data_changed.emit()

    def on_choices_changed(self):
        if self.current_node_item and not self._is_loading:
            self.current_node_item.model.content["choices"] = self.editor_choices.choices
            self.current_node_item.update_preview()
            self.data_changed.emit()

    def on_variants_changed(self):
        if self.current_node_item and not self._is_loading:
            new_content = self.current_node_item.model.content.copy()
            new_content["text_variants"] = self.editor_variants.variants
            old_content = self.current_node_item.model.content
            
            if new_content == old_content:
                return

            if self.undo_stack is not None:
                cmd = EditNodePropertyCommand(
                    self.current_node_item.model,
                    "content",
                    new_content,
                    old_content,
                    self.data_changed
                )
                self.undo_stack.push(cmd)
            else:
                self.current_node_item.model.content = new_content
                self.data_changed.emit()
