from PyQt6.QtWidgets import QTextEdit, QPushButton, QGraphicsOpacityEffect, QFrame, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, QSize, pyqtSignal, QTime
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QCursor
from .cursor_manager import CursorManager

class FadeSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, speed_per_char=15):
        super().__init__(document)
        self.char_speed = speed_per_char
        self.fade_duration = 1000.0 # 1s fade per char
        self.start_time = 0
        self.running = False
        
    def start_animation(self):
        self.start_time = QTime.currentTime().msecsSinceStartOfDay()
        self.running = True
        self.rehighlight()
        
    def highlightBlock(self, text):
        if not self.running:
            return

        current_time = QTime.currentTime().msecsSinceStartOfDay()
        # Handle day wrap-around edge case simply (rare but good practice)
        if current_time < self.start_time: 
            elapsed = (current_time + 86400000) - self.start_time
        else:
            elapsed = current_time - self.start_time

        block_pos = self.currentBlock().position()
        
        # Optimization: We only need to format the "gradient" zone
        # Chars fully visible: index * speed + fade_duration < elapsed
        # Chars invisible: index * speed > elapsed
        
        # Calculate indices relative to GLOBAL document
        # But loop behaves local to block (0..len(text))
        
        # We formats char by char for the gradient zone (smoothness)
        # Optimized: find local range of gradient
        
        # alpha = (elapsed - (global_index * speed)) / duration * 255
        # when alpha >= 255, full visible.
        # when alpha <= 0, invisible.
        
        # Start of gradient (alpha < 255): global_index > (elapsed - duration) / speed
        # End of gradient (alpha > 0): global_index < elapsed / speed
        
        start_grad_global = int((elapsed - self.fade_duration) / self.char_speed)
        end_grad_global = int(elapsed / self.char_speed) + 2 # buffer
        
        # Localize
        start_local = max(0, start_grad_global - block_pos)
        end_local = min(len(text), end_grad_global - block_pos)
        
        # 1. Fully Visible Zone (0 to start_local)
        # We MUST format this because base text color is transparent
        if start_local > 0:
            visible_fmt = QTextCharFormat()
            visible_fmt.setForeground(QColor(255, 255, 255, 255))
            self.setFormat(0, start_local, visible_fmt)

        # 2. Gradient Zone (start_local to end_local)
        for i in range(start_local, end_local + 1):
             if i < 0 or i >= len(text): continue
             global_idx = block_pos + i
             
             # Calculate exact alpha
             char_start_time = global_idx * self.char_speed
             char_elapsed = elapsed - char_start_time
             # 0 to duration mapped to 0 to 255
             alpha = max(0, min(255, int((char_elapsed / self.fade_duration) * 255)))
             
             fmt = QTextCharFormat()
             fmt.setForeground(QColor(255, 255, 255, alpha))
             self.setFormat(i, 1, fmt)
             
        # 3. Invisible Zone (end_local to len)
        # Left unformatted -> uses base style (Transparent)
             
        # Previous chars (0 to start_local) are left default (visible) by default NO,
        # Default text color might be needed if base color isn't set, but QTextEdit handles it.
        # Actually, if we don't setFormat, it uses default usage style.
        # So we only mess with the "incoming" wave.

class FadeTextEdit(QTextEdit):
    """
    QTextEdit with a Per-Character Fade-In Typewriter effect.
    Uses QSyntaxHighlighter to animate opacity of letters.
    """
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        # Cursor Force
        if CursorManager._instance:
            default = CursorManager._instance.get_cursor("default")
            if default:
                self.setCursor(default)
                if self.viewport():
                    self.viewport().setCursor(default)
        
        self.full_text = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_step)
        
        self.highlighter = FadeSyntaxHighlighter(self.document(), speed_per_char=15)
        
    def show_text(self, text):
        self.full_text = text
        self.setPlainText("") # Clear
        
        # Force Font & Style
        # CRITICAL: Text color MUST be transparent initially so the highlighter controls visibility
        font = self.font()
        font.setFamily("Underdog")
        font.setPointSize(20) 
        self.setFont(font)
        
        self.setStyleSheet("font-family: 'Underdog'; font-size: 20px; color: transparent; background: transparent;")
        
        # Start Highlighter Animation
        self.highlighter.start_animation()
        
        # Start Refresher
        self.timer.start(16)
        
        self.setPlainText(self.full_text)
        self.verticalScrollBar().setValue(0)

    def _animate_step(self):
        # Trigger re-highlight
        self.highlighter.rehighlight()
        
        # Check finish condition
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        if current_time < self.highlighter.start_time:
             elapsed = (current_time + 86400000) - self.highlighter.start_time
        else:
             elapsed = current_time - self.highlighter.start_time
             
        total_time_needed = len(self.full_text) * self.highlighter.char_speed + self.highlighter.fade_duration
        
        if elapsed > total_time_needed:
            self.timer.stop()
            self.finished.emit()
            
            # Reset style to solid white at end for performance/consistency
            self.setStyleSheet("font-family: 'Underdog'; font-size: 20px; color: #ffffff; background: transparent;")
        
        # Optional: Auto-scroll
        curr_idx = int(elapsed / self.highlighter.char_speed)
        if curr_idx < len(self.full_text):
            cursor = self.textCursor()
            cursor.setPosition(curr_idx)
            self.setTextCursor(cursor)
