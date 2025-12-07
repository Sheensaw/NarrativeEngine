# main_player.py
import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QFileDialog, QMessageBox, QFrame, QScrollArea, QGraphicsOpacityEffect, QDialog)
from PyQt6.QtGui import QFontDatabase, QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize, QUrl, QTimer, QPropertyAnimation, QEasingCurve

from src.core.models import ProjectModel, ItemModel
from src.core.serializer import ProjectSerializer
from src.engine.story_manager import StoryManager
from src.core.database import DatabaseManager
from src.ui.game_menu import GameMenu
from src.ui.animated_widgets import FadeTextEdit

class QuestOfferDialog(QDialog):
    def __init__(self, parent, quest, project):
        super().__init__(parent)
        self.quest = quest
        self.project = project
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 450)
        
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Background Frame
        self.frame = QFrame()
        self.frame.setObjectName("QuestDialogFrame")
        self.frame.setStyleSheet("""
            QFrame#QuestDialogFrame {
                background-color: #1a1a1a;
                border: 2px solid #b1a270;
                border-radius: 8px;
            }
            QLabel { font-family: 'Underdog'; color: #eee; }
            QTextEdit { background-color: rgba(0,0,0,0.3); border: none; font-size: 16px; padding: 10px; color: #ddd; border-radius: 4px; }
            QPushButton { background-color: #333; color: #ccc; border: 1px solid #555; padding: 10px 20px; font-size: 14px; border-radius: 4px; font-family: 'Underdog'; }
            QPushButton:hover { background-color: #444; border-color: #777; color: #fff; }
            QPushButton#AcceptBtn { background-color: #5d4037; border-color: #8d6e63; color: #ffcc80; }
            QPushButton#AcceptBtn:hover { background-color: #6d4c41; border-color: #a1887f; }
            QPushButton#RefuseBtn { background-color: #333; border-color: #555; }
            QPushButton#RefuseBtn:hover { background-color: #444; border-color: #777; }
        """)
        main_layout.addWidget(self.frame)
        
        content_layout = QVBoxLayout(self.frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header (Title + icon maybe?)
        lbl_header = QLabel("OFFRE DE QUÊTE")
        lbl_header.setStyleSheet("color: #888; font-size: 12px; font-weight: bold; letter-spacing: 2px;")
        lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(lbl_header)
        
        # Title using Quest Title
        lbl_title = QLabel(quest.title.upper())
        lbl_title.setStyleSheet("font-size: 26px; font-weight: bold; color: #b1a270; margin-bottom: 5px;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setWordWrap(True)
        content_layout.addWidget(lbl_title)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #444;")
        content_layout.addWidget(line)

        # Presentation Text
        txt_desc = QTextEdit()
        txt_desc.setReadOnly(True)
        txt_desc.setPlainText(quest.presentation_text if quest.presentation_text else quest.description)
        content_layout.addWidget(txt_desc)
        
        # Loot Preview
        if quest.loot and (quest.loot.get("xp") or quest.loot.get("gold") or quest.loot.get("items")):
            lbl_loot = QLabel("Récompenses :")
            lbl_loot.setStyleSheet("font-weight: bold; margin-top: 10px; color: #bbb;")
            content_layout.addWidget(lbl_loot)
            
            loot_text = []
            if quest.loot.get("xp"): loot_text.append(f"+{quest.loot['xp']} XP")
            if quest.loot.get("gold"): loot_text.append(f"+{quest.loot['gold']} Or")
            
            for item_id, qty in quest.loot.get("items", {}).items():
                item_name = item_id
                if self.project and item_id in self.project.items:
                    item_name = self.project.items[item_id].name
                loot_text.append(f"{qty}x {item_name}")
                
            lbl_loot_val = QLabel(" • ".join(loot_text))
            lbl_loot_val.setStyleSheet("color: #ffcc80; font-style: italic; margin-bottom: 20px; font-size: 14px;")
            lbl_loot_val.setWordWrap(True)
            content_layout.addWidget(lbl_loot_val)
        else:
             content_layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_refuse = QPushButton("Refuser")
        btn_refuse.setObjectName("RefuseBtn")
        btn_refuse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refuse.clicked.connect(self.reject)
        
        btn_accept = QPushButton("Accepter")
        btn_accept.setObjectName("AcceptBtn")
        btn_accept.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_accept.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_refuse)
        btn_layout.addWidget(btn_accept)
        content_layout.addLayout(btn_layout)

    # Enable moving the window by dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

class PlayerWindow(QMainWindow):
    def __init__(self, project_file=None):
        super().__init__()
        self.setWindowTitle("Narrative Player")
        self.setWindowIcon(QIcon("src/assets/icon.ico"))
        self.resize(1280, 720)
        
        # 1. Load Stylesheet
        self._load_stylesheet()
        self._load_font()

        # 2. Managers
        self.db_manager = DatabaseManager()
        self.story_manager = StoryManager()
        
        # Connect signals
        self.story_manager.variables.add_observer(self.on_variable_changed)

        # 3. UI Setup
        self._init_ui()
        
        # 4. Sliding Menu (Overlay)
        # 4. Game Menu (Central Overlay)
        self.game_menu = GameMenu(self, self.story_manager)
        self.game_menu.hide()

        # 5. Load Project if provided
        if project_file:
            self.load_project(project_file)
        else:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.open_project_dialog)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep menu full size (transparent overlay)
        if hasattr(self, 'game_menu'):
            self.game_menu.resize(self.width(), self.height())
        
        
        # Enforce 4:3 Content Area
        if hasattr(self, 'main_area') and hasattr(self, 'content_layout'):
            # Calculate target dimensions
            w = self.main_area.width()
            h = self.main_area.height()
            
            # Target Ratio 4:3
            target_ratio = 4.0 / 3.0
            
            # If wider than 4:3, constrain width
            if h > 0:
                current_ratio = w / h
                if current_ratio > target_ratio:
                    target_width = h * target_ratio
                    margin = int((w - target_width) / 2)
                    self.content_layout.setContentsMargins(margin, 50, margin, 50)
                else:
                    # If taller than 4:3 (portrait), we typically don't constrain height for text flow,
                    # but we keep reasonable side margins.
                    self.content_layout.setContentsMargins(50, 50, 50, 50)

    def keyPressEvent(self, event):
        """Gère les raccourcis clavier."""
        if event.key() == Qt.Key.Key_Return and (event.modifiers() & Qt.KeyboardModifier.AltModifier):
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)

    def _load_stylesheet(self):
        try:
            style_path = os.path.join(os.path.dirname(__file__), "src", "assets", "styles", "player_theme.qss")
            if os.path.exists(style_path):
                with open(style_path, "r") as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Erreur chargement style: {e}")
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; color: #ffffff; font-family: 'Underdog', 'Segoe UI', sans-serif; }
            QTextEdit { background-color: transparent; border: none; font-size: 20px; line-height: 1.6; color: #ffffff; padding: 20px; }
            QPushButton { background-color: #2a2a2a; border: 1px solid #444; color: #eee; padding: 10px 20px; border-radius: 4px; font-size: 16px; font-family: 'Underdog'; }
            QPushButton:hover { background-color: #3a3a3a; border-color: #666; }
            QPushButton:pressed { background-color: #222; }
            QPushButton.choice-btn { text-align: left; font-size: 18px; margin: 5px 0; padding: 15px; border-left: 3px solid #555; }
            QPushButton.choice-btn:enabled:hover { border-left-color: #c42b1c; background-color: #1e1e1e; padding-left: 25px; }
            QPushButton:disabled { color: #555; border-color: #333; background-color: #1a1a1a; border-left-color: #333; padding-left: 15px; }
            QLabel { color: #ffffff; font-family: 'Underdog'; font-size: 16px; }
        """)

    def _load_font(self):
        try:
            font_path = os.path.join(os.path.dirname(__file__), "src", "assets", "fonts", "Underdog.ttf")
            if os.path.exists(font_path):
                id = QFontDatabase.addApplicationFont(font_path)
                if id < 0:
                    print("Erreur chargement font Underdog")
                else:
                    print("Font Underdog chargée")
            else:
                print(f"Font not found at {font_path}")
        except Exception as e:
            print(f"Erreur font: {e}")

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main Layout: Top Bar + Content
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- TOP BAR ---
        self.top_bar = QFrame()
        self.top_bar.setObjectName("TopBar")
        self.top_bar.setFixedHeight(60)
        self.top_bar.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #333;")
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        # --- HUD Elements (Native Widgets) ---
        assets_dir = os.path.join(os.path.dirname(__file__), "src", "assets", "icons")

        # Stats Group
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        self.stat_labels = {}

        def add_stat(name, icon, initial_value):
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(5)
            
            # Icon
            lbl_icon = QLabel()
            icon_path = os.path.join(assets_dir, icon)
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                # No resizing to ensure perfect sharpness (16x16 native)
                lbl_icon.setPixmap(pixmap)
            layout.addWidget(lbl_icon)
            
            # Value
            lbl_val = QLabel(str(initial_value))
            layout.addWidget(lbl_val)
            
            stats_layout.addWidget(container)
            self.stat_labels[name] = lbl_val

        # Health
        add_stat("health", "health.png", "100")

        # Gold
        add_stat("gold", "gold.png", "0")

        # Attributes
        add_stat("strength", "strength.png", "10")
        add_stat("dexterity", "dexterity.png", "10")
        add_stat("resistance", "defense.png", "0")

        top_layout.addLayout(stats_layout)
        top_layout.addStretch()

        # Buttons with Icons
        def create_hud_btn(tooltip, icon_name, callback):
            btn = QPushButton()
            btn.setToolTip(tooltip)
            btn.setObjectName("HUDButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Styling for icon-only button
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("""
                QPushButton#HUDButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 5px;
                }
                QPushButton#HUDButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }
                QPushButton#HUDButton:pressed {
                    background-color: rgba(255, 255, 255, 0.2);
                }
            """)

            icon_path = os.path.join(assets_dir, icon_name)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(28, 28)) # Slightly larger icon
            
            btn.clicked.connect(callback)
            return btn

        btn_inv = create_hud_btn("Inventaire", "inventory.png", lambda: self.toggle_menu(0))
        top_layout.addWidget(btn_inv)

        btn_equip = create_hud_btn("Équipement", "equipment.png", lambda: self.toggle_menu(1))
        top_layout.addWidget(btn_equip)

        btn_quests = create_hud_btn("Quêtes", "quest.png", lambda: self.toggle_menu(2))
        top_layout.addWidget(btn_quests)

        btn_comp = create_hud_btn("Compagnons", "buddy.png", lambda: self.toggle_menu(3))
        top_layout.addWidget(btn_comp)

        main_layout.addWidget(self.top_bar)

        # --- LOCATION TAB (Hanging from Top Bar) ---
        self.lbl_location = QLabel("Eldaron (0, 0)")
        self.lbl_location.setObjectName("LocationTab")
        self.lbl_location.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_location.setFixedSize(400, 50)
        self.lbl_location.setStyleSheet("""
            QLabel#LocationTab {
                background-color: #1a1a1a;
                color: #b1a270;
                border: 1px solid #333;
                border-top: none;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
                font-family: 'Underdog';
                font-size: 14px;
                font-weight: bold;
            }
        """)
        # Container to center it and handle negative margin if needed
        loc_container = QWidget()
        loc_layout = QHBoxLayout(loc_container)
        loc_layout.setContentsMargins(0, 0, 0, 0)
        loc_layout.addWidget(self.lbl_location)
        loc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(loc_container)

        # --- MAIN CONTENT AREA ---
        self.main_area = QWidget()
        self.main_area.setObjectName("MainArea")
        main_layout.addWidget(self.main_area)

        self.content_layout = QVBoxLayout(self.main_area)
        self.content_layout.setContentsMargins(150, 50, 150, 50) # Initial margins, updated by resizeEvent
        self.content_layout.setSpacing(30)
 
        # Story Text
        self.txt_story = FadeTextEdit()
        self.txt_story.setObjectName("StoryText")
        self.txt_story.setReadOnly(True)
        self.txt_story.setFrameShape(QFrame.Shape.NoFrame)
        self.txt_story.finished.connect(self.show_choices_sequentially)
        self.content_layout.addWidget(self.txt_story, 1) # Text takes all remaining space

        # Choices
        self.scroll_choices = QScrollArea()
        self.scroll_choices.setWidgetResizable(True)
        self.scroll_choices.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_choices.setStyleSheet("background: transparent;")
        
        self.choices_container = QWidget()
        self.choices_container.setStyleSheet("background: transparent;")
        self.layout_choices = QVBoxLayout(self.choices_container)
        self.layout_choices.setContentsMargins(0, 0, 0, 0)
        self.layout_choices.setSpacing(10)
        
        self.scroll_choices.setWidget(self.choices_container)
        self.scroll_choices.setWidget(self.choices_container)
        self.content_layout.addWidget(self.scroll_choices, 0) # Stretch 0 to let it adapt to content size, handled in refreshes

    def on_variable_changed(self, name, value):
        """Met à jour l'interface quand une variable change."""
        if name in self.stat_labels:
            self.stat_labels[name].setText(str(value))
        elif name == "max_health":
             pass
        elif name == "player_coordinates":
            # We wait for 'location_text' for the display, but we can keep this for debug or fallback
            pass
        elif name == "location_text" or name.startswith("location_"):
            self.update_location_label()
        elif name == "active_quest_offer":
            if value:
                self.show_quest_offer(value)
        elif name == "active_quests" or name == "completed_quests":
            # State of quests changed, choices might need update (e.g. "Rendre la quête")
            self.refresh_choices_only()

        # Refresh menu if open
        if hasattr(self, 'game_menu') and self.game_menu.isVisible():
            self.game_menu.refresh_current_view()

    def toggle_menu(self, tab_index):
        if self.game_menu.isVisible():
            # If already visible and same tab, hide. If different tab, switch.
            if self.game_menu.stack.currentIndex() == tab_index:
                self.game_menu.hide_menu()
            else:
                self.game_menu.switch_tab(tab_index)
        else:
            self.game_menu.show_menu(tab_index)

    def open_project_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir un projet", "", "JSON Files (*.json)")
        if path:
            self.load_project(path)
        else:
            sys.exit()

    def load_project(self, path):
        project = ProjectSerializer.load_project(path)
        if not project:
            QMessageBox.critical(self, "Erreur", "Impossible de charger le projet.")
            return

        # LOAD DB ITEMS
        db_items = self.db_manager.get_all_items()
        for item_data in db_items.values():
            item = ItemModel(
                id=item_data["id"],
                name=item_data["name"],
                type=item_data["type"],
                description=item_data["description"],
                properties=item_data["data"]
            )
            project.items[item.id] = item

        self.story_manager.load_project(project)
        self.story_manager.start_game()
        self.refresh_ui()

    def refresh_ui(self):
        # 1. Update Text
        text = self.story_manager.get_parsed_text()
        self.txt_story.show_text(text)

        # 2. Update Choices
        while self.layout_choices.count():
            child = self.layout_choices.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        choices = self.story_manager.get_available_choices()
        if not choices and not self.story_manager.current_node:
             lbl = QLabel("Fin de l'histoire.")
             lbl.setStyleSheet("color: #888; font-style: italic; font-size: 16px;")
             self.layout_choices.addWidget(lbl)
        
        for i, choice in enumerate(choices):
            btn = QPushButton(choice["text"])
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("class", "choice-btn")
            btn.clicked.connect(lambda checked, idx=i: self.make_choice(idx))
            
            # Hide initially
            opacity = QGraphicsOpacityEffect(btn)
            opacity.setOpacity(0.0)
            btn.setGraphicsEffect(opacity)
            btn.setVisible(False)
            
            # Store logic disabled state for sequential reveal
            btn.setProperty("logic_disabled", choice.get("disabled", False))
            
            self.layout_choices.addWidget(btn)

        self.layout_choices.addStretch()
        
        # Dynamic resizing of choices area
        count = len(choices) if choices else 1
        needed_height = count * 65 + 40
        final_height = min(needed_height, 350)
        self.scroll_choices.setFixedHeight(final_height)

    def show_choices_sequentially(self):
        """Reveals choices one by one with fade in."""
        # Get all buttons
        buttons = []
        for i in range(self.layout_choices.count()):
            item = self.layout_choices.itemAt(i)
            if item.widget() and isinstance(item.widget(), QPushButton):
                buttons.append(item.widget())
        
        if not buttons:
            return

        self.current_choice_index = 0
        self.choice_buttons = buttons
        
        # Timer for sequential reveal
        self.choice_timer = QTimer(self)
        self.choice_timer.timeout.connect(self._reveal_next_choice)
        self.choice_timer.start(200) # 200ms between choices

    def _reveal_next_choice(self):
        if self.current_choice_index < len(self.choice_buttons):
            btn = self.choice_buttons[self.current_choice_index]
            
            # Apply Logic Disabled state
            is_disabled = btn.property("logic_disabled")
            btn.setEnabled(not is_disabled)
            if is_disabled:
                # Apply disabled visual style explicitly if needed, though properties might handle it
                # But QSS :disabled should work.
                pass

            btn.setVisible(True) # If we hid it
            
            # Fade In
            effect = btn.graphicsEffect()
            if effect:
                anim = QPropertyAnimation(effect, b"opacity", btn)
                anim.setDuration(300)
                anim.setStartValue(0.0)
                anim.setEndValue(1.0)
                anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                anim.start()
            
            self.current_choice_index += 1
        else:
            self.choice_timer.stop()

    def make_choice(self, index):
        result = self.story_manager.make_choice(index)
        
        # If navigation happened or text was modified, full refresh (re-type text)
        if result.get("navigated") or result.get("text_modified"):
            self.refresh_ui()
        else:
            # Otherwise, just refresh choices (e.g. one-shot removed) without re-typing text
            self.refresh_choices_only()

    def refresh_choices_only(self):
        # 1. Update Choices
        while self.layout_choices.count():
            child = self.layout_choices.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        choices = self.story_manager.get_available_choices()
        if not choices and not self.story_manager.current_node:
             lbl = QLabel("Fin de l'histoire.")
             lbl.setStyleSheet("color: #888; font-style: italic; font-size: 16px;")
             self.layout_choices.addWidget(lbl)
        
        for i, choice in enumerate(choices):
            btn = QPushButton(choice["text"])
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("class", "choice-btn")
            btn.clicked.connect(lambda checked, idx=i: self.make_choice(idx))
            
            # Apply Disabled State
            if choice.get("disabled"):
                btn.setEnabled(False)
            
            # Show immediately (no fade) for instant feedback
            self.layout_choices.addWidget(btn)

        self.layout_choices.addStretch()

        # Dynamic resizing of choices area
        count = len(choices) if choices else 1
        needed_height = count * 65 + 40
        final_height = min(needed_height, 350)
        self.scroll_choices.setFixedHeight(final_height)

    def update_hud(self):
        vars = self.story_manager.variables.get_all()
        # Initial update
        for name, val in vars.items():
            if name in self.stat_labels:
                self.stat_labels[name].setText(str(val))
            elif name == "location_text":
                self.update_location_label()

    def update_location_label(self):
        vars = self.story_manager.variables
        continent = vars.get_var("location_continent")
        city = vars.get_var("location_city")
        name = vars.get_var("location_name")
        full_text = vars.get_var("location_text", "Inconnu")
        
        if continent and city and name:
            html = f"<div style='line-height:120%;'>" \
                   f"<span style='font-size:10pt; color:#888; text-transform:uppercase;'>{continent} - {city}</span><br>" \
                   f"<span style='font-size:13pt; font-weight:bold; color:#b1a270;'>{name}</span></div>"
            self.lbl_location.setText(html)
        else:
            self.lbl_location.setText(full_text)

    def show_quest_offer(self, quest_id):
        """Affiche la fenêtre de proposition de quête."""
        if not self.story_manager.project: return
        
        quest = self.story_manager.project.quests.get(quest_id)
        if not quest: return
        
        dialog = QuestOfferDialog(self, quest, self.story_manager.project)
        if dialog.exec():
            # Accepted
            self.story_manager.variables.start_quest(quest_id)
        
        # Always clear the offer variable after closing dialog
        self.story_manager.variables.hide_quest_offer()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    project_file = None
    if len(sys.argv) > 1:
        project_file = sys.argv[1]

    window = PlayerWindow(project_file)
    window.show()
    sys.exit(app.exec())
