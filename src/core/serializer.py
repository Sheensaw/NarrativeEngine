# src/core/serializer.py
import json
import os
from typing import Optional
from src.core.models import ProjectModel


class ProjectSerializer:
    """
    Classe utilitaire pour charger et sauvegarder les projets.
    Gère les erreurs d'I/O et le formatage JSON.
    """

    @staticmethod
    def save_project(project: ProjectModel, file_path: str) -> bool:
        """
        Sauvegarde le projet entier dans un fichier JSON.
        Retourne True si succès, False sinon.
        """
        try:
            data = project.to_dict()

            # Création des dossiers parents si inexistants
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            print(f"[Serializer] Projet sauvegardé avec succès : {file_path}")
            return True

        except Exception as e:
            print(f"[Serializer] ERREUR lors de la sauvegarde : {e}")
            return False

    @staticmethod
    def load_project(file_path: str) -> Optional[ProjectModel]:
        """
        Charge un projet depuis un fichier JSON.
        Retourne une instance de ProjectModel ou None si échec.
        """
        if not os.path.exists(file_path):
            print(f"[Serializer] Fichier introuvable : {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            project = ProjectModel.from_dict(data)
            print(f"[Serializer] Projet '{project.name}' chargé (version {project.version})")
            return project

        except json.JSONDecodeError as e:
            print(f"[Serializer] ERREUR JSON invalide : {e}")
            return None
        except Exception as e:
            print(f"[Serializer] ERREUR lors du chargement : {e}")
            return None