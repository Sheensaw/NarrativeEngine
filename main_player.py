import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QListWidget, QGroupBox, QFileDialog, QMessageBox, QFrame, QScrollArea, QDialog)
from PyQt6.QtGui import QFontDatabase, QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize

from src.core.models import ProjectModel
from src.core.serializer import ProjectSerializer
from src.engine.story_manager import StoryManager

class PlayerWindow(QMainWindow):
    def __init__(self, project_path=None):
        super().__init__()
        self.setWindowTitle("Narrative Engine - Player")
        self.resize(1280, 800)

        # Load Stylesheet
        self._load_stylesheet()

        # Load Font
        self._load_font()

        self.story_manager = StoryManager()
        self.story_manager.variables.add_observer(self.on_variable_changed)

        self._init_ui()

        if project_path:
            self.load_project(project_path)
        else:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.open_project_dialog)

    def _load_stylesheet(self):
        try:
            style_path = os.path.join(os.path.dirname(__file__), "src", "assets", "styles", "player_theme.qss")
            if os.path.exists(style_path):
                with open(style_path, "r") as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Erreur chargement style: {e}")

    def _load_font(self):
        try:
            font_path = os.path.join(os.path.dirname(__file__), "src", "assets", "fonts", "Underdog.ttf")
            if os.path.exists(font_path):
                id = QFontDatabase.addApplicationFont(font_path)
                if id < 0:
                    print("Erreur chargement font Underdog")
                else:
                    print("Font Underdog chargée")
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
        self.top_bar.setFixedHeight(70)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(15)

        # Assets Path
        assets_dir = os.path.join(os.path.dirname(__file__), "src", "assets", "icons")

        # Helper to create stat labels with icons
        def add_stat(icon_name, name, obj_name):
            # Icon
            lbl_icon = QLabel()
            icon_path = os.path.join(assets_dir, icon_name)
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                lbl_icon.setPixmap(pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                lbl_icon.setText(name[:1]) # Fallback text
            
            lbl_icon.setProperty("class", "stat-label")
            
            # Value
            lbl_val = QLabel("0")
            lbl_val.setProperty("class", "stat-value")
            lbl_val.setObjectName(obj_name)
            
            top_layout.addWidget(lbl_icon)
            top_layout.addWidget(lbl_val)
            return lbl_val

        # Using defense.png as placeholder for strength/resistance if needed
        self.lbl_health = add_stat("health.png", "Health", "StatHealth")
        self.lbl_str = add_stat("defense.png", "Strength", "StatStrength") # Placeholder
        self.lbl_dex = add_stat("dexterity.png", "Dexterity", "StatDexterity")
        self.lbl_res = add_stat("defense.png", "Resistance", "StatResistance")
        self.lbl_gold = add_stat("gold.png", "Gold", "StatGold")

        top_layout.addStretch()

        # Helper for Menu Buttons with Icons
        def add_menu_btn(text, icon_name, callback):
            btn = QPushButton(text)
            btn.setProperty("class", "menu-btn")
            icon_path = os.path.join(assets_dir, icon_name)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(20, 20))
            btn.clicked.connect(callback)
            top_layout.addWidget(btn)

        add_menu_btn("Inventaire", "inventory.png", self.open_inventory)
        add_menu_btn("Équipement", "equipment.png", self.open_equipment)
        add_menu_btn("Compagnons", "buddy.png", self.open_companions)

        main_layout.addWidget(self.top_bar)

        # --- MAIN CONTENT AREA ---
        self.main_area = QWidget()
        content_layout = QVBoxLayout(self.main_area)
        content_layout.setContentsMargins(150, 50, 150, 50) # Centered reading experience
        content_layout.setSpacing(30)

        # Story Text
        self.txt_story = QTextEdit()
        self.txt_story.setObjectName("StoryText")
        self.txt_story.setReadOnly(True)
        self.txt_story.setFrameShape(QFrame.Shape.NoFrame)
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

        main_layout.addWidget(self.main_area)

    def open_inventory(self):
        # Retrieve inventory from variables
        inv = self.story_manager.variables.get_var("inventory", {})
        
        # Create display dict
        display_inv = {}
        for item_id, qty in inv.items():
            name = item_id
            if self.story_manager.project and item_id in self.story_manager.project.items:
                name = self.story_manager.project.items[item_id].name
            display_inv[name] = qty

        dialog = InventoryDialog(self, display_inv)
        dialog.exec()

    def open_equipment(self):
        equipped = self.story_manager.variables.get_var("equipped", {})
        dialog = EquipmentDialog(self, equipped)
        dialog.exec()

    def open_companions(self):
        companions = self.story_manager.variables.get_var("companions", [])
        dialog = CompanionsDialog(self, companions)
        dialog.exec()

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

        self.story_manager.load_project(project)
        self.story_manager.start_game()
        self.refresh_ui()

    def refresh_ui(self):
        # 1. Update Text
        text = self.story_manager.get_parsed_text()
        self.txt_story.setMarkdown(text)

        # 2. Update Choices
        # Clear previous buttons
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
            self.layout_choices.addWidget(btn)

        self.layout_choices.addStretch()

    def make_choice(self, index):
        self.story_manager.make_choice(index)
        self.refresh_ui()

    def on_variable_changed(self, name, value):
        self.update_hud()

    def update_hud(self):
        vars = self.story_manager.variables.get_all()
        
        # Update Stats
        self.lbl_health.setText(f"{vars.get('health', 0)}/{vars.get('max_health', 10)}")
        self.lbl_str.setText(str(vars.get('strength', 0)))
        self.lbl_dex.setText(str(vars.get('dexterity', 0)))
        self.lbl_res.setText(str(vars.get('resistance', 0)))
        self.lbl_gold.setText(str(vars.get('gold', 0)))


class InventoryDialog(QDialog):
    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.setWindowTitle("Inventaire")
        self.resize(400, 500)
        self.layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)
        
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        self.layout.addWidget(btn_close)
        
        self.load_items(items or {})

    def load_items(self, items):
        self.list_widget.clear()
        if not items:
            self.list_widget.addItem("Inventaire vide.")
            return

        for item_name, qty in items.items():
            self.list_widget.addItem(f"{item_name} (x{qty})")


class EquipmentDialog(QDialog):
    def __init__(self, parent=None, equipped=None):
        super().__init__(parent)
        self.setWindowTitle("Équipement")
        self.resize(400, 500)
        layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        if equipped:
            for slot, item in equipped.items():
                self.list_widget.addItem(f"{slot}: {item}")
        else:
            self.list_widget.addItem("Aucun équipement.")
            
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class CompanionsDialog(QDialog):
    def __init__(self, parent=None, companions=None):
        super().__init__(parent)
        self.setWindowTitle("Compagnons")
        self.resize(400, 500)
        layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        if companions:
            for npc in companions:
                self.list_widget.addItem(f"👤 {npc}")
        else:
            self.list_widget.addItem("Aucun compagnon.")
            
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Check args for project path
    project_file = None
    if len(sys.argv) > 1:
        project_file = sys.argv[1]

    window = PlayerWindow(project_file)
    window.show()
    sys.exit(app.exec())
