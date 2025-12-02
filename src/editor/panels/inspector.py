
import sys
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QComboBox, QPushButton, 
    QScrollArea, QFrame, QCheckBox, QSpinBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QTabWidget, QToolButton, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PyQt6.QtGui import QUndoStack, QAction, QIcon

from src.core.commands import ReorderChoicesCommand, EditChoiceCommand

from src.editor.graph.node_item import NodeItem
from src.core.definitions import MACRO_DEFINITIONS


class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.toggle_button = QToolButton(text=title, checkable=True, checked=False)
        self.toggle_button.setStyleSheet("QToolButton { border: none; background-color: #444; color: #eee; padding: 5px; text-align: left; font-weight: bold; } QToolButton:hover { background-color: #555; }")
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self.toggle_button.clicked.connect(self.on_pressed)

        self.content_area = QWidget()
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        self.content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

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

    def __init__(self, title="Événements"):
        super().__init__()
        self.events = []
        self.project = None
        
        layout = QVBoxLayout(self)
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

    def set_events(self, events, project=None):
        self.events = events if events else []
        self.project = project
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
        self.events.append(new_event)
        self._create_event_widget(new_event)
        self.data_changed.emit()

    def remove_event(self, item_widget):
        if item_widget.event_data in self.events:
            self.events.remove(item_widget.event_data)
        self.data_changed.emit()


class ChoiceItemWidget(QFrame):
    removed = pyqtSignal()
    changed = pyqtSignal()

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
        body_layout = QVBoxLayout()
        
        # Target
        row_target = QHBoxLayout()
        row_target.addWidget(QLabel("Cible:"))
        self.combo_target = QComboBox()
        self.combo_target.setEditable(True)
        self.combo_target.addItem("", "")
        if self.project:
            for node in self.project.nodes.values():
                self.combo_target.addItem(f"{node.title} ({node.id})", node.id)
        
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
        # Migrate old "modify_text" to "delete" + check modify text
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
                self.combo_rep_target.addItem(f"{node.title} ({node.id})", node.id)
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


class ChoiceEditorWidget(QWidget):
    """Widget pour éditer les choix avec une UI ergonomique."""
    
    data_changed = pyqtSignal()
    
    def __init__(self, title="Choix", undo_stack=None):
        super().__init__()
        self.choices = []
        self.project = None
        self.undo_stack = undo_stack
        self.node_model = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with Copy/Paste
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Choix</b>"))
        
        self.btn_copy = QPushButton("Copier")
        self.btn_copy.setStyleSheet("background-color: #5bc0de; padding: 3px;")
        self.btn_copy.clicked.connect(self.copy_choices)
        header_layout.addWidget(self.btn_copy)
        
        self.btn_paste = QPushButton("Coller")
        self.btn_paste.setStyleSheet("background-color: #f0ad4e; padding: 3px;")
        self.btn_paste.clicked.connect(self.paste_choices)
        header_layout.addWidget(self.btn_paste)
        
        layout.addLayout(header_layout)
        
        # Scroll Area
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
        self.btn_add = QPushButton("Ajouter un Choix")
        self.btn_add.setStyleSheet("background-color: #5cb85c; padding: 5px;")
        self.btn_add.clicked.connect(self.add_choice)
        layout.addWidget(self.btn_add)

    def set_choices(self, choices, project=None, node_model=None):
        self.choices = choices if choices else []
        self.project = project
        self.node_model = node_model
        self.refresh_list()

    def refresh_list(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        for c in self.choices:
            self._create_choice_widget(c)

    def _create_choice_widget(self, choice_data):
        # Container for row (Item + Buttons)
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(2)
        
        # Reorder Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(0)
        btn_layout.setContentsMargins(0,0,0,0)
        
        btn_up = QToolButton()
        btn_up.setText("▲")
        btn_up.setFixedSize(20, 20)
        btn_up.setStyleSheet("border: none; color: #888;")
        
        btn_down = QToolButton()
        btn_down.setText("▼")
        btn_down.setFixedSize(20, 20)
        btn_down.setStyleSheet("border: none; color: #888;")
        
        btn_layout.addWidget(btn_up)
        btn_layout.addWidget(btn_down)
        row_layout.addLayout(btn_layout)

        # Item
        item = ChoiceItemWidget(choice_data, self.project)
        item.removed.connect(lambda: self.remove_choice(item))
        item.changed.connect(self.data_changed.emit)
        row_layout.addWidget(item)
        
        # Connect buttons
        btn_up.clicked.connect(lambda: self.move_choice_up(item))
        btn_down.clicked.connect(lambda: self.move_choice_down(item))

        self.container_layout.addWidget(row_widget)

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
        
        if self.undo_stack and self.node_model:
            new_list = self.choices + [new_choice]
            cmd = EditChoiceCommand(self.node_model, new_list, self.choices, self.data_changed)
            self.undo_stack.push(cmd)
            self.choices = new_list
            self.refresh_list()
            self.data_changed.emit()
        else:
            self.choices.append(new_choice)
            self._create_choice_widget(new_choice)
            self.data_changed.emit()

    def remove_choice(self, item_widget):
        if item_widget.choice_data in self.choices:
            if self.undo_stack and self.node_model:
                new_list = self.choices.copy()
                new_list.remove(item_widget.choice_data)
                cmd = EditChoiceCommand(self.node_model, new_list, self.choices, self.data_changed)
                self.undo_stack.push(cmd)
                self.choices = new_list
                self.refresh_list()
                self.data_changed.emit()
            else:
                self.choices.remove(item_widget.choice_data)
                self.data_changed.emit()
                self.refresh_list()

    def move_choice_up(self, item_widget):
        if item_widget.choice_data not in self.choices: return
        idx = self.choices.index(item_widget.choice_data)
        if idx > 0:
            new_list = self.choices.copy()
            new_list[idx], new_list[idx-1] = new_list[idx-1], new_list[idx]
            
            if self.undo_stack and self.node_model:
                cmd = ReorderChoicesCommand(self.node_model, new_list, self.choices, self.data_changed)
                self.undo_stack.push(cmd)
                self.choices = new_list
                self.refresh_list()
                self.data_changed.emit()
            else:
                self.choices = new_list
                self.refresh_list()
                self.data_changed.emit()

    def move_choice_down(self, item_widget):
        if item_widget.choice_data not in self.choices: return
        idx = self.choices.index(item_widget.choice_data)
        if idx < len(self.choices) - 1:
            new_list = self.choices.copy()
            new_list[idx], new_list[idx+1] = new_list[idx+1], new_list[idx]
            
            if self.undo_stack and self.node_model:
                cmd = ReorderChoicesCommand(self.node_model, new_list, self.choices, self.data_changed)
                self.undo_stack.push(cmd)
                self.choices = new_list
                self.refresh_list()
                self.data_changed.emit()
            else:
                self.choices = new_list
                self.refresh_list()
                self.data_changed.emit()

    def copy_choices(self):
        import json
        if not self.choices:
            return
        clipboard = QApplication.clipboard()
        # Deep copy
        data = json.dumps(self.choices)
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
                
                if self.undo_stack and self.node_model:
                    final_list = self.choices + new_choices
                    cmd = EditChoiceCommand(self.node_model, final_list, self.choices, self.data_changed)
                    self.undo_stack.push(cmd)
                    self.choices = final_list
                    self.refresh_list()
                    self.data_changed.emit()
                else:
                    self.choices.extend(new_choices)
                    self.refresh_list()
                    self.data_changed.emit()
        except Exception as e:
            print(f"Paste error: {e}")


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
    """Widget pour éditer les variantes de texte."""
    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.variants = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
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

    def set_variants(self, variants):
        self.variants = variants if variants else []
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
        self.variants.append(new_variant)
        self._create_variant_widget(new_variant)
        self.data_changed.emit()

    def remove_variant(self, item_widget):
        if item_widget.variant_data in self.variants:
            self.variants.remove(item_widget.variant_data)
        self.data_changed.emit()


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
        self.txt_title.textChanged.connect(self.on_title_changed)
        self.form_general.addRow("Titre :", self.txt_title)
        
        self.layout_general.addLayout(self.form_general)
        self.tabs.addTab(self.tab_general, "Général")

        # Tab 2: Logique
        self.tab_logic = QWidget()
        self.layout_logic = QVBoxLayout(self.tab_logic)
        self.layout_logic.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.editor_on_enter = EventEditorWidget("On Enter")
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
        self.txt_default_preview.setReadOnly(True)
        self.txt_default_preview.setMaximumHeight(80)
        self.txt_default_preview.setStyleSheet("color: #aaa; font-style: italic;")
        self.layout_text.addWidget(self.txt_default_preview)
        
        self.layout_text.addWidget(QLabel("<b>Variantes Conditionnelles :</b>"))
        self.editor_variants = TextVariantEditorWidget()
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
        self.editor_on_enter.set_events(node_model.logic.get("on_enter", []), project=self.project)
        
        # Choices
        self.editor_choices.set_choices(node_model.content.get("choices", []), project=self.project, node_model=node_model)
        
        # Text
        self.txt_default_preview.setPlainText(node_model.content.get("text", ""))
        self.editor_variants.set_variants(node_model.content.get("text_variants", []))
        
        self._is_loading = False

    def on_title_changed(self, text):
        if self.current_node_item and not self._is_loading:
            self.current_node_item.model.title = text
            self.current_node_item.update_preview()
            self.lbl_header.setText(f"Nœud : {text}")
            self.data_changed.emit()

    def on_logic_changed(self):
        if self.current_node_item and not self._is_loading:
            self.current_node_item.model.logic["on_enter"] = self.editor_on_enter.events
            self.data_changed.emit()

    def on_choices_changed(self):
        if self.current_node_item and not self._is_loading:
            self.current_node_item.model.content["choices"] = self.editor_choices.choices
            self.current_node_item.update_preview()
            self.data_changed.emit()

    def on_variants_changed(self):
        if self.current_node_item and not self._is_loading:
            self.current_node_item.model.content["text_variants"] = self.editor_variants.variants
            self.data_changed.emit()