"""
SearchIndicator component - JARVIS Visual feedback for web search operations.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QSizePolicy, QWidget
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QRectF, QPointF
from PySide6.QtGui import QFont, QPainter, QColor

class RotatingSearchIcon(QWidget):
    def __init__(self, text="⟲", color="#00d4ff", font_size=16, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self._text = text
        self._color = QColor(color)
        self._font = QFont("Consolas", font_size)
        self._font.setBold(True)
        self._angle = 0
        self._animation = None
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def get_angle(self): return self._angle
    def set_angle(self, angle): 
        self._angle = angle
        self.update()

    angle = Property(float, get_angle, set_angle)

    def start_animation(self):
        if not self._animation:
            self._animation = QPropertyAnimation(self, b"angle", self)
            self._animation.setDuration(1500)
            self._animation.setStartValue(0)
            self._animation.setEndValue(360)
            self._animation.setLoopCount(-1) 
            self._animation.start()

    def stop_animation(self):
        if self._animation:
            self._animation.stop()
            self._animation = None
        self._angle = 0
        self.update()

    def set_complete(self):
        self.stop_animation()
        self._text = "✓"
        self._color = QColor("#00d4ff") # Keep JARVIS Cyan for success
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)
        painter.setPen(self._color)
        painter.setFont(self._font)
        rect = QRectF(-self.width() / 2, -self.height() / 2, self.width(), self.height())
        painter.drawText(rect, Qt.AlignCenter, self._text)


class SearchIndicator(QFrame):
    """Visual indicator for web search operations."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchIndicator")
        self._is_expanded = True
        self._animation = None
        self._content_height = 0
        self.setMaximumWidth(600)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
        self._setup_ui()
        self._apply_style()
        self.spinner.start_animation()
        
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.header = QFrame()
        self.header.setObjectName("searchHeader")
        self.header.setCursor(Qt.PointingHandCursor)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(10)
        
        self.spinner = RotatingSearchIcon()
        header_layout.addWidget(self.spinner)
        
        self.title_label = QLabel("ESTABLISHING WEB UPLINK...")
        self.title_label.setStyleSheet("color: #00d4ff; font-size: 12px; font-family: Consolas; letter-spacing: 1px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        self.arrow_label = QLabel("▼")
        self.arrow_label.setStyleSheet("color: #6b7a95; font-size: 10px;")
        header_layout.addWidget(self.arrow_label)
        
        self.main_layout.addWidget(self.header)
        
        self.content_container = QWidget()
        self.content_container.setMaximumHeight(170)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(12, 0, 12, 12)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setMinimumHeight(60)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(5, 10, 18, 0.8);
                color: #00d4ff;
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 6px;
                padding: 8px;
                line-height: 140%;
            }
        """)
        content_layout.addWidget(self.log_text)
        
        self.main_layout.addWidget(self.content_container)
        self.header.mousePressEvent = self._on_header_click
        
    def _apply_style(self):
        self.setStyleSheet("""
            QFrame#searchIndicator {
                background-color: rgba(10, 22, 40, 0.6);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                margin-bottom: 6px;
                margin-top: 6px;
            }
            QFrame#searchHeader {
                background-color: transparent;
                border-radius: 8px;
            }
            QFrame#searchHeader:hover {
                background-color: rgba(0, 212, 255, 0.1);
            }
        """)
        
    def _on_header_click(self, event):
        self.toggle_expanded()
        
    def toggle_expanded(self):
        self._is_expanded = not self._is_expanded
        self.arrow_label.setText("▼" if self._is_expanded else "▶")
        target_height = 170 if self._is_expanded else 0
        
        if self._animation:
            self._animation.stop()
            
        self._animation = QPropertyAnimation(self.content_container, b"maximumHeight", self)
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.setStartValue(self.content_container.maximumHeight())
        self._animation.setEndValue(target_height)
        self._animation.start()
        
    def add_query(self, query: str):
        self.log_text.insertPlainText(f"> TRANSMITTING QUERY: {query}\n")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def complete(self):
        self.spinner.set_complete()
        self.title_label.setText("UPLINK COMPLETE")