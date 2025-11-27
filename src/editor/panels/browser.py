# src/editor/panels/browser.py
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeView, QLabel
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import QDir


class BrowserPanel(QWidget):
    """
    Explorateur de fichiers pour gérer les assets (images, sons).
    """

    def __init__(self, root_path="."):
        super().__init__()
        self.root_path = os.path.abspath(root_path)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Header
        self.lbl_header = QLabel("Explorateur de Projet")
        self.lbl_header.setStyleSheet("padding: 5px; font-weight: bold;")
        self.layout.addWidget(self.lbl_header)

        # Vue Arborescente (Création avant le modèle pour stabilité)
        self.tree = QTreeView()

        # Modèle de fichier système
        # CRITIQUE : Utilisation de QDir pour les filtres et parenté explicite
        self.model = QFileSystemModel()
        self.model.setParent(self)
        self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs)

        # Démarrage du scan
        self.model.setRootPath(self.root_path)

        # Liaison Vue-Modèle
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.root_path))

        # Configuration Vue
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(False)  # Optimisation perf

        self.layout.addWidget(self.tree)