from PyQt6.QtGui import QImage
import os

base = "c:/Users/garwi/Documents/NarrativeEngine/src/assets/cursors"
files = ["default_arrow.png", "hand_point.png", "hand_grab_hoover.png", "hand_grab_closed.png"]

for f in files:
    path = os.path.join(base, f)
    if os.path.exists(path):
        img = QImage(path)
        print(f"{f}: {img.width()}x{img.height()}")
    else:
        print(f"{f}: Not Found")
