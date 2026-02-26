"""
Voice Listening Indicator - JARVIS audio uplink visualizer.
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont, QPainter, QColor, QBrush, QPen

class VoiceIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.is_listening = False
        self.pulse_animation = None
        self.opacity_effect = None
        
        self._setup_ui()
        self._setup_animations()
        self.hide()
    
    def _setup_ui(self):
        self.setFixedSize(200, 200)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        self.container = QWidget(self)
        self.container.setFixedSize(200, 200)
        layout.addWidget(self.container)
        
        self.text_label = QLabel("AUDIO UPLINK ACTIVE", self)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setFont(QFont("Consolas", 12, QFont.Bold))
        self.text_label.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                background: rgba(10, 22, 40, 0.7);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
                padding: 6px 12px;
                margin-top: 10px;
                letter-spacing: 2px;
            }
        """)
        layout.addWidget(self.text_label)
        self.setStyleSheet("VoiceIndicator { background: transparent; }")
    
    def _setup_animations(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out.finished.connect(self._on_fade_out_finished)
        
        self.pulse_value = 0.0
        self.pulse_animation = QPropertyAnimation(self, b"pulseValue")
        self.pulse_animation.setDuration(1200)
        self.pulse_animation.setStartValue(0.0)
        self.pulse_animation.setEndValue(1.0)
        self.pulse_animation.setLoopCount(-1) 
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutSine)
    
    def paintEvent(self, event):
        if not self.is_listening: return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        base_size = 80
        pulse_size = base_size + (self.pulse_value * 50) 
        
        center_x = self.width() // 2
        center_y = self.container.height() // 2
        
        # JARVIS Cyan pulses
        pulse_alpha = int(255 * (1 - self.pulse_value))
        pulse_color = QColor(0, 212, 255, pulse_alpha)  
        painter.setPen(QPen(pulse_color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPoint(center_x, center_y), int(pulse_size // 2), int(pulse_size // 2))
        
        main_color = QColor(0, 212, 255, 120) 
        painter.setPen(QPen(main_color, 2))
        painter.setBrush(QBrush(main_color, Qt.SolidPattern))
        painter.drawEllipse(QPoint(center_x, center_y), int(base_size // 2), int(base_size // 2))
        
        inner_color = QColor(0, 212, 255, 255)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(inner_color, Qt.SolidPattern))
        painter.drawEllipse(QPoint(center_x, center_y), 6, 6)
    
    def get_pulse_value(self): return self.pulse_value
    def set_pulse_value(self, value):
        self.pulse_value = value
        self.update() 
    
    pulseValue = property(get_pulse_value, set_pulse_value)
    
    def show_listening(self):
        if self.is_listening: return
        self.is_listening = True
        self._position_window()
        self.show()
        self.fade_in.start()
        if self.pulse_animation: self.pulse_animation.start()
    
    def hide_listening(self, delay_ms: int = 500):
        if not self.is_listening: return
        if delay_ms > 0: QTimer.singleShot(delay_ms, self._do_hide)
        else: self._do_hide()
    
    def _do_hide(self):
        if not self.is_listening: return
        self.is_listening = False
        if self.pulse_animation: self.pulse_animation.stop()
        self.fade_out.start()
    
    def _on_fade_out_finished(self):
        self.hide()
        self.pulse_value = 0.0
    
    def _position_window(self):
        if not self.parent(): return
        parent_rect = self.parent().rect()
        x = (parent_rect.width() - self.width()) // 2
        y = (parent_rect.height() - self.height()) // 2 - 50 
        self.move(x, y)
    
    def showEvent(self, event):
        super().showEvent(event)
        self._position_window()