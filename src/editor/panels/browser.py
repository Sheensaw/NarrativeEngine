# src/editor/panels/browser.py
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeView, QFileSystemModel, QLabel


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

        # Modèle de fichier système
        self.model = QFileSystemModel()
        self.model.setRootPath(self.root_path)

        # Vue Arborescente
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.root_path))

        # Masquer les colonnes inutiles (Taille, Type, Date)
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.setHeaderHidden(True)

        self.layout.addWidget(self.tree)