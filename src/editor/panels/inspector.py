# src/editor/panels/inspector.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QLabel, QGroupBox)
from PyQt6.QtCore import Qt

from src.editor.graph.node_item import NodeItem


class InspectorPanel(QWidget):
    """
    Panneau latéral affichant les propriétés de l'objet sélectionné.
    Permet d'éditer le titre et le contenu (texte) d'un nœud.
    """

    def __init__(self):
        super().__init__()
        self.current_node_item = None

        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Titre du panneau
        self.lbl_header = QLabel("Propriétés")
        self.lbl_header.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        self.layout.addWidget(self.lbl_header)

# src/editor/panels/inspector.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QLabel, QGroupBox, 
                             QPushButton, QComboBox, QHBoxLayout, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal

from src.editor.graph.node_item import NodeItem


class EventEditorWidget(QWidget):
    """Widget pour éditer une liste d'événements structurés."""
    
    data_changed = pyqtSignal()

    def __init__(self, title="Événements"):
        super().__init__()
        self.events = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_title = QLabel(title)
        layout.addWidget(self.lbl_title)
        
        # Liste des events
        self.list_events = QListWidget()
        self.list_events.setMaximumHeight(100)
        layout.addWidget(self.list_events)
        
        # Contrôles d'ajout
        add_layout = QHBoxLayout()
        
        self.combo_type = QComboBox()
        self.combo_type.addItems(["setVariable", "addItem", "removeItem", "startQuest", "completeQuest"])
        add_layout.addWidget(self.combo_type)
        
        self.btn_add = QPushButton("+")
        self.btn_add.setFixedWidth(30)
        self.btn_add.clicked.connect(self.add_event)
        add_layout.addWidget(self.btn_add)
        
        self.btn_del = QPushButton("-")
        self.btn_del.setFixedWidth(30)
        self.btn_del.clicked.connect(self.remove_event)
        add_layout.addWidget(self.btn_del)
        
        layout.addLayout(add_layout)
        
        # Édition des paramètres (simplifié : inputs texte)
        self.form_params = QFormLayout()
        self.input_param1 = QLineEdit()
        self.input_param1.setPlaceholderText("Param 1 (ex: nom variable / item_id)")
        self.input_param2 = QLineEdit()
        self.input_param2.setPlaceholderText("Param 2 (ex: valeur / qté)")
        
        self.form_params.addRow("Arg 1:", self.input_param1)
        self.form_params.addRow("Arg 2:", self.input_param2)
        
        layout.addLayout(self.form_params)

    def set_events(self, events):
        self.events = events if events else []
        self.refresh_list()

    def refresh_list(self):
        self.list_events.clear()
        for ev in self.events:
            t = ev.get('type', 'unknown')
            p = ev.get('parameters', {})
            self.list_events.addItem(f"{t}: {p}")

    def add_event(self):
        ev_type = self.combo_type.currentText()
        p1 = self.input_param1.text()
        p2 = self.input_param2.text()
        
        params = {}
        if ev_type == "setVariable":
            params = {"name": p1, "value": p2}
        elif ev_type in ["addItem", "removeItem"]:
            params = {"item_id": p1, "qty": p2}
        elif ev_type in ["startQuest", "completeQuest"]:
            params = {"quest_id": p1}
            
        self.events.append({"type": ev_type, "parameters": params})
        self.refresh_list()
        self.data_changed.emit()
        
        # Reset inputs
        self.input_param1.clear()
        self.input_param2.clear()

    def remove_event(self):
        row = self.list_events.currentRow()
        if row >= 0:
            self.events.pop(row)
            self.refresh_list()
            self.data_changed.emit()


class ChoiceEditorWidget(QWidget):
    """Widget pour éditer les choix et leurs liens."""
    
    data_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.choices = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("Choix / Navigation"))
        
        self.list_choices = QListWidget()
        self.list_choices.setMaximumHeight(120)
        self.list_choices.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_choices)
        
        # Contrôles
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Ajouter Choix")
        self.btn_add.clicked.connect(self.add_choice)
        btn_layout.addWidget(self.btn_add)
        
        self.btn_del = QPushButton("Supprimer")
        self.btn_del.clicked.connect(self.remove_choice)
        btn_layout.addWidget(self.btn_del)
        
        layout.addLayout(btn_layout)
        
        # Édition du choix sélectionné
        self.edit_group = QGroupBox("Détails Choix")
        form = QFormLayout(self.edit_group)
        
        self.inp_text = QLineEdit()
        self.inp_text.textChanged.connect(self.update_current_choice)
        
        self.inp_target = QLineEdit() # Pour l'instant un ID manuel, idéalement une ComboBox
        self.inp_target.setPlaceholderText("ID du Nœud Cible")
        self.inp_target.textChanged.connect(self.update_current_choice)
        
        self.inp_cond = QLineEdit()
        self.inp_cond.setPlaceholderText("Condition (ex: gold >= 10)")
        self.inp_cond.textChanged.connect(self.update_current_choice)
        
        form.addRow("Texte:", self.inp_text)
        form.addRow("Cible (ID):", self.inp_target)
        form.addRow("Condition:", self.inp_cond)
        
        layout.addWidget(self.edit_group)
        self.edit_group.setEnabled(False)

    def set_choices(self, choices):
        self.choices = choices if choices else []
        self.refresh_list()

    def refresh_list(self):
        self.list_choices.clear()
        for c in self.choices:
            txt = c.get('text', 'Choix')
            tgt = c.get('target_node_id', '?')
            self.list_choices.addItem(f"{txt} -> {tgt}")

    def add_choice(self):
        self.choices.append({"text": "Nouveau Choix", "target_node_id": "", "condition": ""})
        self.refresh_list()
        self.data_changed.emit()

    def remove_choice(self):
        row = self.list_choices.currentRow()
        if row >= 0:
            self.choices.pop(row)
            self.refresh_list()
            self.data_changed.emit()
            self.edit_group.setEnabled(False)

    def on_item_clicked(self, item):
        row = self.list_choices.currentRow()
        if row >= 0:
            c = self.choices[row]
            self.edit_group.setEnabled(True)
            self.inp_text.blockSignals(True)
            self.inp_target.blockSignals(True)
            self.inp_cond.blockSignals(True)
            
            self.inp_text.setText(c.get("text", ""))
            self.inp_target.setText(c.get("target_node_id", ""))
            self.inp_cond.setText(c.get("condition", ""))
            
            self.inp_text.blockSignals(False)
            self.inp_target.blockSignals(False)
            self.inp_cond.blockSignals(False)

    def update_current_choice(self):
        row = self.list_choices.currentRow()
        if row >= 0:
            self.choices[row]["text"] = self.inp_text.text()
            self.choices[row]["target_node_id"] = self.inp_target.text()
            self.choices[row]["condition"] = self.inp_cond.text()
            
            # Update list item text without full refresh
            self.list_choices.item(row).setText(f"{self.inp_text.text()} -> {self.inp_target.text()}")
            self.data_changed.emit()


class InspectorPanel(QWidget):
    """
    Panneau latéral affichant les propriétés de l'objet sélectionné.
    """

    def __init__(self):
        super().__init__()
        self.current_node_item = None
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Titre du panneau
        self.lbl_header = QLabel("Propriétés")
        self.lbl_header.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        self.layout.addWidget(self.lbl_header)

        # Formulaire principal
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)

        self.txt_title = QLineEdit()
        self.txt_title.textChanged.connect(self.on_title_changed)
        
        self.txt_content = QTextEdit()
        self.txt_content.setPlaceholderText("Écrivez le dialogue ici...")
        self.txt_content.setMaximumHeight(100)
        self.txt_content.textChanged.connect(self.on_content_changed)
        
        self.form_layout.addRow("Titre :", self.txt_title)
        self.form_layout.addRow("Contenu :", self.txt_content)
        
        self.layout.addWidget(self.form_widget)

        # --- Event Editors ---
        self.editor_on_enter = EventEditorWidget("On Enter")
        self.editor_on_enter.data_changed.connect(self.on_logic_changed)
        self.layout.addWidget(self.editor_on_enter)

        self.editor_on_exit = EventEditorWidget("On Exit")
        self.editor_on_exit.data_changed.connect(self.on_logic_changed)
        self.layout.addWidget(self.editor_on_exit)

        # --- Choice Editor ---
        self.editor_choices = ChoiceEditorWidget()
        self.editor_choices.data_changed.connect(self.on_choices_changed)
        self.layout.addWidget(self.editor_choices)

        self.layout.addStretch()

        # État initial
        self.set_visible_editors(False)

    def set_visible_editors(self, visible):
        self.form_widget.setVisible(visible)
        self.editor_on_enter.setVisible(visible)
        self.editor_on_exit.setVisible(visible)
        self.editor_choices.setVisible(visible)

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
        self.editor_on_exit.blockSignals(True)
        self.editor_choices.blockSignals(True)

        self.txt_title.setText(model.title)
        self.txt_content.setText(model.content.get("text", ""))
        
        # Load Events
        logic = model.logic
        self.editor_on_enter.set_events(logic.get("on_enter", []))
        self.editor_on_exit.set_events(logic.get("on_exit", []))
        
        # Load Choices
        self.editor_choices.set_choices(model.content.get("choices", []))

        self.txt_title.blockSignals(False)
        self.txt_content.blockSignals(False)
        self.editor_on_enter.blockSignals(False)
        self.editor_on_exit.blockSignals(False)
        self.editor_choices.blockSignals(False)

    def on_title_changed(self, text):
        if self.current_node_item:
            self.current_node_item.model.title = text
            self.current_node_item._title_item.setPlainText(text)

    def on_content_changed(self):
        if self.current_node_item:
            self.current_node_item.model.content["text"] = self.txt_content.toPlainText()

    def on_logic_changed(self):
        if self.current_node_item:
            self.current_node_item.model.logic["on_enter"] = self.editor_on_enter.events
            self.current_node_item.model.logic["on_exit"] = self.editor_on_exit.events

    def on_choices_changed(self):
        if self.current_node_item:
            self.current_node_item.model.content["choices"] = self.editor_choices.choices
            # Note: Updating edges in the graph based on choices is complex and requires
            # access to the Scene/Graph. For now, we just save the data.
            # Ideally, the GraphScene should listen to changes in the model or Inspector.