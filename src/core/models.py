# src/core/models.py
import uuid
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from src.core.definitions import NodeType, KEY_POS_X, KEY_POS_Y


def generate_id() -> str:
    """Génère un identifiant unique (UUID4)."""
    return str(uuid.uuid4())


@dataclass
class NodeModel:
    """
    Représente les données pures d'un nœud (sans l'aspect graphique).
    """
    id: str = field(default_factory=generate_id)
    type: NodeType = NodeType.DIALOGUE
    title: str = "Nouveau Nœud"
    pos_x: float = 0.0
    pos_y: float = 0.0

    # Contenu narratif (Texte, Image, Audio)
    content: Dict[str, Any] = field(default_factory=lambda: {"text": "", "image": None})

    # Logique (Scripts on_enter, on_exit)
    logic: Dict[str, Any] = field(default_factory=lambda: {"on_enter": [], "on_exit": []})

    # Propriétés spécifiques (Conditions, tags)
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le modèle en dictionnaire JSON-friendly."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'NodeModel':
        """Reconstruit un modèle depuis un dictionnaire."""
        # On extrait les positions qui sont souvent stockées à part dans les éditeurs
        # Mais ici nous les gardons dans le modèle pour simplifier.
        node = NodeModel(
            id=data.get("id", generate_id()),
            type=NodeType(data.get("type", NodeType.DIALOGUE)),
            title=data.get("title", "Sans titre"),
            pos_x=float(data.get("pos_x", 0.0)),
            pos_y=float(data.get("pos_y", 0.0)),
            content=data.get("content", {"text": "", "image": None}),
            logic=data.get("logic", {"on_enter": [], "on_exit": []}),
            properties=data.get("properties", {})
        )
        return node


@dataclass
class EdgeModel:
    """
    Représente une connexion entre deux nœuds.
    """
    start_node_id: str
    end_node_id: str
    start_socket_index: int = 0  # Quel choix (sortie) est utilisé ?
    end_socket_index: int = 0  # Généralement 0 (Entrée unique)
    id: str = field(default_factory=generate_id)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'EdgeModel':
        return EdgeModel(
            id=data.get("id", generate_id()),
            start_node_id=data["start_node_id"],
            end_node_id=data["end_node_id"],
            start_socket_index=data.get("start_socket_index", 0),
            end_socket_index=data.get("end_socket_index", 0)
        )


@dataclass
class ItemModel:
    """
    Représente un objet (Item) dans le jeu.
    """
    id: str = field(default_factory=generate_id)
    name: str = "Nouvel Objet"
    type: str = "misc"  # weapon, armor, potion, quest, misc
    description: str = ""
    icon: str = "misc"  # Clé d'icône (ex: 'sword', 'potion')
    stackable: bool = True
    bonuses: Dict[str, float] = field(default_factory=dict)  # ex: {"strength": 5}
    properties: Dict[str, Any] = field(default_factory=dict)  # Custom props

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ItemModel':
        return ItemModel(
            id=data.get("id", generate_id()),
            name=data.get("name", "Nouvel Objet"),
            type=data.get("type", "misc"),
            description=data.get("description", ""),
            icon=data.get("icon", "misc"),
            stackable=data.get("stackable", True),
            bonuses=data.get("bonuses", {}),
            properties=data.get("properties", {})
        )


@dataclass
class QuestModel:
    """
    Représente une quête.
    """
    id: str = field(default_factory=generate_id)
    title: str = "Nouvelle Quête"
    description: str = ""
    steps: List[str] = field(default_factory=list)  # Liste d'objectifs textuels
    rewards: Dict[str, Any] = field(default_factory=lambda: {"gold": 0, "items": []})
    is_main_quest: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'QuestModel':
        return QuestModel(
            id=data.get("id", generate_id()),
            title=data.get("title", "Nouvelle Quête"),
            description=data.get("description", ""),
            steps=data.get("steps", []),
            rewards=data.get("rewards", {"gold": 0, "items": []}),
            is_main_quest=data.get("is_main_quest", False)
        )


@dataclass
class GroupModel:
    """
    Représente un groupe visuel de nœuds (ex: une zone géographique).
    """
    id: str = field(default_factory=generate_id)
    title: str = "Nouveau Groupe"
    pos_x: float = 0.0
    pos_y: float = 0.0
    width: float = 300.0
    height: float = 300.0
    color: str = "#333333" # Hex color
    
    # Propriétés partagées par les nœuds du groupe (ex: continent, city)
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'GroupModel':
        return GroupModel(
            id=data.get("id", generate_id()),
            title=data.get("title", "Nouveau Groupe"),
            pos_x=float(data.get("pos_x", 0.0)),
            pos_y=float(data.get("pos_y", 0.0)),
            width=float(data.get("width", 300.0)),
            height=float(data.get("height", 300.0)),
            color=data.get("color", "#333333"),
            properties=data.get("properties", {})
        )


@dataclass
class LocationModel:
    """
    Représente un lieu (Location) dans le jeu.
    """
    id: str = field(default_factory=generate_id)
    place: str = "Nouveau Lieu"
    city: str = ""
    coords: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    type: str = "Autre"
    continent: str = "Eldaron"
    source_file: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'LocationModel':
        return LocationModel(
            id=data.get("id", generate_id()),
            place=data.get("place", "Nouveau Lieu"),
            city=data.get("city", ""),
            coords=data.get("coords", {"x": 0.0, "y": 0.0}),
            type=data.get("type", "Autre"),
            continent=data.get("continent", "Eldaron"),
            source_file=data.get("source_file", ""),
            properties=data.get("properties", {})
        )


@dataclass
class ProjectModel:
    """
    Le conteneur racine de tout le projet.
    """
    name: str = "Projet RPG Narratif"
    version: str = "1.0.0"
    author: str = "Auteur Anonyme"
    created_at: float = field(default_factory=time.time)
    last_modified: float = field(default_factory=time.time)

    # Données du graphe
    nodes: Dict[str, NodeModel] = field(default_factory=dict)
    edges: List[EdgeModel] = field(default_factory=list)
    groups: Dict[str, GroupModel] = field(default_factory=dict)

    # Données RPG (Variables globales, définitions items/quêtes/lieux)
    variables: Dict[str, Any] = field(default_factory=dict)
    items: Dict[str, ItemModel] = field(default_factory=dict)
    quests: Dict[str, QuestModel] = field(default_factory=dict)
    locations: Dict[str, LocationModel] = field(default_factory=dict)

    def add_node(self, node: NodeModel):
        self.nodes[node.id] = node
        self.last_modified = time.time()

    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]
            # Supprimer aussi les liens associés
            self.edges = [
                e for e in self.edges
                if e.start_node_id != node_id and e.end_node_id != node_id
            ]
            self.last_modified = time.time()

    def add_edge(self, edge: EdgeModel):
        self.edges.append(edge)
        self.last_modified = time.time()

    def add_group(self, group: GroupModel):
        self.groups[group.id] = group
        self.last_modified = time.time()

    def remove_group(self, group_id: str):
        if group_id in self.groups:
            del self.groups[group_id]
            self.last_modified = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "name": self.name,
                "version": self.version,
                "author": self.author,
                "created_at": self.created_at,
                "last_modified": self.last_modified
            },
            "graph": {
                "nodes": [n.to_dict() for n in self.nodes.values()],
                "edges": [e.to_dict() for e in self.edges],
                "groups": [g.to_dict() for g in self.groups.values()]
            },
            "database": {
                "variables": self.variables,
                "items": [i.to_dict() for i in self.items.values()],
                "quests": [q.to_dict() for q in self.quests.values()],
                "locations": [l.to_dict() for l in self.locations.values()]
            }
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ProjectModel':
        project = ProjectModel()

        # Metadata
        meta = data.get("metadata", {})
        project.name = meta.get("name", "Projet RPG")
        project.version = meta.get("version", "1.0.0")
        project.author = meta.get("author", "Auteur")
        project.created_at = meta.get("created_at", time.time())
        project.last_modified = meta.get("last_modified", time.time())

        # Graph Data
        graph_data = data.get("graph", {})

        # Reconstitution des nœuds
        for node_dict in graph_data.get("nodes", []):
            node = NodeModel.from_dict(node_dict)
            project.nodes[node.id] = node

        # Reconstitution des liens
        for edge_dict in graph_data.get("edges", []):
            edge = EdgeModel.from_dict(edge_dict)
            project.edges.append(edge)

        # Reconstitution des groupes
        for group_dict in graph_data.get("groups", []):
            group = GroupModel.from_dict(group_dict)
            project.groups[group.id] = group

        # Database
        db_data = data.get("database", {})
        project.variables = db_data.get("variables", {})
        
        for item_dict in db_data.get("items", []):
            item = ItemModel.from_dict(item_dict)
            project.items[item.id] = item
            
        for quest_dict in db_data.get("quests", []):
            quest = QuestModel.from_dict(quest_dict)
            project.quests[quest.id] = quest
            
        for loc_dict in db_data.get("locations", []):
            loc = LocationModel.from_dict(loc_dict)
            project.locations[loc.id] = loc

        return project
