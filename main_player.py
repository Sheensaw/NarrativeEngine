# main_player.py
import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QFileDialog, QMessageBox, QFrame, QScrollArea, QGraphicsOpacityEffect)
from PyQt6.QtGui import QFontDatabase, QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize, QUrl, QTimer, QPropertyAnimation, QEasingCurve

from src.core.models import ProjectModel, ItemModel
from src.core.serializer import ProjectSerializer
from src.engine.story_manager import StoryManager
from src.core.database import DatabaseManager
from src.ui.sliding_menu import SlidingMenu
from src.ui.animated_widgets import FadeTextEdit, HoverButton

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
        self.sliding_menu = SlidingMenu(self, self.story_manager)
        self.sliding_menu.hide()

        # 5. Load Project if provided
        if project_file:
            self.load_project(project_file)
        else:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.open_project_dialog)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep menu on the right side, full height
        if hasattr(self, 'sliding_menu'):
            menu_width = 400
            self.sliding_menu.setGeometry(self.width() - menu_width, 0, menu_width, self.height())

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
            QPushButton.choice-btn:hover { border-left-color: #c42b1c; background-color: #1e1e1e; padding-left: 25px; }
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

        btn_comp = create_hud_btn("Compagnons", "buddy.png", lambda: self.toggle_menu(2))
        top_layout.addWidget(btn_comp)

        main_layout.addWidget(self.top_bar)

        # --- MAIN CONTENT AREA ---
        self.main_area = QWidget()
        self.main_area.setObjectName("MainArea")
        main_layout.addWidget(self.main_area)

        content_layout = QVBoxLayout(self.main_area)
        content_layout.setContentsMargins(150, 50, 150, 50) # Centered reading experience
        content_layout.setSpacing(30)

        # Story Text
        self.txt_story = FadeTextEdit()
        self.txt_story.setObjectName("StoryText")
        self.txt_story.setReadOnly(True)
        self.txt_story.setFrameShape(QFrame.Shape.NoFrame)
        self.txt_story.finished.connect(self.show_choices_sequentially)
        content_layout.addWidget(self.txt_story, 4)

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
        content_layout.addWidget(self.scroll_choices, 2)

    def on_variable_changed(self, name, value):
        """Met à jour l'interface quand une variable change."""
        if name in self.stat_labels:
            self.stat_labels[name].setText(str(value))
        elif name == "max_health":
             pass
        
        # Refresh menu if open
        if hasattr(self, 'sliding_menu') and self.sliding_menu.isVisible():
            self.sliding_menu.refresh_current_view()

    def toggle_menu(self, tab_index):
        if self.sliding_menu.isVisible():
            # If already visible and same tab, hide. If different tab, switch.
            if self.sliding_menu.stack.currentIndex() == tab_index:
                self.sliding_menu.hide_menu()
            else:
                self.sliding_menu.switch_tab(tab_index)
        else:
            self.sliding_menu.show_menu(tab_index)

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
            btn = HoverButton(choice["text"])
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("class", "choice-btn")
            btn.clicked.connect(lambda checked, idx=i: self.make_choice(idx))
            
            # Hide initially
            opacity = QGraphicsOpacityEffect(btn)
            opacity.setOpacity(0.0)
            btn.setGraphicsEffect(opacity)
            btn.setVisible(False) # Also hide to prevent clicks? No, opacity 0 is enough visually, but setVisible False is safer.
            # Actually, if we setVisible(False), layout might collapse. 
            # Better to use Opacity 0 and maybe disable?
            # Let's use Opacity 0 and setEnabled(False)
            btn.setEnabled(False)
            
            self.layout_choices.addWidget(btn)

        self.layout_choices.addStretch()

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
            btn.setEnabled(True)
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
        self.story_manager.make_choice(index)
        self.refresh_ui()

    def update_hud(self):
        vars = self.story_manager.variables.get_all()
        # Initial update
        for name, val in vars.items():
            if name in self.stat_labels:
                self.stat_labels[name].setText(str(val))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    project_file = None
    if len(sys.argv) > 1:
        project_file = sys.argv[1]

    window = PlayerWindow(project_file)
    window.show()
    sys.exit(app.exec())
