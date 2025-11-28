import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from main_player import PlayerWindow
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_launch():
    app = QApplication(sys.argv)
    
    try:
        window = PlayerWindow()
        window.show()
        print("Window created and shown")
        
        # Check if sliding menu exists
        if hasattr(window, 'sliding_menu'):
            print("SlidingMenu initialized")
        else:
            print("SlidingMenu MISSING")
            sys.exit(1)
            
        # Close after 2 seconds
        QTimer.singleShot(2000, app.quit)
        
        app.exec()
        print("Test passed")
    except Exception as e:
        print(f"Runtime error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_launch()
