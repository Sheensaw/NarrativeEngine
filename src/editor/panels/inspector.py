# src/editor/panels/inspector.py
import sys
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QComboBox, QPushButton, 
    QScrollArea, QFrame, QCheckBox, QSpinBox, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.editor.graph.node_item import NodeItem
from src.core.definitions import MACRO_DEFINITIONS


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
        lbl_type.setStyleSheet("color: #ddd;")
        header_layout.addWidget(lbl_type)
        
        header_layout.addStretch()
        
        btn_remove = QPushButton("X")
        btn_remove.setFixedSize(20, 20)
        btn_remove.setStyleSheet("background-color: #d9534f; color: white; border: none; border-radius: 3px;")
        btn_remove.clicked.connect(self.remove_self)
        header_layout.addWidget(btn_remove)
        
        layout.addLayout(header_layout)
        
        # Body (Macro Editor)
        self.macro_editor = MacroEditorWidget(project=self.project)
        self.macro_editor.set_macro_type(macro_type, event_data.get('parameters', {}))
        self.macro_editor.data_changed.connect(self.on_params_changed)
        layout.addWidget(self.macro_editor)

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
            child = self.container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
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
        
        # Compact Layout
        # Row 1: Text | Target | Remove
        row1 = QHBoxLayout()
        
        self.inp_text = QLineEdit(choice_data.get("text", ""))
        self.inp_text.setPlaceholderText("Texte du choix...")
        self.inp_text.textChanged.connect(self.on_change)
        row1.addWidget(self.inp_text, 2)
        
        self.combo_target = QComboBox()
        self.combo_target.setEditable(True)
        self.combo_target.addItem("", "")
        if self.project:
            for node in self.project.nodes.values():
                self.combo_target.addItem(node.title, node.id)
        
        # Set current target
        target_id = choice_data.get("target_node_id", "")
        idx = self.combo_target.findData(target_id)
        if idx >= 0:
            self.combo_target.setCurrentIndex(idx)
        else:
            self.combo_target.setEditText(target_id)
            
        self.combo_target.currentIndexChanged.connect(self.on_target_changed)
        self.combo_target.editTextChanged.connect(self.on_target_text_changed)
        row1.addWidget(self.combo_target, 2)
        
        btn_remove = QPushButton("X")
        btn_remove.setFixedSize(20, 20)
        btn_remove.setStyleSheet("background-color: #d9534f; color: white; border: none; border-radius: 3px;")
        btn_remove.clicked.connect(self.remove_self)
        row1.addWidget(btn_remove)
        
        layout.addLayout(row1)
        
        # Row 2: Condition | One-Shot | After Use
        row2 = QHBoxLayout()
        
        self.inp_cond = QLineEdit(choice_data.get("condition", ""))
        self.inp_cond.setPlaceholderText("Condition (ex: gold >= 10)")
        self.inp_cond.textChanged.connect(self.on_change)
        row2.addWidget(self.inp_cond)
        
        self.chk_oneshot = QCheckBox("Unique")
        self.chk_oneshot.setChecked(choice_data.get("is_one_shot", False))
        self.chk_oneshot.stateChanged.connect(self.on_oneshot_changed)
        row2.addWidget(self.chk_oneshot)
        
        self.combo_after = QComboBox()
        self.combo_after.addItems(["Disparaître", "Remplacer"])
        current_after = choice_data.get("after_use", "delete")
        self.combo_after.setCurrentIndex(0 if current_after == "delete" else 1)
        self.combo_after.currentIndexChanged.connect(self.on_after_changed)
        # Only visible if oneshot is checked
        self.combo_after.setVisible(self.chk_oneshot.isChecked())
        row2.addWidget(self.combo_after)
        
        layout.addLayout(row2)
        
        # Event Editor (Collapsible or just below)
        self.event_editor = EventEditorWidget("Événements")
        self.event_editor.set_events(choice_data.get("events", []), project=self.project)
        self.event_editor.data_changed.connect(self.on_events_changed)
        layout.addWidget(self.event_editor)

    def remove_self(self):
        self.removed.emit()
        self.deleteLater()

    def on_change(self):
        self.choice_data["text"] = self.inp_text.text()
        self.choice_data["condition"] = self.inp_cond.text()
        self.changed.emit()

    def on_target_changed(self, index):
        data = self.combo_target.itemData(index)
        if data:
            self.choice_data["target_node_id"] = data
            self.changed.emit()

    def on_target_text_changed(self, text):
        self.choice_data["target_node_id"] = text
        self.changed.emit()
        
    def on_oneshot_changed(self, state):
        is_checked = bool(state)
        self.choice_data["is_one_shot"] = is_checked
        self.combo_after.setVisible(is_checked)
        self.changed.emit()
        
    def on_after_changed(self, index):
        self.choice_data["after_use"] = "delete" if index == 0 else "replace"
        self.changed.emit()
        
    def on_events_changed(self):
        self.choice_data["events"] = self.event_editor.events
        self.changed.emit()


class ChoiceEditorWidget(QWidget):
    """Widget pour éditer les choix avec une UI ergonomique."""
    
    data_changed = pyqtSignal()
    
    def __init__(self, title="Choix"):
        super().__init__()
        self.choices = []
        self.project = None
        
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
        self.btn_add = QPushButton("Ajouter un Choix")
        self.btn_add.setStyleSheet("background-color: #5cb85c; padding: 5px;")
        self.btn_add.clicked.connect(self.add_choice)
        layout.addWidget(self.btn_add)

    def set_choices(self, choices, project=None):
        self.choices = choices if choices else []
        self.project = project
        self.refresh_list()

    def refresh_list(self):
        while self.container_layout.count():
            child = self.container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for c in self.choices:
            self._create_choice_widget(c)

    def _create_choice_widget(self, choice_data):
        item = ChoiceItemWidget(choice_data, self.project)
        item.removed.connect(lambda: self.remove_choice(item))
        item.changed.connect(self.data_changed.emit)
        self.container_layout.addWidget(item)

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
        self.choices.append(new_choice)
        self._create_choice_widget(new_choice)
        self.data_changed.emit()

    def remove_choice(self, item_widget):
        if item_widget.choice_data in self.choices:
            self.choices.remove(item_widget.choice_data)
        self.data_changed.emit()


class InspectorPanel(QWidget):
    """
    Panneau latéral affichant les propriétés de l'objet sélectionné.
    Organisé avec des onglets/groupes pliables (QToolBox).
    """

    def __init__(self):
        super().__init__()
        self.current_node_item = None
        self.project = None
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Titre du panneau
        self.lbl_header = QLabel("Propriétés")
        self.lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_header.setStyleSheet("background-color: #333; color: white; padding: 10px; font-weight: bold;")
        self.layout.addWidget(self.lbl_header)

        # Stylesheet global pour le panneau
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555;
                color: #ffffff;
                padding: 4px;
            }
            QGroupBox {
                border: 1px solid #555;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }
            QToolBox::tab {
                background: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
            }
            QToolBox::tab:selected {
                background: #505050;
                font-weight: bold;
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

        # Scroll Area principal pour tout le panneau
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: transparent;")
        self.layout.addWidget(self.scroll_area)

        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background-color: transparent;")
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.container_layout.setSpacing(15)
        self.scroll_area.setWidget(self.container_widget)

        # --- Section 1: Général ---
        self.group_general = QGroupBox("Général")
        self.layout_general = QVBoxLayout(self.group_general)
        
        self.form_general = QFormLayout()
        self.txt_title = QLineEdit()
        self.txt_title.textChanged.connect(self.on_title_changed)
        self.form_general.addRow("Titre :", self.txt_title)
        self.layout_general.addLayout(self.form_general)

        self.layout_general.addWidget(QLabel("Contenu :"))
        self.txt_content = QTextEdit()
        self.txt_content.setPlaceholderText("Texte du dialogue ou de la description...")
        self.txt_content.textChanged.connect(self.on_content_changed)
        self.layout_general.addWidget(self.txt_content)
        
        self.container_layout.addWidget(self.group_general)

        # --- Section 2: Logique (Events) ---
        self.group_logic = QGroupBox("Logique & Événements")
        self.layout_logic = QVBoxLayout(self.group_logic)
        
        self.editor_on_enter = EventEditorWidget("On Enter")
        self.editor_on_enter.data_changed.connect(self.on_logic_changed)
        self.layout_logic.addWidget(QLabel("<b>À l'entrée de la scène :</b>"))
        self.layout_logic.addWidget(self.editor_on_enter)
        
        self.container_layout.addWidget(self.group_logic)

        # --- Section 3: Choix ---
        self.group_choices = QGroupBox("Choix & Navigation")
        self.layout_choices = QVBoxLayout(self.group_choices)
        
        self.editor_choices = ChoiceEditorWidget()
        self.editor_choices.data_changed.connect(self.on_choices_changed)
        self.layout_choices.addWidget(self.editor_choices)
        
        self.container_layout.addWidget(self.group_choices)

        # État initial
        self.set_visible_editors(False)

    def set_project(self, project):
        self.project = project

    def set_visible_editors(self, visible):
        self.container_widget.setVisible(visible)
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

        self.current_node_item = node_items[0]
        self._load_data_from_node()
        self.set_visible_editors(True)

    def _load_data_from_node(self):
        if not self.current_node_item:
            return

        model = self.current_node_item.model

        self.txt_title.blockSignals(True)
        self.txt_content.blockSignals(True)
        self.editor_on_enter.blockSignals(True)
        self.editor_choices.blockSignals(True)

        self.txt_title.setText(model.title)
        self.txt_content.setText(model.content.get("text", ""))
        
        # Load Events
        logic = model.logic
        self.editor_on_enter.set_events(logic.get("on_enter", []), project=self.project)
        
        # Load Choices
        self.editor_choices.set_choices(model.content.get("choices", []), project=self.project)

        self.txt_title.blockSignals(False)
        self.txt_content.blockSignals(False)
        self.editor_on_enter.blockSignals(False)
        self.editor_choices.blockSignals(False)

    def on_title_changed(self, text):
        if self.current_node_item:
            self.current_node_item.model.title = text
            self.current_node_item._title_item.setPlainText(text)

    def on_content_changed(self):
        if self.current_node_item:
            text = self.txt_content.toPlainText()
            self.current_node_item.model.content["text"] = text
            self.current_node_item.update_preview()

    def on_logic_changed(self):
        if self.current_node_item:
            self.current_node_item.model.logic["on_enter"] = self.editor_on_enter.events

    def on_choices_changed(self):
        if self.current_node_item:
            self.current_node_item.model.content["choices"] = self.editor_choices.choices
            self.current_node_item.update_preview()