import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QPixmap, QColor, QCursor
from PyQt6.QtCore import Qt, QPoint

class ItemTooltip(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Main Frame (The Content)
        self.frame = QFrame(self)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #444;
                border-radius: 6px;
            }
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self.frame)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.frame.setGraphicsEffect(shadow)
        
        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(10, 10, 10, 10) # Margin for shadow
        self.layout_main.addWidget(self.frame)
        
        self.layout_content = QVBoxLayout(self.frame)
        self.layout_content.setContentsMargins(10, 10, 10, 10)
        self.layout_content.setSpacing(5)
        
        # UI Elements (To be populated)
        self.lbl_name = QLabel()
        self.lbl_name.setStyleSheet("font-weight: bold; font-size: 14px; color: #fff; font-family: 'Underdog';")
        self.layout_content.addWidget(self.lbl_name)
        
        self.lbl_type = QLabel()
        self.lbl_type.setStyleSheet("color: #888; font-style: italic; font-size: 12px; margin-bottom: 5px;")
        self.layout_content.addWidget(self.lbl_type)
        
        self.stats_container = QWidget()
        self.stats_layout = QHBoxLayout(self.stats_container)
        self.stats_layout.setContentsMargins(0, 0, 0, 0)
        self.stats_layout.setSpacing(5)
        self.layout_content.addWidget(self.stats_container)
        
        self.lbl_desc = QLabel()
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("color: #ccc; font-size: 12px; margin-top: 5px;")
        self.layout_content.addWidget(self.lbl_desc)

    def update_data(self, item_def, assets_dir):
        if not item_def: return

        # 1. Name
        self.lbl_name.setText(item_def.name)
        
        # 2. Type
        type_str = item_def.type.capitalize()
        props = item_def.properties
        subtype = props.get("subtype", "")
        if subtype:
            type_str += f" ({subtype})"
        self.lbl_type.setText(type_str)
        
        # 3. Stats (Badges)
        # Clear previous stats
        while self.stats_layout.count():
            child = self.stats_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        if item_def.type in ["weapon", "armor"]:
            self.stats_container.show()
            self._add_badges(item_def, assets_dir)
        else:
            self.stats_container.hide()
            
        # 4. Description
        self.lbl_desc.setText(item_def.description)
        self.lbl_desc.adjustSize()
        
        # Resize to fit content
        self.adjustSize()

    def _add_badges(self, item_def, assets_dir):
        props = item_def.properties
        
        def add_badge(text, icon=None, bg_color="#2a2a2a", text_color="#ccc"):
            badge = QFrame()
            badge.setStyleSheet(f"background-color: {bg_color}; border-radius: 4px;")
            b_layout = QHBoxLayout(badge)
            b_layout.setContentsMargins(5, 2, 5, 2)
            b_layout.setSpacing(4)
            
            if icon:
                icon_path = os.path.join(assets_dir, icon)
                if os.path.exists(icon_path):
                    pix = QPixmap(icon_path)
                    pix = pix.scaled(14, 14, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    icon_lbl = QLabel()
                    icon_lbl.setPixmap(pix)
                    icon_lbl.setStyleSheet("background: transparent;")
                    b_layout.addWidget(icon_lbl)
            
            txt_lbl = QLabel(str(text))
            txt_lbl.setStyleSheet(f"color:{text_color}; font-size:12px; font-weight:bold; background: transparent;")
            b_layout.addWidget(txt_lbl)
            
            self.stats_layout.addWidget(badge)

        # Damage
        dmg_min = props.get("damage_min", 0)
        dmg_max = props.get("damage_max", 0)
        if dmg_max > 0:
            add_badge(f"{dmg_min}-{dmg_max}", "damages.png", bg_color="#3d2020", text_color="#ffaaaa")
        
        # Speed
        speed = props.get("speed", 0)
        if speed > 0:
            add_badge(f"{speed}", "dexterity.png", bg_color="#20303d", text_color="#aaddff")
        
        # Crit
        crit = props.get("crit_chance", 0)
        crit_mult = props.get("crit_multiplier", 0)
        if crit > 0:
            crit_text = f"{crit}%"
            if crit_mult > 0:
                crit_text += f" x{crit_mult}"
            add_badge(crit_text, "critical.png", bg_color="#3d3d20", text_color="#ffffaa")
            
        self.stats_layout.addStretch()

    def move_to_mouse(self):
        cursor_pos = QCursor.pos()
        # Offset slightly so it doesn't cover the mouse
        self.move(cursor_pos + QPoint(15, 15))
