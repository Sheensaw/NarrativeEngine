# src/editor/panels/database_panel.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QListWidget, QListWidgetItem, QPushButton,
                             QFormLayout, QLineEdit, QTextEdit, QComboBox,
                             QLabel, QDoubleSpinBox, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt
from src.core.models import ItemModel, QuestModel, ProjectModel


class DatabasePanel(QWidget):
    """
    Panneau de gestion de la base de données (Items, Quêtes, Variables).
    """

    def __init__(self, project_model: ProjectModel = None):
        super().__init__()
        self.project_model = project_model
        self._init_ui()

    def set_project(self, project_model: ProjectModel):
        self.project_model = project_model
        self._refresh_items_list()
        self._refresh_quests_list()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tab Items
        self.tab_items = self._create_items_tab()
        self.tabs.addTab(self.tab_items, "Objets")

        # Tab Quests
        self.tab_quests = self._create_quests_tab()
        self.tabs.addTab(self.tab_quests, "Quêtes")

        # Tab Variables
        self.tab_vars = self._create_variables_tab()
        self.tabs.addTab(self.tab_vars, "Variables")

    def _create_variables_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Table des variables
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        
        self.vars_table = QTableWidget()
        self.vars_table.setColumnCount(3)
        self.vars_table.setHorizontalHeaderLabels(["Nom", "Valeur", "Type"])
        self.vars_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.vars_table)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Ajouter Variable")
        btn_add.clicked.connect(self._add_variable)
        btn_del = QPushButton("Supprimer")
        btn_del.clicked.connect(self._delete_variable)
        btn_save = QPushButton("Appliquer Changements")
        btn_save.clicked.connect(self._save_variables)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        self._refresh_variables_list()
        return widget

    def _refresh_variables_list(self):
        self.vars_table.setRowCount(0)
        if not self.project_model: return

        row = 0
        for name, value in self.project_model.variables.items():
            self.vars_table.insertRow(row)
            self.vars_table.setItem(row, 0, QTableWidgetItem(name))
            self.vars_table.setItem(row, 1, QTableWidgetItem(str(value)))
            
            type_str = type(value).__name__
            self.vars_table.setItem(row, 2, QTableWidgetItem(type_str))
            row += 1

    def _add_variable(self):
        row = self.vars_table.rowCount()
        self.vars_table.insertRow(row)
        self.vars_table.setItem(row, 0, QTableWidgetItem("new_var"))
        self.vars_table.setItem(row, 1, QTableWidgetItem("0"))
        self.vars_table.setItem(row, 2, QTableWidgetItem("int"))

    def _delete_variable(self):
        current_row = self.vars_table.currentRow()
        if current_row >= 0:
            self.vars_table.removeRow(current_row)

    def _save_variables(self):
        if not self.project_model: return
        
        new_vars = {}
        for row in range(self.vars_table.rowCount()):
            name_item = self.vars_table.item(row, 0)
            val_item = self.vars_table.item(row, 1)
            type_item = self.vars_table.item(row, 2)

            if not name_item or not val_item: continue
            
            name = name_item.text()
            val_str = val_item.text()
            type_str = type_item.text() if type_item else "str"

            # Conversion basique
            value = val_str
            if type_str == "int":
                try: value = int(val_str)
                except: pass
            elif type_str == "float":
                try: value = float(val_str)
                except: pass
            elif type_str == "bool":
                value = val_str.lower() == "true"

            new_vars[name] = value

        self.project_model.variables = new_vars
        QMessageBox.information(self, "Succès", "Variables mises à jour.")

    def _create_items_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Liste à gauche
        list_layout = QVBoxLayout()
        self.items_list = QListWidget()
        self.items_list.itemClicked.connect(self._on_item_selected)
        list_layout.addWidget(self.items_list)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Ajouter")
        btn_add.clicked.connect(self._add_item)
        btn_del = QPushButton("Supprimer")
        btn_del.clicked.connect(self._delete_item)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        list_layout.addLayout(btn_layout)

        layout.addLayout(list_layout, 1)

        # Formulaire à droite
        self.item_form = QWidget()
        form_layout = QFormLayout(self.item_form)

        self.item_name = QLineEdit()
        self.item_name.textChanged.connect(self._save_current_item)
        self.item_type = QComboBox()
        self.item_type.addItems(["misc", "weapon", "armor", "potion", "quest"])
        self.item_type.currentTextChanged.connect(self._save_current_item)
        self.item_desc = QTextEdit()
        self.item_desc.textChanged.connect(self._save_current_item)
        
        form_layout.addRow("Nom :", self.item_name)
        form_layout.addRow("Type :", self.item_type)
        form_layout.addRow("Description :", self.item_desc)

        layout.addWidget(self.item_form, 2)
        self.item_form.setVisible(False)

        self._refresh_items_list()
        return widget

    def _create_quests_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Liste à gauche
        list_layout = QVBoxLayout()
        self.quests_list = QListWidget()
        self.quests_list.itemClicked.connect(self._on_quest_selected)
        list_layout.addWidget(self.quests_list)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Ajouter")
        btn_add.clicked.connect(self._add_quest)
        btn_del = QPushButton("Supprimer")
        btn_del.clicked.connect(self._delete_quest)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        list_layout.addLayout(btn_layout)

        layout.addLayout(list_layout, 1)

        # Formulaire à droite
        self.quest_form = QWidget()
        form_layout = QFormLayout(self.quest_form)

        self.quest_title = QLineEdit()
        self.quest_title.textChanged.connect(self._save_current_quest)
        self.quest_desc = QTextEdit()
        self.quest_desc.textChanged.connect(self._save_current_quest)
        self.quest_main = QCheckBox("Quête Principale")
        self.quest_main.toggled.connect(self._save_current_quest)

        form_layout.addRow("Titre :", self.quest_title)
        form_layout.addRow("Description :", self.quest_desc)
        form_layout.addRow("", self.quest_main)

        layout.addWidget(self.quest_form, 2)
        self.quest_form.setVisible(False)

        self._refresh_quests_list()
        return widget

    # --- ITEMS LOGIC ---
    def _refresh_items_list(self):
        self.items_list.clear()
        if not self.project_model: return
        for item in self.project_model.items.values():
            list_item = QListWidgetItem(item.name)
            list_item.setData(Qt.ItemDataRole.UserRole, item.id)
            self.items_list.addItem(list_item)

    def _add_item(self):
        new_item = ItemModel()
        self.project_model.items[new_item.id] = new_item
        self._refresh_items_list()

    def _delete_item(self):
        current = self.items_list.currentItem()
        if not current: return
        item_id = current.data(Qt.ItemDataRole.UserRole)
        del self.project_model.items[item_id]
        self._refresh_items_list()
        self.item_form.setVisible(False)

    def _on_item_selected(self, list_item):
        item_id = list_item.data(Qt.ItemDataRole.UserRole)
        item = self.project_model.items.get(item_id)
        if not item: return

        self.current_item_id = item_id
        self.item_form.setVisible(True)
        
        self.item_name.blockSignals(True)
        self.item_type.blockSignals(True)
        self.item_desc.blockSignals(True)

        self.item_name.setText(item.name)
        self.item_type.setCurrentText(item.type)
        self.item_desc.setText(item.description)

        self.item_name.blockSignals(False)
        self.item_type.blockSignals(False)
        self.item_desc.blockSignals(False)

    def _save_current_item(self):
        if not hasattr(self, 'current_item_id'): return
        item = self.project_model.items.get(self.current_item_id)
        if not item: return

        item.name = self.item_name.text()
        item.type = self.item_type.currentText()
        item.description = self.item_desc.toPlainText()

        # Update list item text
        current_list_item = self.items_list.currentItem()
        if current_list_item:
            current_list_item.setText(item.name)

    # --- QUESTS LOGIC ---
    def _refresh_quests_list(self):
        self.quests_list.clear()
        if not self.project_model: return
        for quest in self.project_model.quests.values():
            list_item = QListWidgetItem(quest.title)
            list_item.setData(Qt.ItemDataRole.UserRole, quest.id)
            self.quests_list.addItem(list_item)

    def _add_quest(self):
        new_quest = QuestModel()
        self.project_model.quests[new_quest.id] = new_quest
        self._refresh_quests_list()

    def _delete_quest(self):
        current = self.quests_list.currentItem()
        if not current: return
        quest_id = current.data(Qt.ItemDataRole.UserRole)
        del self.project_model.quests[quest_id]
        self._refresh_quests_list()
        self.quest_form.setVisible(False)

    def _on_quest_selected(self, list_item):
        quest_id = list_item.data(Qt.ItemDataRole.UserRole)
        quest = self.project_model.quests.get(quest_id)
        if not quest: return

        self.current_quest_id = quest_id
        self.quest_form.setVisible(True)

        self.quest_title.blockSignals(True)
        self.quest_desc.blockSignals(True)
        self.quest_main.blockSignals(True)

        self.quest_title.setText(quest.title)
        self.quest_desc.setText(quest.description)
        self.quest_main.setChecked(quest.is_main_quest)

        self.quest_title.blockSignals(False)
        self.quest_desc.blockSignals(False)
        self.quest_main.blockSignals(False)

    def _save_current_quest(self):
        if not hasattr(self, 'current_quest_id'): return
        quest = self.project_model.quests.get(self.current_quest_id)
        if not quest: return

        quest.title = self.quest_title.text()
        quest.description = self.quest_desc.toPlainText()
        quest.is_main_quest = self.quest_main.isChecked()

        current_list_item = self.quests_list.currentItem()
        if current_list_item:
            current_list_item.setText(quest.title)
