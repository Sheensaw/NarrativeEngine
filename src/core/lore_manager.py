import json
import os
import math

print(f"DEBUG: Loading LoreManager from {__file__}")

class LoreManager:
    def __init__(self, lore_directory):
        self.lore_directory = lore_directory
        self.locations = []
        self.load_lore()

    def load_lore(self):
        self.locations = []
        if not os.path.exists(self.lore_directory):
            print(f"Warning: Lore directory not found: {self.lore_directory}")
            return

        # 1. Load Macro (Velkarum)
        velkarum_path = os.path.join(self.lore_directory, "velkarum.json")
        if os.path.exists(velkarum_path):
            self._load_file(velkarum_path, scale="macro")

        # 2. Load Micro (Regional)
        for filename in os.listdir(self.lore_directory):
            if filename.endswith(".json") and filename != "velkarum.json":
                filepath = os.path.join(self.lore_directory, filename)
                self._load_file(filepath, scale="micro")

    def _load_file(self, filepath, scale):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "nodes" in data:
                    for key, node in data["nodes"].items():
                        # Ensure required fields
                        if "x" in node and "y" in node and "continent" in node:
                            self.locations.append({
                                "id": key,
                                "name": node.get("name", key),
                                "x": float(node["x"]),
                                "y": float(node["y"]),
                                "continent": node["continent"],
                                "city": node.get("city") or "",
                                "place": node.get("place") or "",
                                "type": node.get("type", "Unknown"),
                                "scale": scale,
                                "main_location_name": node.get("main_location_name")
                            })
        except Exception as e:
            print(f"Error loading {filepath}: {e}")

    def get_location_at(self, x, y, continent, tolerance=0.1):
        """
        Trouve le lieu le plus proche aux coordonnées données.
        Priorise les lieux 'micro' sur les 'macro'.
        """
        candidates = []
        for loc in self.locations:
            if loc["continent"] == continent:
                dist = math.sqrt((loc["x"] - x)**2 + (loc["y"] - y)**2)
                if dist <= tolerance:
                    candidates.append((dist, loc))
        
        if not candidates:
            return None
            
        # Sort by distance first
        candidates.sort(key=lambda x: x[0])
        
        # Filter for best match logic
        # If we have very close matches (e.g. exact overlap), prefer Micro
        best_dist = candidates[0][0]
        close_matches = [c for c in candidates if abs(c[0] - best_dist) < 0.001]
        
        # Check if any is micro
        micro_match = next((c for c in close_matches if c[1]["scale"] == "micro"), None)
        
        if micro_match:
            return micro_match[1]
            
        return candidates[0][1]

    def get_continents(self):
        return sorted(list(set(loc["continent"] for loc in self.locations if loc.get("continent"))))

    def get_location_types(self):
        """Returns a sorted list of unique location types."""
        return sorted(list(set(loc.get("type", "Unknown") for loc in self.locations)))

    def get_locations(self, continent=None, type_filter=None):
        """Returns a list of locations filtered by continent and type."""
        filtered = self.locations
        
        if continent:
            filtered = [loc for loc in filtered if loc.get("continent") == continent]
            
        if type_filter:
            filtered = [loc for loc in filtered if loc.get("type") == type_filter]
            
        # Sort by City then Place for better readability
        filtered.sort(key=lambda x: (x.get("city") or "", x.get("place") or x.get("name") or ""))
        return filtered


