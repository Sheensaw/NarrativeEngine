import os
from PyQt6.QtGui import QImage

assets_dir = r"c:\Users\garwi\Documents\NarrativeEngine\src\assets\icons"
files = os.listdir(assets_dir)

print(f"{'File':<20} {'Size':<10}")
print("-" * 30)

for f in files:
    if f.endswith(".png"):
        path = os.path.join(assets_dir, f)
        img = QImage(path)
        print(f"{f:<20} {img.width()}x{img.height()}")
