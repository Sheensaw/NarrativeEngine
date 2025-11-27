# main_editor.py
import sys
import os

# Ajout du dossier courant au path pour que les imports 'src.*' fonctionnent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from src.editor.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Chargement du thème sombre
    try:
        with open("src/assets/styles/dark_theme.qss", "r") as f:
            qss = f.read()
            app.setStyleSheet(qss)
    except FileNotFoundError:
        print("Attention : Fichier de style 'dark_theme.qss' introuvable.")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()