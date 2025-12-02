from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QDoubleSpinBox, QPushButton, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from src.core.database import DatabaseManager

class LocationDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, initial_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Définir le Lieu")
        self.resize(500, 250)
        self.db_manager = db_manager
        
        # Data
        initial_data = initial_data or {}
        self.continent = initial_data.get("continent", "")
        self.pos_x = initial_data.get("x", 0.0)
        self.pos_y = initial_data.get("y", 0.0)
        
        # Internal state
        self.locations_cache = []
        
        self.init_ui()
        self.load_data()
        self.set_initial_state()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        # Continent
        self.combo_continent = QComboBox()
        self.combo_continent.currentTextChanged.connect(self.on_continent_changed)
        form_layout.addRow("Continent :", self.combo_continent)
        
        # Location Selection (Grouped by Type)
        self.combo_location = QComboBox()
        self.combo_location.currentIndexChanged.connect(self.on_location_selected)
        form_layout.addRow("Lieu :", self.combo_location)
        
        # Coordinates (Read Only)
        coord_layout = QHBoxLayout()
        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-10000, 10000)
        self.spin_x.setDecimals(2)
        self.spin_x.setPrefix("X: ")
        self.spin_x.setReadOnly(True)
        self.spin_x.setStyleSheet("background-color: #f0f0f0; color: black;")
        
        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-10000, 10000)
        self.spin_y.setDecimals(2)
        self.spin_y.setPrefix("Y: ")
        self.spin_y.setReadOnly(True)
        self.spin_y.setStyleSheet("background-color: #f0f0f0; color: black;")
        
        coord_layout.addWidget(self.spin_x)
        coord_layout.addWidget(self.spin_y)
        form_layout.addRow("Coordonnées :", coord_layout)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_ok = QPushButton("Valider")
        self.btn_ok.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold;")
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)
        
        layout.addLayout(btn_layout)
        
        # Stylesheet
        self.setStyleSheet("""
            QComboBox, QDoubleSpinBox, QLabel { color: black; }
            QComboBox { background-color: white; }
        """)

    def load_data(self):
        # Fetch all locations from DB
        all_locs = self.db_manager.get_all_locations()
        self.locations_cache = list(all_locs.values())
        
        # Populate Continents
        continents = sorted(list(set(loc.get("continent", "Unknown") for loc in self.locations_cache if loc.get("continent"))))
        self.combo_continent.clear()
        self.combo_continent.addItems(continents)

    def populate_locations(self):
        self.combo_location.blockSignals(True)
        self.combo_location.clear()
        
        continent = self.combo_continent.currentText()
        
        # Filter by continent
        filtered = [loc for loc in self.locations_cache if loc.get("continent") == continent]
        
        # Group by Type
        grouped = {}
        for loc in filtered:
            ltype = loc.get("type", "Autre")
            if ltype not in grouped:
                grouped[ltype] = []
            grouped[ltype].append(loc)
            
        # Sort types
        sorted_types = sorted(grouped.keys())
        
        model = QStandardItemModel()
        
        for ltype in sorted_types:
            # Header
            header = QStandardItem(f"-- {ltype} --")
            header.setSelectable(False)
            header.setEnabled(False)
            header.setData(None, Qt.ItemDataRole.UserRole)
            model.appendRow(header)
            
            # Items
            # Sort locations by name/city
            locs = grouped[ltype]
            locs.sort(key=lambda x: (x.get("city") or "", x.get("place")))
            
            for loc in locs:
                city = loc.get("city")
                place = loc.get("place") or "Unknown"
                
                coords = loc.get("coords", {})
                x = coords.get("x", 0)
                y = coords.get("y", 0)
                
                if city:
                    display_text = f"{city} - {place} ({x}, {y})"
                else:
                    display_text = f"{place} ({x}, {y})"
                
                item = QStandardItem(display_text)
                item.setData(loc, Qt.ItemDataRole.UserRole)
                model.appendRow(item)
        
        self.combo_location.setModel(model)
        self.combo_location.blockSignals(False)

    def set_initial_state(self):
        # Set Continent
        idx = self.combo_continent.findText(self.continent)
        if idx >= 0:
            self.combo_continent.setCurrentIndex(idx)
        else:
            if self.combo_continent.count() > 0:
                self.combo_continent.setCurrentIndex(0)
                
        self.populate_locations()
        
        # Try to select current location based on coordinates
        # Find closest match in current list
        best_match_idx = -1
        min_dist = 0.1 # Tolerance
        
        model = self.combo_location.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if not item.isEnabled(): continue # Skip headers
            
            loc = item.data(Qt.ItemDataRole.UserRole)
            if not loc: continue
            
            coords = loc.get("coords", {})
            lx = float(coords.get("x", 0))
            ly = float(coords.get("y", 0))
            
            dist = ((lx - self.pos_x)**2 + (ly - self.pos_y)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                best_match_idx = i
        
        if best_match_idx >= 0:
            self.combo_location.setCurrentIndex(best_match_idx)

    def on_continent_changed(self, text):
        self.continent = text
        self.populate_locations()

    def on_location_selected(self, index):
        loc = self.combo_location.currentData()
        if loc:
            coords = loc.get("coords", {})
            self.pos_x = float(coords.get("x", 0))
            self.pos_y = float(coords.get("y", 0))
            self.spin_x.setValue(self.pos_x)
            self.spin_y.setValue(self.pos_y)

    def get_data(self):
        """Returns the configured location data."""
        loc = self.combo_location.currentData()
        location_name = ""
        city = ""
        
        if loc:
            location_name = loc.get("place")
            city = loc.get("city")
            
        return {
            "continent": self.continent,
            "x": self.pos_x,
            "y": self.pos_y,
            "location_name": location_name,
            "city": city
        }
