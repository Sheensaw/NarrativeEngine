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

    # Données RPG (Variables globales, définitions items/quêtes)
    variables: Dict[str, Any] = field(default_factory=dict)

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
                "edges": [e.to_dict() for e in self.edges]
            },
            "database": {
                "variables": self.variables
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

        # Database
        db_data = data.get("database", {})
        project.variables = db_data.get("variables", {})

        return project
# Modeles de donnees (Dataclasses / Schema JSON)
