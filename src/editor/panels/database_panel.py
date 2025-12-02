# src/editor/panels/database_panel.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QListWidget, QListWidgetItem, QPushButton,
                             QFormLayout, QLineEdit, QTextEdit, QComboBox,
                             QLabel, QDoubleSpinBox, QCheckBox, QMessageBox, QSpinBox, QGroupBox, QFileDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt
from src.core.models import ItemModel, QuestModel, ProjectModel, LocationModel
from src.core.database import DatabaseManager


class DatabasePanel(QWidget):
    """
    Panneau de gestion de la base de données (Items, Quêtes, Variables).
    """

    def __init__(self, project_model: ProjectModel = None):
        super().__init__()
        self.project_model = project_model
        # Initialisation du gestionnaire de base de données
        self.db_manager = DatabaseManager()
        self._init_ui()

    def set_project(self, project_model: ProjectModel):
        self.project_model = project_model
        # On essaie de synchroniser avec la DB au chargement
        self._sync_items_from_db()
        self._refresh_items_list()
        self._refresh_quests_list()
        self._refresh_items_list()
        self._refresh_quests_list()
        self._refresh_variables_list()
        self._refresh_locations_list()
        self._sync_locations_from_db()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Styling pour ressembler à un "Drawer"
        self.setStyleSheet("""
            QWidget { background-color: #222; color: #eee; font-family: 'Segoe UI', sans-serif; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #333; color: #aaa; padding: 8px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #444; color: #fff; font-weight: bold; border-bottom: 2px solid #4a90e2; }
            
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background: #2a2a2a; border: 1px solid #555; color: #fff; padding: 6px; border-radius: 4px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border: 1px solid #4a90e2; }
            
            QPushButton {
                background: #4a90e2; color: white; border: none; padding: 8px 12px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #357abd; }
            QPushButton#dangerBtn { background-color: #d9534f; }
            QPushButton#dangerBtn:hover { background-color: #c9302c; }
            QPushButton#successBtn { background-color: #5cb85c; }
            QPushButton#successBtn:hover { background-color: #4cae4c; }
            
            QTreeWidget, QListWidget, QTableWidget { 
                background: #1a1a1a; border: 1px solid #444; border-radius: 4px; outline: none;
            }
            QTreeWidget::item, QListWidget::item { padding: 4px; }
            QTreeWidget::item:selected, QListWidget::item:selected { background: #357abd; color: white; }
            
            QGroupBox { 
                border: 1px solid #444; margin-top: 20px; padding-top: 15px; border-radius: 4px; font-weight: bold; 
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: #aaa; }
        """)

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

        # Tab Locations
        self.tab_locations = self._create_locations_tab()
        self.tabs.addTab(self.tab_locations, "Lieux")

    def _create_variables_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Table des variables
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        
        self.vars_table = QTableWidget()
        self.vars_table.setColumnCount(3)
        self.vars_table.setHorizontalHeaderLabels(["Nom", "Valeur", "Type"])
        self.vars_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vars_table.setStyleSheet("QHeaderView::section { background-color: #333; color: #fff; }")
        layout.addWidget(self.vars_table)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Ajouter Variable")
        btn_add.clicked.connect(self._add_variable)
        btn_del = QPushButton("Supprimer")
        btn_del.setStyleSheet("background-color: #d9534f;")
        btn_del.clicked.connect(self._delete_variable)
        btn_save = QPushButton("Appliquer Changements")
        btn_save.setStyleSheet("background-color: #5cb85c;")
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
        layout.setContentsMargins(10, 10, 10, 10)

        # Liste à gauche
        list_layout = QVBoxLayout()
        
        # Bouton Import JSON
        btn_import = QPushButton("Importer JSON")
        btn_import.setStyleSheet("background-color: #f0ad4e; color: white; font-weight: bold;")
        btn_import.clicked.connect(self._import_items_json)
        list_layout.addWidget(btn_import)
        
        self.items_tree = QTreeWidget()
        self.items_tree.setHeaderHidden(True)
        self.items_tree.itemClicked.connect(self._on_item_selected)
        list_layout.addWidget(self.items_tree)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Ajouter")
        btn_add.clicked.connect(self._add_item)
        btn_del = QPushButton("Supprimer")
        btn_del.setObjectName("dangerBtn")
        btn_del.clicked.connect(self._delete_item)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        list_layout.addLayout(btn_layout)
        
        # Bouton Save to DB
        btn_sync = QPushButton("Sauvegarder en DB")
        btn_sync.setObjectName("successBtn")
        btn_sync.setStyleSheet("margin-top: 5px;") # Keep margin
        btn_sync.clicked.connect(self._save_items_to_db)
        list_layout.addWidget(btn_sync)

        layout.addLayout(list_layout, 1)

        # Formulaire à droite (Scrollable)
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.item_form = QWidget()
        self.item_form.setStyleSheet("background: transparent;")
        form_layout = QFormLayout(self.item_form)

        self.item_name = QLineEdit()
        self.item_name.textChanged.connect(self._save_current_item)
        
        self.item_type = QComboBox()
        self.item_type.addItems(["misc", "weapon", "armor", "food", "potion", "quest", "usable"])
        self.item_type.currentTextChanged.connect(self._on_item_type_changed)

        self.item_desc = QTextEdit()
        self.item_desc.setMaximumHeight(80)
        self.item_desc.textChanged.connect(self._save_current_item)
        
        form_layout.addRow("Nom :", self.item_name)
        form_layout.addRow("Type :", self.item_type)
        form_layout.addRow("Description :", self.item_desc)

        # --- Champs Spécifiques (Armes/Armures) ---
        self.group_stats = QGroupBox("Statistiques de Combat")
        stats_layout = QFormLayout(self.group_stats)
        
        self.inp_subtype = QComboBox()
        self.inp_subtype.addItems(["dagger", "sword", "longsword", "axe", "mace", "pike", "bow", "crossbow"])
        self.inp_subtype.currentTextChanged.connect(self._save_current_item)
        
        self.inp_dmg_min = QSpinBox()
        self.inp_dmg_min.setRange(0, 999)
        self.inp_dmg_min.valueChanged.connect(self._save_current_item)
        
        self.inp_dmg_max = QSpinBox()
        self.inp_dmg_max.setRange(0, 999)
        self.inp_dmg_max.valueChanged.connect(self._save_current_item)
        
        self.inp_crit_chance = QSpinBox()
        self.inp_crit_chance.setRange(0, 100)
        self.inp_crit_chance.setSuffix("%")
        self.inp_crit_chance.valueChanged.connect(self._save_current_item)
        
        self.inp_speed = QDoubleSpinBox()
        self.inp_speed.setRange(0.1, 5.0)
        self.inp_speed.setSingleStep(0.1)
        self.inp_speed.valueChanged.connect(self._save_current_item)

        self.chk_two_handed = QCheckBox("Deux mains")
        self.chk_two_handed.toggled.connect(self._save_current_item)

        stats_layout.addRow("Sous-type :", self.inp_subtype)
        stats_layout.addRow("Dégâts Min :", self.inp_dmg_min)
        stats_layout.addRow("Dégâts Max :", self.inp_dmg_max)
        stats_layout.addRow("Critique :", self.inp_crit_chance)
        stats_layout.addRow("Vitesse :", self.inp_speed)
        stats_layout.addRow("", self.chk_two_handed)
        
        form_layout.addRow(self.group_stats)

        # --- Prérequis ---
        self.group_reqs = QGroupBox("Prérequis")
        reqs_layout = QFormLayout(self.group_reqs)
        
        self.inp_req_str = QSpinBox()
        self.inp_req_str.valueChanged.connect(self._save_current_item)
        self.inp_req_dex = QSpinBox()
        self.inp_req_dex.valueChanged.connect(self._save_current_item)
        self.inp_req_lvl = QSpinBox()
        self.inp_req_lvl.valueChanged.connect(self._save_current_item)
        
        reqs_layout.addRow("Force Min :", self.inp_req_str)
        reqs_layout.addRow("Dextérité Min :", self.inp_req_dex)
        reqs_layout.addRow("Niveau Min :", self.inp_req_lvl)
        
        form_layout.addRow(self.group_reqs)

        # --- Effets ---
        self.group_effects = QGroupBox("Effets Spéciaux")
        effects_layout = QFormLayout(self.group_effects)
        
        self.inp_eff_bleed = QSpinBox()
        self.inp_eff_bleed.valueChanged.connect(self._save_current_item)
        self.inp_eff_poison = QSpinBox()
        self.inp_eff_poison.valueChanged.connect(self._save_current_item)
        
        effects_layout.addRow("Saignement :", self.inp_eff_bleed)
        effects_layout.addRow("Poison :", self.inp_eff_poison)
        
        form_layout.addRow(self.group_effects)

        # --- Nourriture ---
        self.group_food = QGroupBox("Nourriture")
        food_layout = QFormLayout(self.group_food)
        self.inp_food_health = QSpinBox()
        self.inp_food_health.setRange(0, 999)
        self.inp_food_health.valueChanged.connect(self._save_current_item)
        food_layout.addRow("Bonus Vie :", self.inp_food_health)
        form_layout.addRow(self.group_food)

        # --- Potions ---
        self.group_potion = QGroupBox("Potion")
        potion_layout = QFormLayout(self.group_potion)
        self.inp_potion_heal = QSpinBox()
        self.inp_potion_heal.setRange(0, 999)
        self.inp_potion_heal.valueChanged.connect(self._save_current_item)
        
        self.inp_potion_buff_str = QSpinBox()
        self.inp_potion_buff_str.setRange(0, 999)
        self.inp_potion_buff_str.valueChanged.connect(self._save_current_item)
        
        self.inp_potion_duration = QSpinBox()
        self.inp_potion_duration.setRange(0, 9999)
        self.inp_potion_duration.setSuffix(" sec")
        self.inp_potion_duration.valueChanged.connect(self._save_current_item)

        potion_layout.addRow("Soin Instantané :", self.inp_potion_heal)
        potion_layout.addRow("Buff Force :", self.inp_potion_buff_str)
        potion_layout.addRow("Durée :", self.inp_potion_duration)
        form_layout.addRow(self.group_potion)

        scroll.setWidget(self.item_form)
        layout.addWidget(scroll, 2)
        
        self.item_form.setVisible(False)
        self._refresh_items_list()
        return widget

    def _create_quests_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Liste à gauche
        list_layout = QVBoxLayout()
        self.quests_list = QListWidget()
        self.quests_list.itemClicked.connect(self._on_quest_selected)
        list_layout.addWidget(self.quests_list)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Ajouter")
        btn_add.clicked.connect(self._add_quest)
        btn_del = QPushButton("Supprimer")
        btn_del.setStyleSheet("background-color: #d9534f;")
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
        self.items_tree.clear()
        if not self.project_model: return
        
        # Group items by type
        items_by_type = {}
        for item in self.project_model.items.values():
            itype = item.type or "misc"
            if itype not in items_by_type: items_by_type[itype] = []
            items_by_type[itype].append(item)
            
        # Create Tree Nodes
        for itype in sorted(items_by_type.keys()):
            type_node = QTreeWidgetItem(self.items_tree)
            type_node.setText(0, itype.capitalize())
            type_node.setExpanded(True)
            
            for item in sorted(items_by_type[itype], key=lambda x: x.name):
                item_node = QTreeWidgetItem(type_node)
                item_node.setText(0, item.name)
                item_node.setData(0, Qt.ItemDataRole.UserRole, item.id)

    def _add_item(self):
        new_item = ItemModel()
        self.project_model.items[new_item.id] = new_item
        self._refresh_items_list()
        # Select the new item
        # (Simplified: just refresh for now, selection logic would need to find the node)

    def _delete_item(self):
        current = self.items_tree.currentItem()
        if not current or not current.parent(): return # Ensure it's an item, not a category
        
        item_id = current.data(0, Qt.ItemDataRole.UserRole)
        if not item_id: return
        
        # Confirm
        reply = QMessageBox.question(self, "Confirmer", "Supprimer cet objet définitivement (DB et Fichier) ?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        # Delete from Model
        if item_id in self.project_model.items:
            del self.project_model.items[item_id]
            
        # Delete from DB & JSON
        self.db_manager.delete_item(item_id)
        
        self._refresh_items_list()
        self.item_form.setVisible(False)

    def _on_item_selected(self, item_node, column):
        if not item_node.parent(): return # Category node
        
        item_id = item_node.data(0, Qt.ItemDataRole.UserRole)
        item = self.project_model.items.get(item_id)
        if not item: return

        self.current_item_id = item_id
        self.item_form.setVisible(True)
        
        # Block signals

        widgets = [self.item_name, self.item_type, self.item_desc, self.inp_subtype, 
                   self.inp_dmg_min, self.inp_dmg_max, self.inp_crit_chance, self.inp_speed,
                   self.chk_two_handed, self.inp_req_str, self.inp_req_dex, self.inp_req_lvl,
                   self.inp_eff_bleed, self.inp_eff_poison,
                   self.inp_food_health, self.inp_potion_heal, self.inp_potion_buff_str, self.inp_potion_duration]
        for w in widgets: w.blockSignals(True)

        # Basic
        self.item_name.setText(item.name)
        self.item_type.setCurrentText(item.type)
        self.item_desc.setText(item.description)
        
        # Stats (stored in properties to be flexible)
        props = item.properties
        self.inp_subtype.setCurrentText(props.get("subtype", "sword"))
        self.inp_dmg_min.setValue(props.get("damage_min", 0))
        self.inp_dmg_max.setValue(props.get("damage_max", 0))
        self.inp_crit_chance.setValue(props.get("crit_chance", 5))
        self.inp_speed.setValue(props.get("speed", 1.0))
        self.chk_two_handed.setChecked(props.get("is_two_handed", False))
        
        # Reqs
        reqs = props.get("requirements", {})
        self.inp_req_str.setValue(reqs.get("forceMin", 0))
        self.inp_req_dex.setValue(reqs.get("dexMin", 0))
        self.inp_req_lvl.setValue(reqs.get("levelMin", 0))
        
        # Effects
        effects = props.get("effects", {})
        self.inp_eff_bleed.setValue(effects.get("bleed", 0))
        self.inp_eff_poison.setValue(effects.get("poison", 0))

        # Food
        bonus = props.get("bonus", {})
        self.inp_food_health.setValue(bonus.get("health", 0))

        # Potion
        # Potions might use 'effects' or specific fields depending on JSON structure.
        # We'll map them to properties for now.
        self.inp_potion_heal.setValue(effects.get("heal_instant", 0))
        self.inp_potion_buff_str.setValue(effects.get("buff_str", 0))
        self.inp_potion_duration.setValue(effects.get("duration", 0))

        # Update visibility based on type
        self._update_stats_visibility(item.type)

        # Unblock
        for w in widgets: w.blockSignals(False)

    def _on_item_type_changed(self, text):
        self._update_stats_visibility(text)
        self._save_current_item()

    def _update_stats_visibility(self, item_type):
        is_combat = item_type in ["weapon", "armor"]
        self.group_stats.setVisible(is_combat)
        self.group_reqs.setVisible(is_combat)
        self.group_effects.setVisible(is_combat or item_type == "potion") # Potions also use effects
        
        self.group_food.setVisible(item_type == "food")
        self.group_potion.setVisible(item_type == "potion")

    def _save_current_item(self):
        if not hasattr(self, 'current_item_id'): return
        item = self.project_model.items.get(self.current_item_id)
        if not item: return

        item.name = self.item_name.text()
        item.type = self.item_type.currentText()
        item.description = self.item_desc.toPlainText()
        
        # Save Stats to properties
        item.properties["subtype"] = self.inp_subtype.currentText()
        item.properties["damage_min"] = self.inp_dmg_min.value()
        item.properties["damage_max"] = self.inp_dmg_max.value()
        item.properties["crit_chance"] = self.inp_crit_chance.value()
        item.properties["speed"] = self.inp_speed.value()
        item.properties["is_two_handed"] = self.chk_two_handed.isChecked()
        
        item.properties["requirements"] = {
            "forceMin": self.inp_req_str.value(),
            "dexMin": self.inp_req_dex.value(),
            "levelMin": self.inp_req_lvl.value()
        }
        
        item.properties["effects"] = {
            "bleed": self.inp_eff_bleed.value(),
            "poison": self.inp_eff_poison.value(),
            "heal_instant": self.inp_potion_heal.value(),
            "buff_str": self.inp_potion_buff_str.value(),
            "duration": self.inp_potion_duration.value()
        }
        
        item.properties["bonus"] = {
            "health": self.inp_food_health.value()
        }

        # Update list item text
        # Update list item text
        current_tree_item = self.items_tree.currentItem()
        if current_tree_item:
            current_tree_item.setText(0, item.name)
            # If type changed, we might need to move it, but full refresh is safer/easier
            if current_tree_item.parent().text(0).lower() != item.type.lower():
                self._refresh_items_list()

        # --- AUTO-SYNC DB & JSON ---
        # 1. Save to DB
        self.db_manager.save_item(item.id, item.name, item.type, item.description, item.properties)
        
        # 2. Sync JSON if source file exists
        db_item = self.db_manager.get_item(item.id)
        if db_item and db_item.get("source_file"):
            self.db_manager.update_json_from_db(db_item["source_file"])

    # --- IMPORT / EXPORT DB ---
    def _import_items_json(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Importer JSON Items", "", "JSON Files (*.json)")
        if not paths: return
        
        success_count = 0
        for path in paths:
            if self.db_manager.import_items_from_json(path):
                success_count += 1
        
        if success_count > 0:
            self._sync_items_from_db()
            self._refresh_items_list()
            QMessageBox.information(self, "Succès", f"{success_count} fichier(s) importé(s) avec succès.")
        else:
            QMessageBox.warning(self, "Erreur", "Aucun fichier n'a pu être importé.")

    def _save_items_to_db(self):
        if not self.project_model: return
        
        count = 0
        for item in self.project_model.items.values():
            self.db_manager.save_item(item.id, item.name, item.type, item.description, item.properties)
            count += 1
            
        QMessageBox.information(self, "Succès", f"{count} items sauvegardés dans la base de données.")

    def _sync_items_from_db(self):
        """Charge les items de la DB dans le ProjectModel."""
        if not self.project_model: return
        
        db_items = self.db_manager.get_all_items()
        for item_data in db_items.values():
            # Conversion DB dict -> ItemModel
            item = ItemModel(
                id=item_data["id"],
                name=item_data["name"],
                type=item_data["type"],
                description=item_data["description"],
                properties=item_data["data"]
            )
            self.project_model.items[item.id] = item

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

    # --- LOCATIONS LOGIC ---
    def _create_locations_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Liste à gauche
        list_layout = QVBoxLayout()
        
        # Bouton Import JSON (Optionnel, ou utiliser celui des items si générique)
        # Pour l'instant, on garde simple
        
        self.locations_tree = QTreeWidget()
        self.locations_tree.setHeaderHidden(True)
        self.locations_tree.itemClicked.connect(self._on_location_selected)
        list_layout.addWidget(self.locations_tree)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Ajouter")
        btn_add.clicked.connect(self._add_location)
        btn_del = QPushButton("Supprimer")
        btn_del.setObjectName("dangerBtn")
        btn_del.clicked.connect(self._delete_location)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        list_layout.addLayout(btn_layout)
        
        # Bouton Save to DB
        btn_sync = QPushButton("Sauvegarder en DB")
        btn_sync.setObjectName("successBtn")
        btn_sync.setStyleSheet("margin-top: 5px;")
        btn_sync.clicked.connect(self._save_locations_to_db)
        list_layout.addWidget(btn_sync)

        layout.addLayout(list_layout, 1)

        # Formulaire à droite
        self.location_form = QWidget()
        form_layout = QFormLayout(self.location_form)

        self.loc_place = QLineEdit()
        self.loc_place.textChanged.connect(self._save_current_location)
        
        self.loc_city = QLineEdit()
        self.loc_city.textChanged.connect(self._save_current_location)
        
        self.loc_continent = QComboBox()
        self.loc_continent.addItems(["Eldaron", "Thaurgrim", "Iskarion", "Velkarum", "Varnal", "Helrun", "Unknown"])
        self.loc_continent.setEditable(True)
        self.loc_continent.currentTextChanged.connect(self._save_current_location)
        
        self.loc_type = QComboBox()
        self.loc_type.addItems(["Ville", "Village", "Donjon", "Taverne", "Boutique", "Temple", "Autre"])
        self.loc_type.setEditable(True)
        self.loc_type.currentTextChanged.connect(self._save_current_location)
        
        self.loc_x = QDoubleSpinBox()
        self.loc_x.setRange(-99999, 99999)
        self.loc_x.valueChanged.connect(self._save_current_location)
        
        self.loc_y = QDoubleSpinBox()
        self.loc_y.setRange(-99999, 99999)
        self.loc_y.valueChanged.connect(self._save_current_location)

        form_layout.addRow("Lieu (Place) :", self.loc_place)
        form_layout.addRow("Ville (City) :", self.loc_city)
        form_layout.addRow("Continent :", self.loc_continent)
        form_layout.addRow("Type :", self.loc_type)
        form_layout.addRow("Pos X :", self.loc_x)
        form_layout.addRow("Pos Y :", self.loc_y)

        layout.addWidget(self.location_form, 2)
        self.location_form.setVisible(False)

        self._refresh_locations_list()
        return widget

    def _refresh_locations_list(self):
        self.locations_tree.clear()
        if not self.project_model: return
        
        # Group by Type
        locs_by_type = {}
        for loc in self.project_model.locations.values():
            ltype = loc.type or "Autre"
            if ltype not in locs_by_type: locs_by_type[ltype] = []
            locs_by_type[ltype].append(loc)
            
        # Create Tree Nodes
        for ltype in sorted(locs_by_type.keys()):
            type_node = QTreeWidgetItem(self.locations_tree)
            type_node.setText(0, ltype)
            type_node.setExpanded(True)
            
            # Sort by City then Place
            sorted_locs = sorted(locs_by_type[ltype], key=lambda x: (x.city or "", x.place))
            
            for loc in sorted_locs:
                loc_node = QTreeWidgetItem(type_node)
                display = f"{loc.city} - {loc.place}" if loc.city else loc.place
                loc_node.setText(0, display)
                loc_node.setData(0, Qt.ItemDataRole.UserRole, loc.id)

    def _add_location(self):
        new_loc = LocationModel()
        self.project_model.locations[new_loc.id] = new_loc
        self._refresh_locations_list()

    def _delete_location(self):
        current = self.locations_tree.currentItem()
        if not current or not current.parent(): return
        
        loc_id = current.data(0, Qt.ItemDataRole.UserRole)
        if not loc_id: return
        
        reply = QMessageBox.question(self, "Confirmer", "Supprimer ce lieu ?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        if loc_id in self.project_model.locations:
            del self.project_model.locations[loc_id]
            
        # Delete from DB & Sync JSON
        self.db_manager.delete_location(loc_id)
        
        self._refresh_locations_list()
        self.location_form.setVisible(False)

    def _on_location_selected(self, item_node, column):
        if not item_node.parent(): return
        
        loc_id = item_node.data(0, Qt.ItemDataRole.UserRole)
        loc = self.project_model.locations.get(loc_id)
        if not loc: return

        self.current_loc_id = loc_id
        self.location_form.setVisible(True)
        
        self.loc_place.blockSignals(True)
        self.loc_city.blockSignals(True)
        self.loc_continent.blockSignals(True)
        self.loc_type.blockSignals(True)
        self.loc_x.blockSignals(True)
        self.loc_y.blockSignals(True)

        self.loc_place.setText(loc.place)
        self.loc_city.setText(loc.city)
        self.loc_continent.setCurrentText(loc.continent)
        self.loc_type.setCurrentText(loc.type)
        self.loc_x.setValue(loc.coords.get("x", 0.0))
        self.loc_y.setValue(loc.coords.get("y", 0.0))

        self.loc_place.blockSignals(False)
        self.loc_city.blockSignals(False)
        self.loc_continent.blockSignals(False)
        self.loc_type.blockSignals(False)
        self.loc_x.blockSignals(False)
        self.loc_y.blockSignals(False)

    def _save_current_location(self):
        if not hasattr(self, 'current_loc_id'): return
        loc = self.project_model.locations.get(self.current_loc_id)
        if not loc: return

        loc.place = self.loc_place.text()
        loc.city = self.loc_city.text()
        loc.continent = self.loc_continent.currentText()
        loc.type = self.loc_type.currentText()
        loc.coords["x"] = self.loc_x.value()
        loc.coords["y"] = self.loc_y.value()

        # Update Tree Item Text
        current_tree_item = self.locations_tree.currentItem()
        if current_tree_item:
            display = f"{loc.city} - {loc.place}" if loc.city else loc.place
            current_tree_item.setText(0, display)
            # If type changed, refresh list
            if current_tree_item.parent().text(0) != loc.type:
                self._refresh_locations_list()

        # Auto-save to DB & Sync JSON
        self.db_manager.save_location(loc.id, loc.place, loc.city, loc.coords, loc.type, loc.continent, loc.source_file)
        
        if loc.source_file:
            self.db_manager.update_location_json_from_db(loc.source_file)

    def _save_locations_to_db(self):
        if not self.project_model: return
        count = 0
        for loc in self.project_model.locations.values():
            self.db_manager.save_location(loc.id, loc.place, loc.city, loc.coords, loc.type, loc.continent, loc.source_file)
            count += 1
        QMessageBox.information(self, "Succès", f"{count} lieux sauvegardés.")

    def _sync_locations_from_db(self):
        if not self.project_model: return
        db_locs = self.db_manager.get_all_locations()
        for d in db_locs.values():
            loc = LocationModel(
                id=d["id"],
                place=d["place"],
                city=d.get("city", ""),
                coords=d.get("coords", {"x": 0, "y": 0}),
                type=d.get("type", "Autre"),
                continent=d.get("continent", "Unknown"),
                source_file=d.get("source_file", ""),
                properties=d.get("data", {})
            )
            self.project_model.locations[loc.id] = loc
        self._refresh_locations_list()
