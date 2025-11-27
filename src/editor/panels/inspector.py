# src/editor/panels/inspector.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QLabel, QGroupBox)
from PyQt6.QtCore import Qt

from src.editor.graph.node_item import NodeItem


class InspectorPanel(QWidget):
    """
    Panneau latéral affichant les propriétés de l'objet sélectionné.
    Permet d'éditer le titre et le contenu (texte) d'un nœud.
    """

    def __init__(self):
        super().__init__()
        self.current_node_item = None

        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Titre du panneau
        self.lbl_header = QLabel("Propriétés")
        self.lbl_header.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        self.layout.addWidget(self.lbl_header)

        # Formulaire
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)

        # Champs
        self.txt_title = QLineEdit()
        self.txt_title.textChanged.connect(self.on_title_changed)

        self.txt_content = QTextEdit()
        self.txt_content.setPlaceholderText("Écrivez le dialogue ici...")
        self.txt_content.textChanged.connect(self.on_content_changed)

        self.form_layout.addRow("Titre :", self.txt_title)
        self.form_layout.addRow("Contenu :", self.txt_content)

        self.layout.addWidget(self.form_widget)
        self.layout.addStretch()  # Pousse le contenu vers le haut

        # État initial : caché tant que rien n'est sélectionné
        self.form_widget.setVisible(False)

    def set_selection(self, selected_items):
        """Appelé quand la sélection change dans la scène."""
        # On ne gère que la sélection d'un seul nœud pour l'instant
        node_items = [i for i in selected_items if isinstance(i, NodeItem)]

        if not node_items:
            self.current_node_item = None
            self.form_widget.setVisible(False)
            return

        self.current_node_item = node_items[0]
        self._load_data_from_node()
        self.form_widget.setVisible(True)

    def _load_data_from_node(self):
        """Remplit les champs avec les données du modèle."""
        if not self.current_node_item:
            return

        model = self.current_node_item.model

        # On bloque les signaux pour éviter de déclencher on_changed pendant le chargement
        self.txt_title.blockSignals(True)
        self.txt_content.blockSignals(True)

        self.txt_title.setText(model.title)
        self.txt_content.setText(model.content.get("text", ""))

        self.txt_title.blockSignals(False)
        self.txt_content.blockSignals(False)

    def on_title_changed(self, text):
        """Sauvegarde le titre dans le modèle et met à jour le graph."""
        if self.current_node_item:
            self.current_node_item.model.title = text
            # Mettre à jour visuellement le titre sur le nœud
            self.current_node_item._title_item.setPlainText(text)

    def on_content_changed(self):
        """Sauvegarde le texte narratif."""
        if self.current_node_item:
            text = self.txt_content.toPlainText()
            self.current_node_item.model.content["text"] = text