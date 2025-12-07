import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QListWidget, QFrame, QScrollArea, QStackedWidget, QListWidgetItem, QGraphicsDropShadowEffect, QMenu, QSizePolicy)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint

class QuestItemWidget(QFrame):
    def __init__(self, quest_model, status="active", current_step_text=None):
        super().__init__()
        # Determine colors based on status
        border_color = "#b1a270" if status == "active" else "#5cb85c"
        status_text = "EN COURS" if status == "active" else "COMPLÉTÉE"
        status_bg = "#3d3510" if status == "active" else "#1e3a1e"
        status_fg = "#ffe066" if status == "active" else "#aaffaa"

        self.setStyleSheet(f"""
            QuestItemWidget {{
                background-color: #1a1a1a;
                border: 1px solid {border_color};
                border-radius: 6px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Header: Title + Status Badge
        header = QHBoxLayout()
        header.setSpacing(10)
        
        lbl_title = QLabel(quest_model.title)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #eee; font-family: 'Underdog';")
        lbl_title.setWordWrap(True)
        header.addWidget(lbl_title, 1)
        
        lbl_status = QLabel(status_text)
        lbl_status.setStyleSheet(f"background-color: {status_bg}; color: {status_fg}; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 10px;")
        lbl_status.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        header.addWidget(lbl_status)
        
        layout.addLayout(header)
        
        # Description
        lbl_desc = QLabel(quest_model.description)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #aaa; font-style: italic; font-size: 12px;")
        layout.addWidget(lbl_desc)
        
        # Current Objective (Step)
        if current_step_text:
            lbl_step = QLabel(f"Objectif : {current_step_text}")
            lbl_step.setWordWrap(True)
            lbl_step.setStyleSheet("color: #ffe066; font-weight: bold; font-size: 13px; margin-top: 5px; border-left: 2px solid #b1a270; padding-left: 5px;")
            layout.addWidget(lbl_step)
        
        # Completion Status
        if status == "completed":
            lbl_return = QLabel("Prête à être rendue.")
            lbl_return.setStyleSheet("color: #5cb85c; font-weight: bold; font-size: 12px; margin-top: 5px;")
            layout.addWidget(lbl_return)

class InventoryItemWidget(QFrame):
    def __init__(self, item_def, qty, assets_dir, is_equipped=False):
        super().__init__()
        self.setStyleSheet("""
            InventoryItemWidget {
                background-color: #111;
                border-radius: 6px;
                border: 1px solid #333;
            }
            QLabel {
                border: none;
                background-color: transparent;
                selection-background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Header Row: Name + Qty + Equipped Badge
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        name = item_def.name if item_def else "Unknown"
        header_lbl = QLabel(f"{name} x{qty}")
        header_lbl.setStyleSheet("font-weight:bold; font-size:15px; color:#fff; font-family: 'Underdog', 'Segoe UI', sans-serif;")
        header_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        header_layout.addWidget(header_lbl)
        
        if is_equipped:
            lbl_equipped = QLabel("ÉQUIPÉ")
            lbl_equipped.setStyleSheet("background-color: #2a5a2a; color: #fff; font-weight: bold; font-size: 10px; padding: 2px 4px; border-radius: 3px;")
            lbl_equipped.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            header_layout.addWidget(lbl_equipped)
            
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 2. Subtitle: Type
        type_str = item_def.type.capitalize() if item_def else "Objet"
        type_lbl = QLabel(type_str)
        type_lbl.setStyleSheet("color:#888; font-style:italic; font-size:12px; margin-bottom: 4px; font-family: 'Segoe UI', sans-serif;")
        type_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(type_lbl)

        # 3. Stats Row (Badges)
        if item_def and item_def.type in ["weapon", "armor"]:
            props = item_def.properties
            
            stats_widget = QWidget()
            stats_widget.setStyleSheet("background-color: transparent;")
            stats_layout = QHBoxLayout(stats_widget)
            stats_layout.setContentsMargins(0, 0, 0, 0)
            stats_layout.setSpacing(6)
            
            def add_badge(text, icon=None, bg_color="#2a2a2a", text_color="#ccc"):
                badge = QFrame()
                badge.setStyleSheet(f"""
                    QFrame {{
                        background-color: {bg_color};
                        border-radius: 4px;
                        border: 1px solid {bg_color};
                    }}
                """)
                b_layout = QHBoxLayout(badge)
                b_layout.setContentsMargins(5, 2, 5, 2)
                b_layout.setSpacing(4)
                
                if icon:
                    icon_path = os.path.join(assets_dir, icon)
                    if os.path.exists(icon_path):
                        pix = QPixmap(icon_path)
                        pix = pix.scaled(14, 14, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        icon_lbl = QLabel()
                        icon_lbl.setPixmap(pix)
                        icon_lbl.setStyleSheet("background: transparent;")
                        icon_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
                        b_layout.addWidget(icon_lbl)
                
                txt_lbl = QLabel(str(text))
                txt_lbl.setStyleSheet(f"color:{text_color}; font-size:12px; font-weight:bold; background: transparent; font-family: 'Segoe UI', sans-serif;")
                txt_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
                b_layout.addWidget(txt_lbl)
                
                stats_layout.addWidget(badge)

            # Badge 1: Subtype
            subtype = props.get("subtype", type_str)
            add_badge(subtype, bg_color="#333", text_color="#aaa")

            # Badge 2: Damage
            dmg_min = props.get("damage_min", 0)
            dmg_max = props.get("damage_max", 0)
            if dmg_max > 0:
                add_badge(f"{dmg_min}-{dmg_max}", "damages.png", bg_color="#3d2020", text_color="#ffaaaa")
            
            # Badge 3: Speed
            speed = props.get("speed", 0)
            if speed > 0:
                add_badge(f"{speed}", "dexterity.png", bg_color="#20303d", text_color="#aaddff")
            
            # Badge 4: Crit
            crit = props.get("crit_chance", 0)
            crit_mult = props.get("crit_multiplier", 0)
            if crit > 0:
                crit_text = f"{crit}%"
                if crit_mult > 0:
                    crit_text += f" x{crit_mult}"
                add_badge(crit_text, "critical.png", bg_color="#3d3d20", text_color="#ffffaa")
            
            stats_layout.addStretch()
            layout.addWidget(stats_widget)

        # Description
        desc = item_def.description if item_def else ""
        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("color:#777; font-size:12px; margin-top: 4px; font-family: 'Underdog', 'Segoe UI', sans-serif;")
            desc_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            layout.addWidget(desc_lbl)


class SlidingMenu(QWidget):
    def __init__(self, parent=None, story_manager=None):
        super().__init__(parent)
        self.story_manager = story_manager
        # SlidingMenu covers the whole window for click-outside detection
        self.resize(parent.size())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.menu_width = 400
        
        # --- Menu Panel (The actual visible part) ---
        self.menu_panel = QFrame(self)
        self.menu_panel.setFixedWidth(self.menu_width)
        self.menu_panel.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-left: 1px solid #333;
            }
            QPushButton#TabBtn {
                background-color: transparent;
                color: #888;
                border: none;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
                text-align: center;
            }
            QPushButton#TabBtn:checked {
                color: #fff;
                border-bottom: 2px solid #c42b1c;
                background-color: #222;
            }
            QPushButton#TabBtn:hover {
                color: #ccc;
                background-color: #222;
            }
        """)
        
        # Shadow effect on the panel
        shadow = QGraphicsDropShadowEffect(self.menu_panel)
        shadow.setBlurRadius(20)
        shadow.setXOffset(-5)
        shadow.setYOffset(0)
        shadow.setColor(Qt.GlobalColor.black)
        self.menu_panel.setGraphicsEffect(shadow)
        
        # Layout INSIDE the panel
        layout = QVBoxLayout(self.menu_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- Header (Tabs + Close) ---
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet("background-color: #111; border-bottom: 1px solid #333;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        
        self.btn_group = []
        
        def add_tab(text, index, icon_name=None):
            btn = QPushButton(text)
            btn.setObjectName("TabBtn")
            if icon_name:
                icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", icon_name)
                if os.path.exists(icon_path):
                    btn.setIcon(QIcon(icon_path))
                    btn.setIconSize(QSize(24, 24))
            
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda: self.switch_tab(index))
            header_layout.addWidget(btn)
            self.btn_group.append(btn)
            return btn

        self.btn_inv = add_tab("Inventaire", 0)
        self.btn_equip = add_tab("Équipement", 1)
        self.btn_quests = add_tab("Quêtes", 2, "quest.png")
        self.btn_comp = add_tab("Compagnons", 3)
        
        # Close Button
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(50, 50)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.hide_menu)
        btn_close.setStyleSheet("QPushButton { color: #888; border: none; font-size: 16px; } QPushButton:hover { color: #fff; background-color: #c42b1c; }")
        header_layout.addWidget(btn_close)
        
        layout.addWidget(header)
        
        # --- Content Stack ---
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # 1. Inventory View
        self.view_inventory = QWidget()
        self.init_inventory_view()
        self.stack.addWidget(self.view_inventory)
        
        # 2. Equipment View
        self.view_equipment = QWidget()
        self.init_equipment_view()
        self.stack.addWidget(self.view_equipment)
        
        # 3. Quests View
        self.view_quests = QWidget()
        self.init_quests_view()
        self.stack.addWidget(self.view_quests)

        # 4. Companions View
        self.view_companions = QWidget()
        self.init_companions_view()
        self.stack.addWidget(self.view_companions)
        
        # Initial State
        self.switch_tab(0)
        self.hide() # Hidden by default
        
        # Animation
        self.anim = QPropertyAnimation(self.menu_panel, b"pos")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.finished.connect(self._on_anim_finished)
        self.is_closing = False

    def resizeEvent(self, event):
        # Keep menu panel full height and attached to right side (conceptually)
        # But during animation we control position manually.
        # When static (open), it should be at width() - menu_width
        self.menu_panel.setFixedSize(self.menu_width, self.height())
        if not self.anim.state() == QPropertyAnimation.State.Running and self.isVisible():
             self.menu_panel.move(self.width() - self.menu_width, 0)
        
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        # Close if clicked outside the menu panel
        if not self.menu_panel.geometry().contains(event.pos()):
            self.hide_menu()
        else:
            super().mousePressEvent(event)

    def show_menu(self, tab_index=0):
        # Ensure we cover the parent
        if self.parent():
            self.resize(self.parent().size())
            
        self.show()
        self.raise_()
        self.switch_tab(tab_index)
        
        # Animate In
        start_pos = QPoint(self.width(), 0)
        end_pos = QPoint(self.width() - self.menu_width, 0)
        
        self.menu_panel.move(start_pos)
        self.anim.stop()
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(end_pos)
        self.anim.start()
        
    def hide_menu(self):
        if self.is_closing: return
        self.is_closing = True
        
        # Animate Out
        start_pos = self.menu_panel.pos()
        end_pos = QPoint(self.width(), 0)
        
        self.anim.stop()
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(end_pos)
        self.anim.start()
    
    def _on_anim_finished(self):
        if self.is_closing:
            self.hide()
            self.is_closing = False

    def init_inventory_view(self):
        layout = QVBoxLayout(self.view_inventory)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.inv_list = QListWidget()
        self.inv_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.inv_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.inv_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.inv_list.customContextMenuRequested.connect(self.show_inv_context_menu)
        self.inv_list.setStyleSheet("""
            QListWidget { background-color: #222; border: 1px solid #444; outline: none; border-radius: 4px; }
            QListWidget::item { border-bottom: 1px solid #333; padding: 0px; }
            QListWidget::item:selected { background-color: transparent; border: none; }
            QListWidget::item:hover { background-color: transparent; }
        """)
        layout.addWidget(self.inv_list)

    def init_equipment_view(self):
        layout = QVBoxLayout(self.view_equipment)
        layout.setContentsMargins(10, 10, 10, 10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.layout_slots = QVBoxLayout(container)
        self.layout_slots.setSpacing(10)
        self.layout_slots.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def init_companions_view(self):
        layout = QVBoxLayout(self.view_companions)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.comp_list = QListWidget()
        self.comp_list.setStyleSheet("background-color: #222; border: 1px solid #444; border-radius: 4px; color: #eee;")
        layout.addWidget(self.comp_list)

    def init_quests_view(self):
        layout = QVBoxLayout(self.view_quests)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.quests_list = QListWidget()
        self.quests_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.quests_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.quests_list.setStyleSheet("""
            QListWidget { background-color: #222; border: 1px solid #444; outline: none; border-radius: 4px; }
            QListWidget::item { border-bottom: 1px solid #333; padding: 0px; }
            QListWidget::item:hover { background-color: transparent; }
        """)
        layout.addWidget(self.quests_list)

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.btn_group):
            btn.setChecked(i == index)
        self.refresh_current_view()

    def show_menu(self, tab_index=0):
        self.show()
        self.raise_()
        self.switch_tab(tab_index)
        
    def hide_menu(self):
        self.hide()

    def refresh_current_view(self):
        idx = self.stack.currentIndex()
        if idx == 0: self.refresh_inventory()
        elif idx == 1: self.refresh_equipment()
        elif idx == 2: self.refresh_quests()
        elif idx == 3: self.refresh_companions()

    def refresh_inventory(self):
        self.inv_list.clear()
        if not self.story_manager: return
        
        inv_data = self.story_manager.variables.get_var("inventory", {})
        equipped_data = self.story_manager.variables.get_var("equipped", {})
        
        # Type safety checks
        if not isinstance(inv_data, dict):
            inv_data = {}
        if not isinstance(equipped_data, dict):
            equipped_data = {}
            
        project_items = self.story_manager.project.items if self.story_manager.project else {}
        # Adjust assets path relative to this file location (src/ui/...)
        # Actually, __file__ will be src/ui/sliding_menu.py, so assets are in ../assets/icons
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons")
        
        if not inv_data:
            self.inv_list.addItem("Inventaire vide.")
            return

        # Create a set of equipped item IDs for fast lookup
        equipped_ids = set(equipped_data.values())

        for item_id, qty in inv_data.items():
            item_def = project_items.get(item_id)
            is_equipped = item_id in equipped_ids
            
            widget = InventoryItemWidget(item_def, qty, assets_dir, is_equipped)
            
            list_item = QListWidgetItem(self.inv_list)
            list_item.setSizeHint(widget.sizeHint())
            list_item.setData(Qt.ItemDataRole.UserRole, item_id)
            
            self.inv_list.addItem(list_item)
            self.inv_list.setItemWidget(list_item, widget)

    def show_inv_context_menu(self, pos):
        item = self.inv_list.itemAt(pos)
        if not item: return
        
        item_id = item.data(Qt.ItemDataRole.UserRole)
        if not item_id: return
        
        project_items = self.story_manager.project.items if self.story_manager.project else {}
        item_def = project_items.get(item_id)
        if not item_def: return
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2a2a2a; color: #eee; border: 1px solid #444; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #3a3a3a; }
        """)
        
        if item_def.type in ["weapon", "armor"]:
            action_equip = menu.addAction("Équiper")
            action_equip.triggered.connect(lambda: self.equip_item(item_id, item_def))
            
        menu.exec(self.inv_list.mapToGlobal(pos))

    def equip_item(self, item_id, item_def):
        slot = "weapon"
        props = item_def.properties
        if item_def.type == "armor":
            subtype = props.get("subtype", "").lower()
            if "tête" in subtype or "head" in subtype: slot = "head"
            elif "torse" in subtype or "chest" in subtype: slot = "torso"
            elif "bras" in subtype or "arms" in subtype: slot = "arms"
            elif "jambes" in subtype or "legs" in subtype: slot = "legs"
            elif "pieds" in subtype or "feet" in subtype: slot = "feet"
            else: slot = "torso"
            
        self.story_manager.variables.equip_item(item_id, slot)
        self.refresh_inventory()

    def refresh_equipment(self):
        while self.layout_slots.count():
            child = self.layout_slots.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        if not self.story_manager: return
        
        equipped = self.story_manager.variables.get_var("equipped", {})
        if not isinstance(equipped, dict):
            equipped = {}
            
        project_items = self.story_manager.project.items if self.story_manager.project else {}
        
        slots = ["head", "torso", "arms", "legs", "feet", "weapon"]
        slot_names = {"head": "Tête", "torso": "Torse", "arms": "Bras", "legs": "Jambes", "feet": "Pieds", "weapon": "Arme"}
        
        for slot in slots:
            slot_name = slot_names.get(slot, slot.capitalize())
            item_id = equipped.get(slot)
            
            slot_widget = QFrame()
            slot_widget.setStyleSheet("background-color: #222; border: 1px solid #444; border-radius: 6px;")
            slot_layout = QHBoxLayout(slot_widget)
            slot_layout.setContentsMargins(10, 10, 10, 10)
            
            lbl_slot = QLabel(slot_name)
            lbl_slot.setStyleSheet("font-weight: bold; color: #888; font-size: 14px; width: 60px;")
            slot_layout.addWidget(lbl_slot)
            
            if item_id:
                item_def = project_items.get(item_id)
                name = item_def.name if item_def else item_id
                lbl_item = QLabel(name)
                lbl_item.setStyleSheet("color: #eee; font-weight: bold; font-size: 14px;")
                slot_layout.addWidget(lbl_item)
                
                slot_layout.addStretch()
                
                btn_unequip = QPushButton("✕")
                btn_unequip.setToolTip("Déséquiper")
                btn_unequip.setFixedSize(24, 24)
                btn_unequip.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_unequip.clicked.connect(lambda checked, s=slot: self.unequip_item(s))
                btn_unequip.setStyleSheet("QPushButton { background-color: #333; color: #aaa; border: none; border-radius: 12px; font-weight: bold; } QPushButton:hover { background-color: #c42b1c; color: white; }")
                slot_layout.addWidget(btn_unequip)
            else:
                lbl_empty = QLabel("Vide")
                lbl_empty.setStyleSheet("color: #555; font-style: italic;")
                slot_layout.addWidget(lbl_empty)
                slot_layout.addStretch()
            
            self.layout_slots.addWidget(slot_widget)
        self.layout_slots.addStretch()

    def unequip_item(self, slot):
        self.story_manager.variables.unequip_item(slot)
        self.refresh_equipment()

    def refresh_companions(self):
        self.comp_list.clear()
        if not self.story_manager: return
        companions = self.story_manager.variables.get_var("companions", [])
        if companions:
            for npc in companions:
                self.comp_list.addItem(f"👤 {npc}")
        else:
            self.comp_list.addItem("Aucun compagnon.")

    def refresh_quests(self):
        self.quests_list.clear()
        if not self.story_manager or not self.story_manager.project: return
        
        active_ids = self.story_manager.variables.get_var("active_quests", [])
        completed_ids = self.story_manager.variables.get_var("completed_quests", [])
        returned_ids = self.story_manager.variables.get_var("returned_quests", [])
        quest_steps = self.story_manager.variables.get_var("quest_steps", {})
        
        has_quests = False
        
        # Display Active Quests
        for qid in active_ids:
            if qid in returned_ids: continue
            
            quest = self.story_manager.project.quests.get(qid)
            if quest:
                has_quests = True
                
                # Determine current step text
                step_idx = quest_steps.get(qid, 0)
                step_text = None
                if quest.steps and step_idx < len(quest.steps):
                    step_text = quest.steps[step_idx]
                elif quest.steps:
                    step_text = quest.steps[-1] # Fallback to last step if index overflow
                
                self._add_quest_item(quest, "active", step_text)
                
        # Display Completed Quests
        for qid in completed_ids:
            if qid in returned_ids: continue
            
            quest = self.story_manager.project.quests.get(qid)
            if quest:
                has_quests = True
                self._add_quest_item(quest, "completed", None)

        if not has_quests:
            item = QListWidgetItem("Aucune quête active.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.quests_list.addItem(item)

    def _add_quest_item(self, quest, status, step_text):
        widget = QuestItemWidget(quest, status, step_text)
        item = QListWidgetItem(self.quests_list)
        item.setSizeHint(widget.sizeHint())
        self.quests_list.addItem(item)
        self.quests_list.setItemWidget(item, widget)
