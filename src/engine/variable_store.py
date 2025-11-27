# src/engine/variable_store.py
from typing import Any, Dict, Callable, List


class VariableStore:
    """
    Gère l'état global du jeu (variables, inventaire, quêtes).
    Implémente le pattern Observer pour notifier l'UI des changements.
    """

    def __init__(self):
        # Stockage principal des variables {nom: valeur}
        self._variables: Dict[str, Any] = {}

        # Liste des fonctions à appeler quand une variable change
        # Signature: callback(var_name: str, new_value: Any)
        self._observers: List[Callable[[str, Any], None]] = []

    def load_state(self, variables: Dict[str, Any]):
        """Charge un état complet (ex: chargement de sauvegarde ou init projet)."""
        self._variables = variables.copy()
        # On notifie tout le monde du rechargement complet
        self.notify_all()

    def get_all(self) -> Dict[str, Any]:
        """Retourne une copie de toutes les variables."""
        return self._variables.copy()

    def set_var(self, name: str, value: Any):
        """Définit ou met à jour une variable."""
        old_val = self._variables.get(name)
        if old_val != value:
            self._variables[name] = value
            self.notify(name, value)

    def get_var(self, name: str, default: Any = None) -> Any:
        """Récupère la valeur d'une variable."""
        return self._variables.get(name, default)

    def add_observer(self, callback: Callable[[str, Any], None]):
        """Abonne une fonction aux changements de variables."""
        if callback not in self._observers:
            self._observers.append(callback)

    def notify(self, name: str, value: Any):
        """Avertit les observateurs d'un changement spécifique."""
        for callback in self._observers:
            try:
                callback(name, value)
            except Exception as e:
                print(f"[VariableStore] Erreur dans un observer : {e}")

    def notify_all(self):
        """Force la notification de toutes les variables."""
        for name, value in self._variables.items():
            self.notify(name, value)