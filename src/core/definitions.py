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


# --- MACRO DEFINITIONS (SugarCube-like) ---
MACRO_DEFINITIONS = {
    "set": {
        "label": "Set Variable",
        "args": [
            {"name": "name", "type": "string", "label": "Variable Name ($var)"},
            {"name": "value", "type": "string", "label": "Value (Expression)"},
        ]
    },
    "unset": {
        "label": "Unset Variable",
        "args": [
            {"name": "name", "type": "string", "label": "Variable Name ($var)"},
        ]
    },
    "run": {
        "label": "Run Script",
        "args": [
            {"name": "script", "type": "text", "label": "JavaScript/Code"},
        ]
    },
    "print": {
        "label": "Print Text",
        "args": [
            {"name": "text", "type": "string", "label": "Text to Print"},
        ]
    },
    "audio": {
        "label": "Play Audio",
        "args": [
            {"name": "track", "type": "string", "label": "Track Name"},
            {"name": "action", "type": "select", "label": "Action", "options": ["play", "stop", "pause", "fadein", "fadeout"]},
        ]
    },
    "goto": {
        "label": "Go To Passage",
        "args": [
            {"name": "target", "type": "node_select", "label": "Passage Name"},
        ]
    },
    "button": {
        "label": "Button",
        "args": [
            {"name": "text", "type": "string", "label": "Button Text"},
            {"name": "target", "type": "node_select", "label": "Target Passage (Optional)"},
        ]
    },
    "addItem": {
        "label": "Add Item (Inventory)",
        "args": [
            {"name": "item_id", "type": "item_select", "label": "Item"},
            {"name": "qty", "type": "int", "label": "Quantity", "default": 1},
        ]
    },
    "removeItem": {
        "label": "Remove Item (Inventory)",
        "args": [
            {"name": "item_id", "type": "item_select", "label": "Item"},
            {"name": "qty", "type": "int", "label": "Quantity", "default": 1},
        ]
    },
    "startQuest": {
        "label": "Start Quest",
        "args": [
            {"name": "quest_id", "type": "quest_select", "label": "Quest"},
            {"name": "loot", "type": "string", "label": "Loot (Optional)"},
        ]
    },
    "completeQuest": {
        "label": "Complete Quest",
        "args": [
            {"name": "quest_id", "type": "quest_select", "label": "Quest"},
        ]
    },
    "spawn": {
        "label": "Spawn NPC",
        "args": [
            {"name": "id", "type": "string", "label": "NPC ID"},
            {"name": "target", "type": "node_select", "label": "Passage/Location"},
            {"name": "x", "type": "int", "label": "X Coord (Optional)", "default": 0},
            {"name": "y", "type": "int", "label": "Y Coord (Optional)", "default": 0},
        ]
    },
    "movePnj": {
        "label": "Move NPC",
        "args": [
            {"name": "id", "type": "string", "label": "NPC ID"},
            {"name": "target", "type": "node_select", "label": "Target Passage"},
            {"name": "x", "type": "int", "label": "X Coord (Optional)", "default": 0},
            {"name": "y", "type": "int", "label": "Y Coord (Optional)", "default": 0},
        ]
    },
    "pnj": {
        "label": "Define NPC",
        "args": [
            {"name": "id", "type": "string", "label": "NPC ID"},
            {"name": "name", "type": "string", "label": "Display Name"},
            {"name": "type", "type": "string", "label": "Type (guard, merchant...)"},
        ]
    },
    "pnjfollow": {
        "label": "NPC Follow",
        "args": [
            {"name": "id", "type": "string", "label": "NPC ID"},
            {"name": "target_id", "type": "string", "label": "Target ID (player/npc)"},
        ]
    },
    "setrelation": {
        "label": "Set Relation",
        "args": [
            {"name": "id", "type": "string", "label": "NPC ID"},
            {"name": "value", "type": "int", "label": "Value (0-100)"},
        ]
    },
    "changerelation": {
        "label": "Change Relation",
        "args": [
            {"name": "id", "type": "string", "label": "NPC ID"},
            {"name": "amount", "type": "int", "label": "Amount (+/-)"},
        ]
    },
    "setloyalty": {
        "label": "Set Loyalty",
        "args": [
            {"name": "id", "type": "string", "label": "NPC ID"},
            {"name": "value", "type": "int", "label": "Value (0-100)"},
        ]
    },
    "changeloyalty": {
        "label": "Change Loyalty",
        "args": [
            {"name": "id", "type": "string", "label": "NPC ID"},
            {"name": "amount", "type": "int", "label": "Amount (+/-)"},
        ]
    },
    "setmood": {
        "label": "Set Mood",
        "args": [
            {"name": "id", "type": "string", "label": "NPC ID"},
            {"name": "mood", "type": "string", "label": "Mood (happy, angry...)"},
        ]
    },
}