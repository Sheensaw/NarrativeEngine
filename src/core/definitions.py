# src/core/definitions.py
from enum import Enum


class NodeType(str, Enum):
    """
    Définit les types de nœuds disponibles dans le moteur.
    Utilisé pour la sérialisation et le rendu graphique.
    """
    DIALOGUE = "dialogue"  # Nœud standard : Texte + Choix
    CHOICE = "choice"  # (Optionnel) Nœud de branchement pur
    EVENT = "event"  # Nœud sans UI, change des variables
    CONDITION = "condition"  # Nœud logique (If/Else) pour diriger le flux
    START = "start"  # Point d'entrée du graphe
    END = "end"  # Fin de la partie


class SocketType(int, Enum):
    """
    Définit le type de port de connexion.
    """
    INPUT = 1  # Entrée (gauche du nœud)
    OUTPUT = 2  # Sortie (droite du nœud)


# --- CONSTANTES DE CONFIGURATION ---

# Taille par défaut des nœuds
NODE_WIDTH = 240
NODE_HEIGHT = 160

# Couleurs de l'interface (Format Hex)
COLORS = {
    # Couleurs des nœuds par type
    NodeType.DIALOGUE: "#3498db",  # Bleu
    NodeType.EVENT: "#e74c3c",  # Rouge
    NodeType.CONDITION: "#f1c40f",  # Jaune
    NodeType.START: "#2ecc71",  # Vert
    NodeType.END: "#95a5a6",  # Gris

    # Éléments graphiques
    "node_bg": "#2b2b2b",
    "node_border_selected": "#ffffff",
    "node_border_default": "#1e1e1e",
    "socket": "#ecf0f1",
    "connection": "#bdc3c7",
    "connection_active": "#f39c12",
    "grid_bg": "#212121",
    "grid_lines_light": "#2f2f2f",
    "grid_lines_dark": "#1a1a1a",
}

# Clés utilisées dans les dictionnaires de données (pour éviter les "magic strings")
KEY_ID = "id"
KEY_TYPE = "type"
KEY_TITLE = "title"
KEY_CONTENT = "content"
KEY_LOGIC = "logic"
KEY_POS_X = "pos_x"
KEY_POS_Y = "pos_y"
KEY_INPUTS = "inputs"
KEY_OUTPUTS = "outputs"