import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QListWidget, QFrame, QScrollArea, QStackedWidget, QListWidgetItem, 
                             QGraphicsDropShadowEffect, QMenu, QSizePolicy, QGraphicsOpacityEffect,
                             QGridLayout)
from PyQt6.QtGui import QPixmap, QIcon, QColor, QFont
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup

# ==============================================================================
# HELPER WIDGETS (Ported from SlidingMenu)
# ==============================================================================

# ==============================================================================
# Helper Widgets
# ==============================================================================
from src.ui.tooltips import ItemTooltip

class ThemedMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
         # Enforce PointingHandCursor for the entire menu to ensure custom cursor is used
         # assuming global stylesheet sets QWidget { cursor: ... } or we set it explicitly if needed.
         # But the user specifically asked for "gardent les curseur png".
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setStyleSheet("""
            QMenu {
                background-color: #1a1a1a;
                color: #d4c59a; /* Dull Gold */
                border: 1px solid #333;
                font-family: 'Underdog';
                font-size: 14px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #333;
                color: #d4c59a;
            }
        """)

class InventorySlotWidget(QFrame):
    def __init__(self, item_def, qty, assets_dir, is_equipped=False, is_new=False, tooltip_widget=None, on_interaction_callback=None):
        super().__init__()
        self.item_def = item_def
        self.tooltip_widget = tooltip_widget
        self.assets_dir = assets_dir
        self.is_new = is_new
        self.on_interaction_callback = on_interaction_callback
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(180, 64)
        self.setMouseTracking(True)
        self.setMouseTracking(True)
        # Main Widget is transparent container
        self.setStyleSheet("background: transparent; border: none;")
        
        # Inner Frame (Visual Box)
        self.inner_frame = QFrame(self)
        self.inner_frame.setMouseTracking(True)
        self.inner_frame.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) # Pass events to Main
        
        # Style Inner Frame
        # Base: Obsidian (#080808) + Iron (#333)
        # Equipped: Shadowed Gold (#141208) + Antique Gold (#7d7248)
        if is_equipped:
             self.inner_frame.setStyleSheet("""
                QFrame {
                    background-color: #141208; 
                    border: 1px solid #7d7248;
                    border-radius: 2px;
                }
            """)
        else:
             self.inner_frame.setStyleSheet("""
                QFrame {
                    background-color: #080808;
                    border: 1px solid #333;
                    border-radius: 2px;
                }
            """)

        # Layout for Inner Frame (Text)
        inner_layout = QVBoxLayout(self.inner_frame)
        inner_layout.setContentsMargins(10, 8, 10, 8)
        inner_layout.setSpacing(2)
        
        # 1. Name
        # 1. Name
        name_text = item_def.name if item_def else "Unknown"
        self.lbl_name = QLabel(name_text)
        self.lbl_name.setStyleSheet("color: #d4c59a; font-weight: bold; font-family: 'Underdog'; font-size: 12px; background: transparent; border: none;")
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        self.lbl_name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.lbl_name.setWordWrap(True)
        inner_layout.addWidget(self.lbl_name)
        
        # 2. Details
        itype = item_def.type.lower()
        type_map = {
            "weapon": "Arme", "armor": "Armure",
            "consumable": "Consommable", "potion": "Potion",
            "quest": "Objet de Quête", "gold": "Or", "currency": "Monnaie",
            "material": "Matériau", "junk": "Bric-à-brac"
        }
        details_text = type_map.get(itype, itype.capitalize())
        details_text = type_map.get(itype, itype.capitalize())
        lbl_details = QLabel(details_text)
        lbl_details.setStyleSheet("color: #888; font-size: 11px; font-style: italic; background: transparent; border: none;")
        lbl_details.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        lbl_details.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) 
        inner_layout.addWidget(lbl_details)
        
        # --- Overlay Badges (Children of Main Widget, floating over InnerFrame) ---
        
        # New Badge (Dark Blood)
        self.lbl_new = None
        if self.is_new:
            self.lbl_new = QLabel("NOUVEAU", self)
            self.lbl_new.setStyleSheet("""
                background-color: #4a0a0a; 
                color: #d4c59a; 
                font-size: 8px; 
                font-family: 'Underdog';
                border-radius: 0px; 
                padding: 1px 4px;
                min-width: 30px;
                border: 1px solid #8a1c1c;
            """)
            self.lbl_new.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_new.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.lbl_new.adjustSize()
            self.lbl_new.show()

        # Equipped Badge (Gold Tag)
        self.lbl_eq = None
        if is_equipped:
            self.lbl_eq = QLabel("ÉQUIPÉ", self)
            self.lbl_eq.setStyleSheet("""
                background-color: #141208; 
                color: #d4c59a; 
                font-size: 8px; 
                font-family: 'Underdog';
                border-radius: 0px; 
                padding: 1px 4px;
                min-width: 30px;
                border: 1px solid #7d7248;
            """)
            self.lbl_eq.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_eq.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.lbl_eq.adjustSize()
            self.lbl_eq.show()

        # Stack Badge (Iron Tag)
        self.lbl_count = None
        if qty > 1:
            self.lbl_count = QLabel(f"{qty}", self)
            self.lbl_count.setStyleSheet("""
                background-color: #1a1a1a; 
                color: #aaa; 
                font-size: 10px; 
                font-weight: bold; 
                border-radius: 0px; 
                padding: 0px 4px;
                min-width: 12px;
                border: 1px solid #444;
            """)
            self.lbl_count.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_count.adjustSize()
            self.lbl_count.show()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # Position Inner Frame with larger margin to allow "floating" badges
        margin_x = 12
        margin_y = 6
        self.inner_frame.setGeometry(margin_x, margin_y, self.width() - 2*margin_x, self.height() - 2*margin_y)
        
        # Position Badges relative to OUTER container
        # Do NOT push beyond self.width() or it clips.
        # Right align with 0 or small positive padding.
        
        overlap_offset = 0
        
        if self.lbl_eq:
            bw = self.lbl_eq.width()
            self.lbl_eq.move(self.width() - bw - overlap_offset, 0)
            self.lbl_eq.raise_()
            if self.lbl_new: self.lbl_new.hide()
            
        elif self.lbl_new:
            bw = self.lbl_new.width()
            self.lbl_new.move(self.width() - bw - overlap_offset, 0)
            self.lbl_new.raise_()
            self.lbl_new.show()
            
        if self.lbl_count:
            bw = self.lbl_count.width()
            bh = self.lbl_count.height()
            self.lbl_count.move(self.width() - bw - overlap_offset, self.height() - bh - 0)
            self.lbl_count.raise_()
            
    def enterEvent(self, event):
        super().enterEvent(event)
        
        # New Item Logic
        if self.is_new and self.lbl_new and self.lbl_new.isVisible():
            self.lbl_new.hide()
            self.is_new = False
            if self.on_interaction_callback:
                self.on_interaction_callback(self.item_def.id)

        # Hover effect on Inner Frame
        if "141208" in self.inner_frame.styleSheet(): # Equipped
             self.inner_frame.setStyleSheet("""
                QFrame {
                    background-color: #242218; 
                    border: 1px solid #9d9268;
                    border-radius: 2px;
                }
            """)
        else:
             self.inner_frame.setStyleSheet("""
                QFrame {
                    background-color: #1a1a1a; 
                    border: 1px solid #777;
                    border-radius: 2px;
                }
            """)
            
        if self.tooltip_widget:
            self.tooltip_widget.update_data(self.item_def, self.assets_dir)
            self.tooltip_widget.move_to_mouse()
            self.tooltip_widget.show()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        # Restore Style
        if self.lbl_eq: # Check existence of eq badge primarily means is_equipped
             self.inner_frame.setStyleSheet("""
                QFrame {
                    background-color: #141208; 
                    border: 1px solid #7d7248;
                    border-radius: 2px;
                }
            """)
        else:
             self.inner_frame.setStyleSheet("""
                QFrame {
                    background-color: #080808;
                    border: 1px solid #333;
                    border-radius: 2px;
                }
            """)
            
        if self.tooltip_widget:
            self.tooltip_widget.hide()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.tooltip_widget and self.tooltip_widget.isVisible():
            self.tooltip_widget.move_to_mouse(event.globalPosition().toPoint())

class QuestItemWidget(QFrame):
    def __init__(self, quest, status, step_text):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #080808;
                border: 1px solid #333;
                border-radius: 2px;
                margin-bottom: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header: Title + Status
        header_layout = QHBoxLayout()
        
        lbl_title = QLabel(quest.title)
        lbl_title.setStyleSheet("color: #d4c59a; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        header_layout.addWidget(lbl_title)
        
        header_layout.addStretch()
        
        status_color = "#888"
        if status == "active": status_color = "#ffcc80"
        elif status == "completed": status_color = "#66bb6a"
        
        lbl_status = QLabel(status.upper())
        # Color Logic: Active=Gold, Completed=Green
        if status == "active": 
            lbl_status.setStyleSheet(f"color: #d4c59a; font-size: 10px; font-weight: bold; border: 1px solid #7d7248; border-radius: 2px; padding: 2px 5px; background: transparent;")
        elif status == "completed":
            lbl_status.setStyleSheet(f"color: #5a835a; font-size: 10px; font-weight: bold; border: 1px solid #4caf50; border-radius: 2px; padding: 2px 5px; background: transparent;")
        else:
             lbl_status.setStyleSheet(f"color: #888; font-size: 10px; font-weight: bold; border: 1px solid #444; border-radius: 2px; padding: 2px 5px; background: transparent;")
        
        header_layout.addWidget(lbl_status)
        
        layout.addLayout(header_layout)
        
        # Step Text
        if step_text:
            lbl_step = QLabel(step_text)
            lbl_step.setWordWrap(True)
            lbl_step.setStyleSheet("color: #ccc; font-style: italic; margin-top: 5px; border: none; background: transparent;")
            layout.addWidget(lbl_step)
# ==============================================================================
# MAIN MENU CLASS
# ==============================================================================

class GameMenu(QWidget):
    def __init__(self, parent=None, story_manager=None):
        super().__init__(parent)
        self.story_manager = story_manager
        # Cover entire window
        self.resize(parent.size())
        
        # Setup UI
        self._init_ui()
        
        # Hidden by default
        self.hide()
        self.is_closing = False

    def _init_ui(self):
        # 1. Background Dimmer
        self.dimmer = QWidget(self)
        self.dimmer.setStyleSheet("background-color: rgba(0, 0, 0, 0.7);")
        self.dimmer.resize(self.size())
        
        # 2. Central Panel
        self.panel = QFrame(self)
        self.panel.setFixedSize(900, 600)
        self.panel.setStyleSheet("""
            QFrame {
                background-color: #0f0f0f;
                border: 1px solid #444;
                border-radius: 2px;
            }
        """)
        
        # Layout inside Panel using HBox for Sidebar + Content
        panel_layout = QHBoxLayout(self.panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        
        # --- LEFT SIDEBAR (Navigation) ---
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("""
            QWidget {
                background-color: #161616;
                border-right: 1px solid #333;
                border-top-left-radius: 2px;
                border-bottom-left-radius: 2px;
            }
            QLabel { background: transparent; border: none; color: #666; font-weight: bold; padding: 10px; }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(10)
        
        # Header "SYSTEM" or "MENU"
        lbl_menu = QLabel("MENU")
        lbl_menu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_menu.setStyleSheet("font-size: 18px; color: #888; letter-spacing: 2px; margin-bottom: 20px;")
        sidebar_layout.addWidget(lbl_menu)
        
        # New Item Logic (Session based)
        self.seen_items = set()

        self.btn_group = []

        # Navigation Buttons
        self.btn_inv = self._add_nav_btn("Inventaire", 0, sidebar_layout)
        self.btn_equip = self._add_nav_btn("Équipement", 1, sidebar_layout)
        self.btn_quests = self._add_nav_btn("Quêtes", 2, sidebar_layout)
        self.btn_comp = self._add_nav_btn("Compagnons", 3, sidebar_layout)
        
        sidebar_layout.addStretch()
        
        # Close Button (Bottom of sidebar) - Professional Footer Style
        btn_close = QPushButton("RETOUR AU JEU")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.hide_menu)
        btn_close.setFixedHeight(45)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #0c0c0c;
                color: #888;
                border: none;
                border-top: 1px solid #333;
                font-weight: bold;
                font-size: 12px;
                letter-spacing: 2px;
                text-align: center;
                border-bottom-left-radius: 2px;
            }
            QPushButton:hover {
                background-color: #4a0a0a;
                color: #d4c59a;
                border-top: 1px solid #8a1c1c;
            }
        """)
        sidebar_layout.addWidget(btn_close)
        
        panel_layout.addWidget(self.sidebar)
        
        # --- RIGHT CONTENT AREA ---
        self.content_area = QWidget()
        self.content_area.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header for Content (Dynamic Title)
        self.lbl_page_title = QLabel("INVENTAIRE")
        self.lbl_page_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #eee; margin-bottom: 10px; font-family: 'Underdog'; letter-spacing: 2px;")
        content_layout.addWidget(self.lbl_page_title)
        
        # Stacked Widget
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        
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
        
        panel_layout.addWidget(self.content_area)
        
        # Initial Selection
        self.switch_tab(0)

    def _add_nav_btn(self, text, index, layout):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(40)
        btn.clicked.connect(lambda: self.switch_tab(index))
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                border-left: 2px solid transparent;
                font-size: 13px;
                text-align: left;
                padding-left: 25px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #222;
                color: #ccc;
            }
            QPushButton:checked {
                background-color: #262626;
                color: #d4c59a;
                border-left: 2px solid #7d7248;
            }
        """)
        layout.addWidget(btn)
        self.btn_group.append(btn)
        return btn

    def resizeEvent(self, event):
        self.dimmer.resize(self.size())
        # Center Panel
        self.panel.move(
            (self.width() - self.panel.width()) // 2,
            (self.height() - self.panel.height()) // 2
        )
        super().resizeEvent(event)
        
    def show_menu(self, tab_index=0):
        if self.parent():
            self.resize(self.parent().size())
            
        self.show()
        self.raise_()
        self.switch_tab(tab_index)
        
        # Simple Fade In Animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.start()

    def hide_menu(self):
        if self.is_closing: return
        self.is_closing = True
        
        # Fade Out
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(150)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self._on_close_finished)
        self.anim.start()
        
    def _on_close_finished(self):
        self.hide()
        self.is_closing = False

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.btn_group):
            btn.setChecked(i == index)
            
        titles = ["INVENTAIRE", "ÉQUIPEMENT", "JOURNAL DE QUÊTES", "COMPAGNONS"]
        if 0 <= index < len(titles):
            self.lbl_page_title.setText(titles[index])
            
        self.refresh_current_view()

    def refresh_current_view(self):
        idx = self.stack.currentIndex()
        if idx == 0: self.refresh_inventory()
        elif idx == 1: self.refresh_equipment()
        elif idx == 2: self.refresh_quests()
        elif idx == 3: self.refresh_companions()

    # ==========================================================================
    # LOGIC PORTED FROM SLIDING MENU
    # ==========================================================================

    def init_inventory_view(self):
        # Container for the grid
        self.inv_container = QWidget()
        self.inv_container.setStyleSheet("background: transparent;")
        
        # Grid Layout
        self.inv_grid = QGridLayout(self.inv_container)
        self.inv_grid.setContentsMargins(0, 0, 0, 0)
        self.inv_grid.setSpacing(8)
        self.inv_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) # Force Vertical Only
        scroll.setWidget(self.inv_container)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #111; width: 6px; margin: 0; }
            QScrollBar::handle:vertical { background: #444; min-height: 20px; border-radius: 2px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal { height: 0px; background: transparent; }
        """)
        
        # Main layout for the view page
        layout = QVBoxLayout(self.view_inventory)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        # Tooltip Instance
        self.item_tooltip = ItemTooltip(self)

    def refresh_inventory(self):
        # Clear Grid
        while self.inv_grid.count():
            child = self.inv_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        if not self.story_manager: return
        
        inv_data = self.story_manager.variables.get_var("inventory", {})
        equipped_data = self.story_manager.variables.get_var("equipped", {})
        
        if not isinstance(inv_data, dict): inv_data = {}
        if not isinstance(equipped_data, dict): equipped_data = {}
            
        project_items = self.story_manager.project.items if self.story_manager.project else {}
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons")
        
        equipped_ids = set(equipped_data.values())

        row, col = 0, 0
        cols_per_row = 3
        
        if not inv_data:
            lbl_empty = QLabel("Inventaire vide.")
            lbl_empty.setStyleSheet("color: #666; font-style: italic; margin-top: 20px;")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.inv_grid.addWidget(lbl_empty, 0, 0, 1, cols_per_row)
            return

        # Sorting Logic
        def sort_key(item_tuple):
            i_id = item_tuple[0]
            item_def = project_items.get(i_id)
            if not item_def: return (999, "")
            
            # Type Priority
            type_order = {
                "weapon": 0,
                "armor": 1,
                "potion": 2,
                "consumable": 3,
                "material": 4,
                "quest": 5,
                "gold": 6, "currency": 6,
                "junk": 99
            }
            t_order = type_order.get(item_def.type.lower(), 50)
            return (t_order, item_def.name)

        sorted_items = sorted(inv_data.items(), key=sort_key)

        for item_id, qty in sorted_items:
            item_def = project_items.get(item_id)
            is_equipped = item_id in equipped_ids
            is_new = item_id not in self.seen_items
            
            slot = InventorySlotWidget(item_def, qty, assets_dir, is_equipped, is_new, self.item_tooltip, self.mark_as_seen)
            # Add context menu support
            slot.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            slot.customContextMenuRequested.connect(lambda pos, i=item_id, d=item_def: self.show_slot_context_menu(pos, i, d))
            
            self.inv_grid.addWidget(slot, row, col)
            
            col += 1
            if col >= cols_per_row:
                col = 0
                row += 1

    def show_slot_context_menu(self, pos, item_id, item_def):
        if not item_def: return
        
        # Use ThemedMenu for Custom Cursor and Style
        menu = ThemedMenu(self)
        
        equipped_data = self.story_manager.variables.get_var("equipped", {})
        if not isinstance(equipped_data, dict): equipped_data = {}
        
        # Check if equipped (value of any slot)
        equipped_slot = None
        for slot, i_id in equipped_data.items():
            if i_id == item_id:
                equipped_slot = slot
                break
        
        if item_def.type in ["weapon", "armor"]:
            if equipped_slot:
                action_unequip = menu.addAction("Déséquiper")
                action_unequip.triggered.connect(lambda: self.unequip_item(equipped_slot))
                # Refresh inventory also needed after unequip, unequip_item only refreshes equipment view
                # We should update unequip_item to refresh current view if needed? 
                # Or just call refresh_current_view here? 
                # unequip_item calls refresh_equipment. If we are in inventory view, we need refresh_inventory.
                # Let's verify unequip_item or just chain the call.
                action_unequip.triggered.connect(self.refresh_inventory)
            else:
                action_equip = menu.addAction("Équiper")
                action_equip.triggered.connect(lambda: self.equip_item(item_id, item_def))
            
        # We need to map the global position correctly because 'pos' is relative to the slot widget
        sender_widget = self.sender()
        if sender_widget:
            global_pos = sender_widget.mapToGlobal(pos)
            menu.exec(global_pos)

    def mark_as_seen(self, item_id):
        if item_id not in self.seen_items:
            self.seen_items.add(item_id)
            # Optional: Persist this state if needed/requested

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

    def init_equipment_view(self):
        layout = QVBoxLayout(self.view_equipment)
        layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container.setFixedWidth(600) # Centered Fixed Width
        
        self.layout_slots = QVBoxLayout(container)
        self.layout_slots.setSpacing(10)
        self.layout_slots.setContentsMargins(0, 0, 0, 0)
        
        # Wrapper to center the container
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        wrapper_layout.addWidget(container)
        
        scroll.setWidget(wrapper)
        layout.addWidget(scroll)

    def refresh_equipment(self):
        while self.layout_slots.count():
            child = self.layout_slots.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        if not self.story_manager: return
        
        equipped = self.story_manager.variables.get_var("equipped", {})
        if not isinstance(equipped, dict): equipped = {}
        project_items = self.story_manager.project.items if self.story_manager.project else {}
        
        slots = ["head", "torso", "arms", "legs", "feet", "weapon"]
        slot_names = {"head": "Tête", "torso": "Torse", "arms": "Bras", "legs": "Jambes", "feet": "Pieds", "weapon": "Arme"}
        
        for slot in slots:
            slot_name = slot_names.get(slot, slot.capitalize())
            item_id = equipped.get(slot)
            
            slot_widget = QFrame()
            slot_widget.setStyleSheet("background-color: #080808; border: 1px solid #333; border-radius: 2px;")
            slot_layout = QHBoxLayout(slot_widget)
            slot_layout.setContentsMargins(15, 15, 15, 15)
            
            lbl_slot = QLabel(slot_name)
            lbl_slot.setStyleSheet("font-weight: bold; color: #888; font-size: 14px; width: 60px;")
            slot_layout.addWidget(lbl_slot)
            
            if item_id:
                item_def = project_items.get(item_id)
                name = item_def.name if item_def else item_id
                lbl_item = QLabel(name)
                lbl_item.setStyleSheet("color: #d4c59a; font-weight: bold; font-size: 15px;")
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

    def init_quests_view(self):
        layout = QVBoxLayout(self.view_quests)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.quests_list = QListWidget()
        self.quests_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.quests_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.quests_list.setStyleSheet("""
            QListWidget { background-color: #222; border: 1px solid #333; outline: none; border-radius: 4px; }
            QListWidget::item { border-bottom: 1px solid #333; padding: 0px; }
            QListWidget::item:hover { background-color: transparent; }
        """)
        # Scroll Bar Styling
        self.quests_list.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical { background: #111; width: 6px; margin: 0; }
            QScrollBar::handle:vertical { background: #444; min-height: 20px; border-radius: 2px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        layout.addWidget(self.quests_list)

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
                step_idx = quest_steps.get(qid, 0)
                step_text = None
                if quest.steps and step_idx < len(quest.steps):
                    step_text = quest.steps[step_idx]
                elif quest.steps:
                    step_text = quest.steps[-1]
                
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

    def init_companions_view(self):
        layout = QVBoxLayout(self.view_companions)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.comp_list = QListWidget()
        self.comp_list.setStyleSheet("background-color: #222; border: 1px solid #333; border-radius: 4px; color: #eee;")
        layout.addWidget(self.comp_list)

    def refresh_companions(self):
        self.comp_list.clear()
        if not self.story_manager: return
        companions = self.story_manager.variables.get_var("companions", [])
        if companions:
            for npc in companions:
                self.comp_list.addItem(f"👤 {npc}")
        else:
            self.comp_list.addItem("Aucun compagnon.")
