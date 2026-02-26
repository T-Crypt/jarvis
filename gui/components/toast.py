"""
Toast Notification Component - JARVIS system notifications.
"""

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

class ToastNotification(QWidget):
    
    def __init__(self, parent, message: str, success: bool = True, duration_ms: int = 3000):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self._setup_ui(message, success)
        self._setup_animation(duration_ms)
        
    def _setup_ui(self, message: str, success: bool):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        icon = "✓" if success else "⚠"
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Consolas", 14, QFont.Bold))
        
        msg_label = QLabel(message.upper())
        msg_label.setFont(QFont("Consolas", 11))
        msg_label.setWordWrap(True)
        msg_label.setMaximumWidth(320)
        
        layout.addWidget(icon_label)
        layout.addWidget(msg_label, 1)
        
        # JARVIS styling
        bg_color = "rgba(0, 212, 255, 0.15)" if success else "rgba(255, 59, 48, 0.15)"
        border_color = "#00d4ff" if success else "#ff3b30"
        text_color = "#00d4ff" if success else "#ff3b30"
        
        self.setStyleSheet(f"""
            ToastNotification {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-left: 4px solid {border_color};
                border-radius: 8px;
            }}
            QLabel {{
                color: {text_color};
                background: transparent;
                letter-spacing: 1px;
            }}
        """)
        self.adjustSize()
        
    def _setup_animation(self, duration_ms: int):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out.finished.connect(self.deleteLater)
        
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self._start_fade_out)
        self.dismiss_timer.setInterval(duration_ms)
        
    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.width() - self.width() - 25
            y = 70  
            self.move(x, y)
        self.fade_in.start()
        self.dismiss_timer.start()
        
    def _start_fade_out(self):
        self.fade_out.start()
    
    @staticmethod
    def show_toast(parent, message: str, success: bool = True, duration_ms: int = 3000):
        toast = ToastNotification(parent, message, success, duration_ms)
        toast.show()
        return toast