import copy
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTreeWidget, QTreeWidgetItem, 
                             QLineEdit, QPushButton, QHBoxLayout, QLabel, QFormLayout, 
                             QComboBox, QDoubleSpinBox, QCheckBox, QMessageBox, QDialog, 
                             QListWidget, QListWidgetItem, QSpinBox, QTextEdit, QGroupBox, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal
from src.core.models import ProjectModel, ItemModel, QuestModel, LocationModel
from src.editor.commands import AddDictItemCommand, RemoveDictItemCommand, ReplaceDictItemCommand
from src.core.database import DatabaseManager

class DatabasePanel(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, undo_stack=None):
        super().__init__()
        self.undo_stack = undo_stack
        self.project_model = None
        self.db_manager = DatabaseManager()
        self._init_ui()
        self._apply_styles()
        
        # Connect signal to refresh logic
        self.data_changed.connect(self.on_data_changed)

    def on_data_changed(self):
        """Called when Undo/Redo operations modify the data."""
        self._refresh_items_list()
        self._refresh_quests_list()
        self._refresh_locations_list()

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #eee; font-family: 'Segoe UI', sans-serif; }
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox { 
                background-color: #3d3d3d; border: 1px solid #555; border-radius: 4px; padding: 4px; color: #fff; 
            }
            QTreeWidget, QListWidget { background-color: #2d2d2d; border: 1px solid #444; border-radius: 4px; }
            QTreeWidget::item:selected, QListWidget::item:selected { background-color: #444; }
            QPushButton { background-color: #444; border: 1px solid #555; border-radius: 4px; padding: 6px; }
            QPushButton:hover { background-color: #555; }
            QPushButton:pressed { background-color: #333; }
            QPushButton#dangerBtn { background-color: #844; border-color: #a66; }
            QPushButton#dangerBtn:hover { background-color: #955; }
            QPushButton#successBtn { background-color: #484; border-color: #6a6; }
            QPushButton#successBtn:hover { background-color: #595; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #333; color: #ccc; padding: 8px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #444; color: #fff; border-bottom: 2px solid #5ab; }
            QGroupBox { border: 1px solid #555; margin-top: 20px; border-radius: 4px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: #aaa; }
        """)

    def set_project(self, project: ProjectModel):
        self.project_model = project
        self._refresh_items_list()
        self._refresh_quests_list()
        self._refresh_locations_list()
        self._sync_items_from_db()
        self._sync_locations_from_db()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._create_items_tab(), "Objets")
        self.tabs.addTab(self._create_quests_tab(), "Quêtes")
        self.tabs.addTab(self._create_locations_tab(), "Lieux")

    def _create_items_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Left: List
        left_layout = QVBoxLayout()
        self.item_search = QLineEdit()
        self.item_search.setPlaceholderText("Rechercher...")
        self.item_search.textChanged.connect(self._filter_items_list)
        left_layout.addWidget(self.item_search)
        
        self.items_tree = QTreeWidget()
        self.items_tree.setHeaderHidden(True)
        self.items_tree.itemClicked.connect(self._on_item_selected)
        left_layout.addWidget(self.items_tree)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Ajouter")
        btn_add.clicked.connect(self._add_item)
        btn_del = QPushButton("Supprimer")
        btn_del.clicked.connect(self._delete_item)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        left_layout.addLayout(btn_layout)
        
        # Import/Export
        io_layout = QHBoxLayout()
        btn_import = QPushButton("Import JSON")
        btn_import.clicked.connect(self._import_items_json)
        btn_save_db = QPushButton("Save to DB")
        btn_save_db.clicked.connect(self._save_items_to_db)
        io_layout.addWidget(btn_import)
        io_layout.addWidget(btn_save_db)
        left_layout.addLayout(io_layout)

        layout.addLayout(left_layout, 1)
        
        # Right: Form
        self.item_form = QWidget()
        form_layout = QFormLayout(self.item_form)
        
        self.item_name = QLineEdit()
        self.item_name.editingFinished.connect(self._save_current_item)
        
        self.item_type = QComboBox()
        self.item_type.addItems(["weapon", "armor", "potion", "food", "misc", "quest"])
        self.item_type.currentTextChanged.connect(self._on_item_type_changed)
        
        self.item_desc = QTextEdit()
        self.item_desc.setMaximumHeight(60)
        self.item_desc.textChanged.connect(self._save_current_item)
        
        form_layout.addRow("Nom:", self.item_name)
        form_layout.addRow("Type:", self.item_type)
        form_layout.addRow("Description:", self.item_desc)
        
        # Sub-groups
        # Stats
        self.group_stats = QGroupBox("Stats")
        stats_layout = QFormLayout(self.group_stats)
        self.inp_subtype = QComboBox()
        self.inp_subtype.addItems(["sword", "axe", "bow", "staff", "shield", "helmet", "chest", "boots"])
        self.inp_subtype.currentTextChanged.connect(self._save_current_item)
        self.inp_dmg_min = QSpinBox(); self.inp_dmg_min.setRange(0, 999); self.inp_dmg_min.valueChanged.connect(self._save_current_item)
        self.inp_dmg_max = QSpinBox(); self.inp_dmg_max.setRange(0, 999); self.inp_dmg_max.valueChanged.connect(self._save_current_item)
        self.inp_crit_chance = QSpinBox(); self.inp_crit_chance.setRange(0, 100); self.inp_crit_chance.valueChanged.connect(self._save_current_item)
        self.inp_speed = QDoubleSpinBox(); self.inp_speed.setRange(0.1, 5.0); self.inp_speed.valueChanged.connect(self._save_current_item)
        self.chk_two_handed = QCheckBox("Deux mains"); self.chk_two_handed.toggled.connect(self._save_current_item)
        
        stats_layout.addRow("Sous-type:", self.inp_subtype)
        stats_layout.addRow("Dmg Min:", self.inp_dmg_min)
        stats_layout.addRow("Dmg Max:", self.inp_dmg_max)
        stats_layout.addRow("Crit %:", self.inp_crit_chance)
        stats_layout.addRow("Vitesse:", self.inp_speed)
        stats_layout.addRow(self.chk_two_handed)
        form_layout.addRow(self.group_stats)
        
        # Reqs
        self.group_reqs = QGroupBox("Pré-requis")
        reqs_layout = QFormLayout(self.group_reqs)
        self.inp_req_str = QSpinBox(); self.inp_req_str.valueChanged.connect(self._save_current_item)
        self.inp_req_dex = QSpinBox(); self.inp_req_dex.valueChanged.connect(self._save_current_item)
        self.inp_req_lvl = QSpinBox(); self.inp_req_lvl.valueChanged.connect(self._save_current_item)
        reqs_layout.addRow("Force:", self.inp_req_str)
        reqs_layout.addRow("Dextérité:", self.inp_req_dex)
        reqs_layout.addRow("Niveau:", self.inp_req_lvl)
        form_layout.addRow(self.group_reqs)
        
        # Effects
        self.group_effects = QGroupBox("Effets")
        eff_layout = QFormLayout(self.group_effects)
        self.inp_eff_bleed = QSpinBox(); self.inp_eff_bleed.valueChanged.connect(self._save_current_item)
        self.inp_eff_poison = QSpinBox(); self.inp_eff_poison.valueChanged.connect(self._save_current_item)
        eff_layout.addRow("Saignement:", self.inp_eff_bleed)
        eff_layout.addRow("Poison:", self.inp_eff_poison)
        form_layout.addRow(self.group_effects)
        
        # Food
        self.group_food = QGroupBox("Nourriture")
        food_layout = QFormLayout(self.group_food)
        self.inp_food_health = QSpinBox(); self.inp_food_health.valueChanged.connect(self._save_current_item)
        food_layout.addRow("PV Rendus:", self.inp_food_health)
        form_layout.addRow(self.group_food)
        
        # Potion
        self.group_potion = QGroupBox("Potion")
        pot_layout = QFormLayout(self.group_potion)
        self.inp_potion_heal = QSpinBox(); self.inp_potion_heal.valueChanged.connect(self._save_current_item)
        self.inp_potion_buff_str = QSpinBox(); self.inp_potion_buff_str.valueChanged.connect(self._save_current_item)
        self.inp_potion_duration = QSpinBox(); self.inp_potion_duration.valueChanged.connect(self._save_current_item)
        pot_layout.addRow("Soin Instant:", self.inp_potion_heal)
        pot_layout.addRow("Buff Force:", self.inp_potion_buff_str)
        pot_layout.addRow("Durée (tours):", self.inp_potion_duration)
        form_layout.addRow(self.group_potion)
        
        layout.addWidget(self.item_form, 2)
        self.item_form.setVisible(False)
        return widget

    def _create_quests_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        left_layout = QVBoxLayout()
        self.quest_search = QLineEdit()
        self.quest_search.setPlaceholderText("Rechercher...")
        self.quest_search.textChanged.connect(self._filter_quests_list)
        left_layout.addWidget(self.quest_search)
        
        self.quests_tree = QTreeWidget()
        self.quests_tree.setHeaderHidden(True)
        self.quests_tree.itemClicked.connect(self._on_quest_selected)
        left_layout.addWidget(self.quests_tree)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Ajouter")
        btn_add.clicked.connect(self._add_quest)
        btn_del = QPushButton("Supprimer")
        btn_del.clicked.connect(self._delete_quest)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        left_layout.addLayout(btn_layout)
        
        layout.addLayout(left_layout, 1)
        
        self.quest_form = QWidget()
        form_layout = QFormLayout(self.quest_form)
        
        self.quest_title = QLineEdit()
        self.quest_title.editingFinished.connect(self._save_current_quest)
        
        self.quest_desc = QTextEdit()
        self.quest_desc.setMaximumHeight(60)
        self.quest_desc.textChanged.connect(self._save_current_quest)
        
        self.quest_presentation = QTextEdit()
        self.quest_presentation.setMaximumHeight(60)
        self.quest_presentation.textChanged.connect(self._save_current_quest)
        
        self.quest_main = QCheckBox("Quête Principale")
        self.quest_main.toggled.connect(self._save_current_quest)
        
        self.loot_xp = QSpinBox()
        self.loot_xp.setRange(0, 99999)
        self.loot_xp.valueChanged.connect(self._save_current_quest)
        
        self.loot_gold = QSpinBox()
        self.loot_gold.setRange(0, 99999)
        self.loot_gold.valueChanged.connect(self._save_current_quest)
        

        self.quest_steps_list = QListWidget()
        
        form_layout.addRow("Titre:", self.quest_title)
        form_layout.addRow("Description:", self.quest_desc)
        form_layout.addRow("Texte (Offre):", self.quest_presentation)
        
        self.quest_return_scene = QComboBox()
        self.quest_return_scene.setEditable(True)
        self.quest_return_scene.setPlaceholderText("ID de la Scène de Validation (Optionnel)")
        self.quest_return_scene.currentIndexChanged.connect(self._save_current_quest)
        self.quest_return_scene.editTextChanged.connect(self._save_current_quest)
        form_layout.addRow("Scène Validation:", self.quest_return_scene)
        
        form_layout.addRow("", self.quest_main)
        
        # LOOT SECTION (Inline)
        self.group_loot = QGroupBox("Récompenses (Loot)")
        loot_layout = QVBoxLayout(self.group_loot)
        
        # XP / GOLD
        form_loot = QFormLayout()
        self.loot_xp = QSpinBox()
        self.loot_xp.setRange(0, 99999)
        self.loot_xp.valueChanged.connect(self._save_current_quest)
        
        self.loot_gold = QSpinBox()
        self.loot_gold.setRange(0, 99999)
        self.loot_gold.valueChanged.connect(self._save_current_quest)
        
        form_loot.addRow("XP:", self.loot_xp)
        form_loot.addRow("Or:", self.loot_gold)
        loot_layout.addLayout(form_loot)
        
        # ITEMS LIST
        loot_layout.addWidget(QLabel("Items:"))
        self.list_loot_items = QListWidget()
        self.list_loot_items.setMaximumHeight(100)
        loot_layout.addWidget(self.list_loot_items)
        
        # Controls (Add Item)
        add_loot_layout = QHBoxLayout()
        self.combo_loot_item = QComboBox()
        self.spin_loot_qty = QSpinBox()
        self.spin_loot_qty.setRange(1, 99)
        
        btn_add_loot = QPushButton("+")
        btn_add_loot.clicked.connect(self._add_loot_item_inline)
        btn_del_loot = QPushButton("-")
        btn_del_loot.clicked.connect(self._remove_loot_item_inline)
        
        add_loot_layout.addWidget(self.combo_loot_item, 1)
        add_loot_layout.addWidget(self.spin_loot_qty)
        add_loot_layout.addWidget(btn_add_loot)
        add_loot_layout.addWidget(btn_del_loot)
        loot_layout.addLayout(add_loot_layout)
        
        form_layout.addRow(self.group_loot)

        
        steps_widget = QWidget()
        steps_layout = QVBoxLayout(steps_widget)
        steps_layout.addWidget(QLabel("Étapes:"))
        steps_layout.addWidget(self.quest_steps_list)
        steps_btn_layout = QHBoxLayout()
        btn_add_step = QPushButton("+")
        btn_add_step.clicked.connect(self._add_quest_step)
        btn_del_step = QPushButton("-")
        btn_del_step.clicked.connect(self._delete_quest_step)
        steps_btn_layout.addWidget(btn_add_step)
        steps_btn_layout.addWidget(btn_del_step)
        steps_layout.addLayout(steps_btn_layout)
        form_layout.addRow(steps_widget)
        
        layout.addWidget(self.quest_form, 2)
        self.quest_form.setVisible(False)
        return widget

    def _refresh_quests_list(self):
        self.quests_tree.clear()
        if not self.project_model: return
        search_text = self.quest_search.text().lower()
        for quest in self.project_model.quests.values():
            if search_text and search_text not in quest.title.lower():
                continue
                
            tree_item = QTreeWidgetItem([quest.title])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, quest.id)
            self.quests_tree.addTopLevelItem(tree_item)

    def _filter_quests_list(self):
        self._refresh_quests_list()

    def _add_quest(self):
        new_quest = QuestModel()
        if self.undo_stack is not None:
            cmd = AddDictItemCommand(self.project_model.quests, new_quest.id, new_quest, "Ajouter Quête", self.data_changed)
            self.undo_stack.push(cmd)
        else:
            self.project_model.quests[new_quest.id] = new_quest
            self._refresh_quests_list()

    def _delete_quest(self):
        current = self.quests_tree.currentItem()
        if not current: return
        quest_id = current.data(0, Qt.ItemDataRole.UserRole)
        
        if self.undo_stack is not None:
            cmd = RemoveDictItemCommand(self.project_model.quests, quest_id, "Supprimer Quête", self.data_changed)
            self.undo_stack.push(cmd)
        else:
            del self.project_model.quests[quest_id]
            self._refresh_quests_list()
            
        self.quest_form.setVisible(False)

    def _on_quest_selected(self, tree_item, column):
        quest_id = tree_item.data(0, Qt.ItemDataRole.UserRole)
        quest = self.project_model.quests.get(quest_id)
        if not quest: return

        self.current_quest_id = quest_id
        self.quest_form.setVisible(True)

        self.quest_presentation.blockSignals(True)
        self.quest_return_scene.blockSignals(True)
        self.loot_xp.blockSignals(True)
        self.loot_gold.blockSignals(True)

        self.quest_title.setText(quest.title)
        self.quest_desc.setText(quest.description)
        self.quest_presentation.setText(quest.presentation_text)
        self.quest_main.setChecked(quest.is_main_quest)
        
        # Populate Return Scene Combo
        self.quest_return_scene.clear()
        self.quest_return_scene.addItem("", "")
        if self.project_model:
            for node in self.project_model.nodes.values():
                self.quest_return_scene.addItem(node.title, node.id)
                
        # Select current
        idx = self.quest_return_scene.findData(quest.return_scene_id)
        if idx >= 0:
            self.quest_return_scene.setCurrentIndex(idx)
        else:
            self.quest_return_scene.setEditText(quest.return_scene_id)
        
        loot = quest.loot
        self.loot_xp.setValue(loot.get("xp", 0))
        self.loot_gold.setValue(loot.get("gold", 0))
        
        self._refresh_loot_ui()
        
        self.quest_title.blockSignals(False)
        self.quest_desc.blockSignals(False)
        self.quest_presentation.blockSignals(False)
        self.quest_main.blockSignals(False)
        self.quest_return_scene.blockSignals(False)
        self.loot_xp.blockSignals(False)
        self.loot_gold.blockSignals(False)
        
        self._refresh_quest_steps(quest)

    def _refresh_quest_steps(self, quest):
        self.quest_steps_list.clear()
        if not quest: return
        for step in quest.steps:
            item = QListWidgetItem(step)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.quest_steps_list.addItem(item)

    def _save_current_quest(self):
        if not hasattr(self, 'current_quest_id'): return
        quest = self.project_model.quests.get(self.current_quest_id)
        if not quest: return

        # Capture old state
        old_state = copy.deepcopy(quest)

        quest.title = self.quest_title.text()
        quest.description = self.quest_desc.toPlainText()
        quest.presentation_text = self.quest_presentation.toPlainText()
        quest.is_main_quest = self.quest_main.isChecked()
        quest.is_main_quest = self.quest_main.isChecked()
        
        # Read from combo
        scene_id = self.quest_return_scene.currentData()
        # If editable and text manually entered but no data
        if not scene_id:
             scene_id = self.quest_return_scene.currentText()
             # Maybe user typed "Title (ID)", try to extract if needed, 
             # but usually clean ID or matched data is best. 
             # For now, simplistic approach: if no data match, trust text (allows dynamic IDs?)
             # But usually text is "Title (ID)". If user just typed ID, it might not match data.
             # Strict usage:
             # If user selects item, currentData is ID.
             # If user types ID, findData might fail.
             # Let's trust currentData first, then text (which might be the ID if manually typed)
        
        # Use data if available, else text (for manual entry)
        if self.quest_return_scene.findText(self.quest_return_scene.currentText()) >= 0:
             # Chosen from list or matches list text
             idx = self.quest_return_scene.findText(self.quest_return_scene.currentText())
             scene_id = self.quest_return_scene.itemData(idx)
        else:
             scene_id = self.quest_return_scene.currentText()

        quest.return_scene_id = scene_id
        
        quest.loot["xp"] = self.loot_xp.value()
        quest.loot["gold"] = self.loot_gold.value()
        # Loot items are handled immediately by inline methods
        
        # Save steps from UI
        new_steps = []
        for i in range(self.quest_steps_list.count()):
            new_steps.append(self.quest_steps_list.item(i).text())
        quest.steps = new_steps

        if self.undo_stack is not None:
            cmd = ReplaceDictItemCommand(self.project_model.quests, quest.id, quest, old_state, "Modifier Quête", self.data_changed)
            self.undo_stack.push(cmd)
        else:
            # Manual update
            current_item = self.quests_tree.currentItem()
            if current_item:
                current_item.setText(0, quest.title)

    def _add_quest_step(self):
        if not hasattr(self, 'current_quest_id'): return
        quest = self.project_model.quests.get(self.current_quest_id)
        if not quest: return
        
        old_state = copy.deepcopy(quest)
        quest.steps.append("Nouvelle étape")
        
        if self.undo_stack is not None:
            cmd = ReplaceDictItemCommand(self.project_model.quests, quest.id, quest, old_state, "Ajouter Étape Quête", self.data_changed)
            self.undo_stack.push(cmd)
        else:
            self._refresh_quest_steps(quest)

    def _delete_quest_step(self):
        if not hasattr(self, 'current_quest_id'): return
        quest = self.project_model.quests.get(self.current_quest_id)
        if not quest: return
        
        row = self.quest_steps_list.currentRow()
        if row < 0: return
        
        old_state = copy.deepcopy(quest)
        quest.steps.pop(row)
        
        if self.undo_stack is not None:
            cmd = ReplaceDictItemCommand(self.project_model.quests, quest.id, quest, old_state, "Supprimer Étape Quête", self.data_changed)
            self.undo_stack.push(cmd)
        else:
            self._refresh_quest_steps(quest)

    # --- INLINE LOOT MANAGEMENT ---
    def _refresh_loot_ui(self):
        """Met à jour la liste des items de loot pour la quête actuelle."""
        if not hasattr(self, 'current_quest_id') or not self.project_model: return
        quest = self.project_model.quests.get(self.current_quest_id)
        if not quest: return
        
        # Update Items Combo
        self.combo_loot_item.clear()
        for item in sorted(self.project_model.items.values(), key=lambda x: x.name):
            self.combo_loot_item.addItem(item.name, item.id)
            
        # Update List
        self.list_loot_items.clear()
        items = quest.loot.get("items", {})
        for item_id, qty in items.items():
            item_name = "Inconnu"
            if item_id in self.project_model.items:
                 item_name = self.project_model.items[item_id].name
            
            self.list_loot_items.addItem(f"{qty}x {item_name} ({item_id})")
            
    def _add_loot_item_inline(self):
        if not hasattr(self, 'current_quest_id'): return
        quest = self.project_model.quests.get(self.current_quest_id)
        if not quest: return
        
        item_id = self.combo_loot_item.currentData()
        qty = self.spin_loot_qty.value()
        
        if item_id:
             quest.loot.setdefault("items", {})[item_id] = qty
             self._refresh_loot_ui()
             self._save_current_quest()

    def _remove_loot_item_inline(self):
        if not hasattr(self, 'current_quest_id'): return
        quest = self.project_model.quests.get(self.current_quest_id)
        if not quest: return
        
        row = self.list_loot_items.currentRow()
        if row >= 0:
            keys = list(quest.loot.get("items", {}).keys())
            if row < len(keys):
                del quest.loot["items"][keys[row]]
                self._refresh_loot_ui()
                self._save_current_quest()

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
                # Filter logic
                search_text = self.item_search.text().lower() if hasattr(self, 'item_search') else ""
                if search_text and search_text not in item.name.lower():
                    continue
                    
                item_node = QTreeWidgetItem(type_node)
                item_node.setText(0, item.name)
                item_node.setData(0, Qt.ItemDataRole.UserRole, item.id)

    def _filter_items_list(self):
        self._refresh_items_list()

    def _add_item(self):
        new_item = ItemModel()
        if self.undo_stack is not None:
            cmd = AddDictItemCommand(self.project_model.items, new_item.id, new_item, "Ajouter Objet", self.data_changed)
            self.undo_stack.push(cmd)
        else:
            self.project_model.items[new_item.id] = new_item
            self._refresh_items_list()

    def _delete_item(self):
        current = self.items_tree.currentItem()
        if not current or not current.parent(): return # Ensure it's an item, not a category
        
        item_id = current.data(0, Qt.ItemDataRole.UserRole)
        if not item_id: return
        
        # Confirm
        reply = QMessageBox.question(self, "Confirmer", "Supprimer cet objet définitivement (DB et Fichier) ?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        # Delete from Model (Undoable)
        if self.undo_stack is not None:
            cmd = RemoveDictItemCommand(self.project_model.items, item_id, "Supprimer Objet", self.data_changed)
            self.undo_stack.push(cmd)
        else:
            if item_id in self.project_model.items:
                del self.project_model.items[item_id]
            self._refresh_items_list()
            
        # Delete from DB & JSON
        # Note: Undo will restore in memory but not automatically in DB. 
        # User must "Save to DB" to persist restoration.
        self.db_manager.delete_item(item_id)
        
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

        # Capture old state for Undo
        old_state = copy.deepcopy(item)

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

        if self.undo_stack is not None:
            # Push command (Redo will re-apply 'item', Undo will apply 'old_state')
            cmd = ReplaceDictItemCommand(self.project_model.items, item.id, item, old_state, "Modifier Objet", self.data_changed)
            self.undo_stack.push(cmd)
        else:
            # Manual update if no undo stack
            current_tree_item = self.items_tree.currentItem()
            if current_tree_item:
                current_tree_item.setText(0, item.name)
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
    # --- QUESTS LOGIC (Legacy methods removed/updated) ---
    # _refresh_quests_list is already defined above

    # --- LOCATIONS LOGIC ---
    def _create_locations_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Liste à gauche
        # Liste à gauche
        list_layout = QVBoxLayout()
        
        # Search Bar
        self.loc_search = QLineEdit()
        self.loc_search.setPlaceholderText("Rechercher un lieu...")
        self.loc_search.textChanged.connect(self._filter_locations_list)
        list_layout.addWidget(self.loc_search)
        
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
        self.loc_place.editingFinished.connect(self._save_current_location)
        
        self.loc_city = QLineEdit()
        self.loc_city.editingFinished.connect(self._save_current_location)
        
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
        self.loc_x.editingFinished.connect(self._save_current_location)
        
        self.loc_y = QDoubleSpinBox()
        self.loc_y.setRange(-99999, 99999)
        self.loc_y.editingFinished.connect(self._save_current_location)

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
                # Filter
                search_text = self.loc_search.text().lower() if hasattr(self, 'loc_search') else ""
                display = f"{loc.city} - {loc.place}" if loc.city else loc.place
                
                if search_text and search_text not in display.lower():
                    continue

                loc_node = QTreeWidgetItem(type_node)
                loc_node.setText(0, display)
                loc_node.setData(0, Qt.ItemDataRole.UserRole, loc.id)

    def _filter_locations_list(self):
        self._refresh_locations_list()

    def _add_location(self):
        new_loc = LocationModel()
        if self.undo_stack is not None:
            cmd = AddDictItemCommand(self.project_model.locations, new_loc.id, new_loc, "Ajouter Lieu", self.data_changed)
            self.undo_stack.push(cmd)
        else:
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

        if self.undo_stack is not None:
            cmd = RemoveDictItemCommand(self.project_model.locations, loc_id, "Supprimer Lieu", self.data_changed)
            self.undo_stack.push(cmd)
        else:
            if loc_id in self.project_model.locations:
                del self.project_model.locations[loc_id]
            self._refresh_locations_list()
            
        # Delete from DB & Sync JSON
        self.db_manager.delete_location(loc_id)
        
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

        old_state = copy.deepcopy(loc)

        loc.place = self.loc_place.text()
        loc.city = self.loc_city.text()
        loc.continent = self.loc_continent.currentText()
        loc.type = self.loc_type.currentText()
        loc.coords["x"] = self.loc_x.value()
        loc.coords["y"] = self.loc_y.value()

        if self.undo_stack is not None:
            cmd = ReplaceDictItemCommand(self.project_model.locations, loc.id, loc, old_state, "Modifier Lieu", self.data_changed)
            self.undo_stack.push(cmd)
        else:
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
