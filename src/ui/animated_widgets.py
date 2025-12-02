from PyQt6.QtWidgets import QTextEdit, QPushButton, QGraphicsOpacityEffect, QFrame
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, QSize, pyqtSignal

class FadeTextEdit(QTextEdit):
    """
    QTextEdit with a typewriter effect (left-to-right reveal) AND a soft fade-in.
    """
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.full_text = ""
        self.current_char_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._step_typewriter)
        
        # Opacity Effect for the "soft" feel
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)
        
    def show_text(self, text):
        self.full_text = text
        self.current_char_index = 0
        self.setMarkdown("")
        
        # Force Font
        font = self.font()
        font.setFamily("Underdog")
        font.setPointSize(20) 
        self.setFont(font)
        
        # Reset Opacity
        self.opacity_effect.setOpacity(0.0)
        
        # Start Fade Animation (Global fade for softness)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(1000) # 1 second fade
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.start()
        
        # Start Typewriter (Left to Right)
        # Faster speed: 10ms per char
        self.timer.start(10) 

    def _step_typewriter(self):
        if self.current_char_index < len(self.full_text):
            self.current_char_index += 1 # 1 char at a time for smoothness
            partial = self.full_text[:self.current_char_index]
            self.setMarkdown(partial)
            
            # Re-apply font style
            self.setStyleSheet("font-family: 'Underdog'; font-size: 20px; color: #ffffff; background: transparent;")
        else:
            self.timer.stop()
            self.setMarkdown(self.full_text)
            self.setStyleSheet("font-family: 'Underdog'; font-size: 20px; color: #ffffff; background: transparent;")
            self.finished.emit()


class HoverButton(QPushButton):
    """
    QPushButton with hover animation (slide right).
    """
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._padding_left = 15 # Default padding
        
    @pyqtProperty(int)
    def paddingLeft(self):
        return self._padding_left
        
    @paddingLeft.setter
    def paddingLeft(self, val):
        self._padding_left = val
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left; 
                font-size: 18px; 
                margin: 5px 0; 
                padding: 15px; 
                padding-left: {val}px;
                border-left: 3px solid #555;
                background-color: #2a2a2a;
                color: #eee;
                border-radius: 4px;
                font-family: 'Underdog';
            }}
            QPushButton:hover {{
                border-left-color: #c42b1c; 
                background-color: #1e1e1e;
            }}
        """)

    def enterEvent(self, event):
        self.anim = QPropertyAnimation(self, b"paddingLeft")
        self.anim.setDuration(200)
        self.anim.setStartValue(15)
        self.anim.setEndValue(10)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim = QPropertyAnimation(self, b"paddingLeft")
        self.anim.setDuration(200)
        self.anim.setStartValue(10)
        self.anim.setEndValue(15)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.start()
        super().leaveEvent(event)
