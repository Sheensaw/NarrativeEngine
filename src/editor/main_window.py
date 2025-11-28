# src/editor/main_window.py
import os
from PyQt6.QtWidgets import (QMainWindow, QDockWidget, QToolBar,
                             QFileDialog, QMessageBox, QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon

from src.core.models import ProjectModel, NodeModel
from src.core.serializer import ProjectSerializer
from src.core.definitions import NodeType
from src.editor.graph.scene import NodeScene
from src.editor.graph.view import NodeGraphView
from src.editor.panels.inspector import InspectorPanel
from src.editor.panels.database_panel import DatabasePanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Narrative RPG Engine - Editor")
        self.setWindowIcon(QIcon("src/assets/icon.ico"))
        self.resize(1600, 900)
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QDockWidget { color: #ccc; font-weight: bold; }
            QDockWidget::title { background: #333; padding: 5px; }
            QToolBar { background: #333; border-bottom: 1px solid #555; spacing: 10px; padding: 5px; }
            QToolBar::separator { background: #555; width: 1px; height: 20px; margin: 5px; }
        """)

        self.project_path = None

        # 1. Initialiser la logique centrale (Scène & Vue)
        self.scene = NodeScene(self)
        self.view = NodeGraphView(self.scene, self)
        self.setCentralWidget(self.view)

        # --- Inspecteur (Droite) ---
        self.inspector = InspectorPanel()
        self.dock_inspector = QDockWidget("Inspecteur", self)
        self.dock_inspector.setWidget(self.inspector)
        self.dock_inspector.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_inspector)

        # --- Database (Gauche - Drawer) ---
        self.database_panel = DatabasePanel()
        self.dock_database = QDockWidget("Base de Données", self)
        self.dock_database.setWidget(self.database_panel)
        self.dock_database.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        # On l'ajoute à gauche mais on le cache par défaut pour l'effet "Drawer"
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_database)
        self.dock_database.hide()

        # 3. Initialiser la Toolbar et Menus
        self._init_actions()

        # 4. Charger un projet vide par défaut ou le dernier projet
        self.new_project()
        self._load_last_project()

        # 5. Connexions Signaux
        self.scene.selectionChanged.connect(self.on_selection_changed)

    def _init_actions(self):
        """Barre d'outils supérieure."""
        print("DEBUG: Init Actions")
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setObjectName("MainToolbar")
        self.addToolBar(toolbar)

        # Actions Fichier
        act_new = QAction("Nouveau", self)
        act_new.triggered.connect(self.new_project)
        toolbar.addAction(act_new)

        act_save = QAction("Sauvegarder", self)
        act_save.triggered.connect(self.save_project)
        toolbar.addAction(act_save)

        act_load = QAction("Charger", self)
        act_load.triggered.connect(self.load_project_dialog)
        toolbar.addAction(act_load)

        toolbar.addSeparator()

        # Actions Édition
        act_add_node = QAction("Ajouter Dialogue", self)
        act_add_node.triggered.connect(self.add_dialogue_node)
        toolbar.addAction(act_add_node)

        toolbar.addSeparator()

        # Actions Affichage (Drawer Toggles)
        act_toggle_db = QAction("Base de Données", self)
        act_toggle_db.setCheckable(True)
        act_toggle_db.setChecked(False)
        act_toggle_db.toggled.connect(self.dock_database.setVisible)
        # Synchroniser l'état si le dock est fermé manuellement
        self.dock_database.visibilityChanged.connect(act_toggle_db.setChecked)
        toolbar.addAction(act_toggle_db)

        act_toggle_insp = QAction("Inspecteur", self)
        act_toggle_insp.setCheckable(True)
        act_toggle_insp.setChecked(True)
        act_toggle_insp.toggled.connect(self.dock_inspector.setVisible)
        self.dock_inspector.visibilityChanged.connect(act_toggle_insp.setChecked)
        toolbar.addAction(act_toggle_insp)

        toolbar.addSeparator()

        # Actions Jeu
        act_play = QAction("▶ Jouer", self)
        act_play.triggered.connect(self.run_game)
        toolbar.addAction(act_play)

    def _ensure_default_variables(self, project: ProjectModel):
        """Injecte les variables par défaut si elles manquent."""
        defaults = {
            "health": 100,
            "max_health": 100,
            "strength": 10,
            "dexterity": 10,
            "resistance": 0,
            "gold": 0,
            "inventory": {},
            "equipped": {},
            "companions": []
        }
        for key, val in defaults.items():
            if key not in project.variables:
                project.variables[key] = val

    def on_selection_changed(self):
        """Transmet la sélection de la scène à l'inspecteur."""
        selected = self.scene.selectedItems()
        self.inspector.set_selection(selected)

    def run_game(self):
        """Lance le joueur avec le projet actuel."""
        # 1. Sauvegarder d'abord
        self.save_project()
        if not self.project_path:
            return

        # 2. Lancer le processus joueur
        import subprocess
        import sys
        
        # On utilise l'interpréteur Python actuel
        python_exe = sys.executable
        player_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "main_player.py")
        
        try:
            subprocess.Popen([python_exe, player_script, self.project_path])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lancer le jeu :\n{e}")

    # --- Gestion Projet ---

    def new_project(self):
        """Crée un projet vierge."""
        project = ProjectModel()
        
        # Initialiser les variables par défaut (Stats RPG)
        project.variables = {
            "health": 100,
            "max_health": 100,
            "strength": 10,
            "dexterity": 10,
            "resistance": 0,
            "gold": 0,
            "inventory": {},
            "equipped": {},
            "companions": []
        }

        # Ajouter un nœud de départ par défaut
        start_node = NodeModel(type=NodeType.START, title="Début", pos_x=0, pos_y=0)
        project.add_node(start_node)

        self.scene.set_project(project)
        self.inspector.set_project(project)
        self.database_panel.set_project(project)
        self.project_path = None

    def save_project(self):
        """Sauvegarde rapide."""
        if not self.scene.project:
            return

        if not self.project_path:
            path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder Projet", "", "JSON Files (*.json)")
            if not path:
                return
            self.project_path = path

        success = ProjectSerializer.save_project(self.scene.project, self.project_path)
        if success:
            self._save_last_project()
            self.statusBar().showMessage(f"Sauvegardé : {self.project_path}", 3000)

    def load_project_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Charger Projet", "", "JSON Files (*.json)")
        if path:
            project = ProjectSerializer.load_project(path)
            if project:
                self._ensure_default_variables(project)
                self.scene.set_project(project)
                self.inspector.set_project(project)
                self.database_panel.set_project(project)
                self.project_path = path
                self._save_last_project()
                self.statusBar().showMessage(f"Chargé : {path}", 3000)

    def add_dialogue_node(self):
        """Ajoute un nœud au centre de la vue."""
        if not self.scene.project:
            return

        # Ajout avec un léger décalage aléatoire ou centré
        import random
        # On essaie de centrer sur la vue
        center = self.view.mapToScene(self.view.viewport().rect().center())
        
        new_node = NodeModel(
            title="Nouveau Dialogue",
            type=NodeType.DIALOGUE,
            pos_x=center.x() + random.randint(-20, 20),
            pos_y=center.y() + random.randint(-20, 20)
        )
        self.scene.project.add_node(new_node)
        self.scene.add_node_item(new_node)

    def _save_last_project(self):
        """Sauvegarde le chemin du dernier projet ouvert dans un fichier de config."""
        if not self.project_path:
            return
        
        import json
        config_path = "editor_config.json"
        try:
            with open(config_path, "w") as f:
                json.dump({"last_project": self.project_path}, f)
        except Exception as e:
            print(f"Erreur sauvegarde config: {e}")

    def _load_last_project(self):
        """Charge le dernier projet ouvert si disponible."""
        import json
        config_path = "editor_config.json"
        if not os.path.exists(config_path):
            return

        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                last_path = config.get("last_project")
                
                if last_path and os.path.exists(last_path):
                    project = ProjectSerializer.load_project(last_path)
                    if project:
                        self._ensure_default_variables(project)
                        self.scene.set_project(project)
                        self.inspector.set_project(project)
                        self.database_panel.set_project(project)
                        self.project_path = last_path
                        self.statusBar().showMessage(f"Projet restauré : {last_path}", 5000)
        except Exception as e:
            print(f"Erreur chargement config: {e}")