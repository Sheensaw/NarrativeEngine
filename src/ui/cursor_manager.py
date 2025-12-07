import os
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtCore import Qt, QObject, QEvent
from PyQt6.QtWidgets import QPushButton, QAbstractButton, QTabBar

class CursorManager(QObject):
    _instance = None
    
    def __init__(self):
        super().__init__()
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "cursors")
        self.resized_dir = os.path.join(self.base_dir, "resized")
        
        # Ensure resized dir exists
        if not os.path.exists(self.resized_dir):
            os.makedirs(self.resized_dir)

        # Definitions handled as before
        self.cursors_def = {
            "default": { "file": "default_arrow.png", "hotspot": (7, 5) },
            "pointer": { "file": "hand_point.png", "hotspot": (10, 7) },
            "grab": { "file": "hand_grab_hoover.png", "hotspot": (33, 30) },
            "closed": { "file": "hand_grab_closed.png", "hotspot": (33, 30) }
        }
        
        self.loaded_cursors = {}

    def process_cursors(self):
        """Resizes images and loads QCursor objects."""
        for key, data in self.cursors_def.items():
            src_path = os.path.join(self.base_dir, data["file"])
            dst_path = os.path.join(self.resized_dir, data["file"])

            if not os.path.exists(src_path):
                print(f"[CursorManager] Warning: Source cursor not found: {src_path}")
                continue

            if not os.path.exists(dst_path):
                pix = QPixmap(src_path)
                if not pix.isNull():
                    scaled = pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    scaled.save(dst_path)
            
            # Load QCursor
            if os.path.exists(dst_path):
                pix = QPixmap(dst_path)
                hotspot_x, hotspot_y = data["hotspot"]
                self.loaded_cursors[key] = QCursor(pix, hotspot_x, hotspot_y)
                
    def get_cursor(self, name):
        return self.loaded_cursors.get(name)

    def eventFilter(self, obj, event):
        # Global Event Filter to handle Hover Logic
        if event.type() == QEvent.Type.Enter:
            # Check interaction type
            if isinstance(obj, (QAbstractButton, QTabBar)):
                 # We can't just obj.setCursor because it might flicker or be overridden
                 ptr = self.get_cursor("pointer")
                 if ptr: 
                    obj.setCursor(ptr)
            elif obj.inherits("InventorySlotWidget"): 
                 ptr = self.get_cursor("pointer")
                 if ptr:
                    obj.setCursor(ptr)
            elif obj.inherits("QTextEdit") or obj.inherits("FadeTextEdit"):
                 # Force default cursor instead of IBeam
                 # Note: QTextEdit events often bubble from viewport, so we might catch viewport here?
                 # Viewport usually doesn't import properties from parent easily but let's try.
                 default = self.get_cursor("default")
                 if default:
                    obj.setCursor(default)
                    # Force viewport too just in case
                    if hasattr(obj, "viewport") and obj.viewport():
                        obj.viewport().setCursor(default)
                        
        return super().eventFilter(obj, event)

def setup_cursors(app):
    # Singleton patternish
    if not CursorManager._instance:
        CursorManager._instance = CursorManager()
    
    manager = CursorManager._instance
    manager.process_cursors()
    
    # 1. Set Default Cursor for the whole App (Fallback)
    default_cursor = manager.get_cursor("default")
    if default_cursor:
        # We need to set this on existing windows or the app override?
        # App override is too strong.
        # We rely on setting it on the top-level windows usually, or via event filter.
        pass

    # Install Global Event Filter
    app.installEventFilter(manager)
    
    # Apply default cursor to all top level widgets? 
    # Hard to guarantee. 
    # Better: Update Loop or just rely on manual 'setCursor' in main classes if possible.
    # But for now, let's try to set the generic default on the app using a specific call?
    # No, let's iterate top level widgets?
    for widget in app.topLevelWidgets():
         if default_cursor: widget.setCursor(default_cursor)

