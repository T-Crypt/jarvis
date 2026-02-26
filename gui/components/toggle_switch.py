"""
ToggleSwitch component - Custom toggle switch for PySide6 JARVIS theme.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QPainter, QColor

class ToggleSwitch(QWidget):
    toggled = Signal(bool)
    
    def __init__(self, label: str = "", checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._thumb_position = 1.0 if checked else 0.0
        self._label = label
        
        self.setFixedSize(80 if label else 50, 28)
        self.setCursor(Qt.PointingHandCursor)
        
        self._animation = QPropertyAnimation(self, b"thumb_position")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def get_thumb_position(self): return self._thumb_position
    def set_thumb_position(self, pos):
        self._thumb_position = pos
        self.update()
    
    thumb_position = Property(float, get_thumb_position, set_thumb_position)
    
    def isChecked(self): return self._checked
    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self._animate_thumb()
            self.toggled.emit(self._checked)
    
    def _animate_thumb(self):
        self._animation.stop()
        self._animation.setStartValue(self._thumb_position)
        self._animation.setEndValue(1.0 if self._checked else 0.0)
        self._animation.start()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        track_width = 44
        track_height = 24
        thumb_size = 20
        padding = 2
        
        label_offset = 0
        if self._label:
            painter.setPen(QColor("#6b7a95"))
            painter.drawText(0, 0, 30, 28, Qt.AlignVCenter | Qt.AlignLeft, self._label)
            label_offset = 35
        
        # JARVIS Colors
        track_off_color = QColor(0, 212, 255, 30) # Dim Cyan
        track_on_color = QColor(0, 212, 255, 255) # Bright Cyan
        
        r = int(track_off_color.red() + (track_on_color.red() - track_off_color.red()) * self._thumb_position)
        g = int(track_off_color.green() + (track_on_color.green() - track_off_color.green()) * self._thumb_position)
        b = int(track_off_color.blue() + (track_on_color.blue() - track_off_color.blue()) * self._thumb_position)
        a = int(track_off_color.alpha() + (track_on_color.alpha() - track_off_color.alpha()) * self._thumb_position)
        track_color = QColor(r, g, b, a)
        
        track_rect = QRectF(label_offset, 2, track_width, track_height)
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, track_height / 2, track_height / 2)
        
        thumb_x = label_offset + padding + (track_width - thumb_size - padding * 2) * self._thumb_position
        thumb_y = 2 + padding
        thumb_rect = QRectF(thumb_x, thumb_y, thumb_size, thumb_size)
        painter.setBrush(QColor("#050a12") if self._checked else QColor("#8b9bb4")) # Dark thumb when on
        painter.drawEllipse(thumb_rect)