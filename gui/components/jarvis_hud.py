"""
JARVIS HUD Components - Custom painted Iron Man themed widgets.

Provides:
  ArcReactorWidget   — animated concentric glowing rings
  ScanLineWidget     — animated horizontal scan sweep
  HUDCornerWidget    — corner bracket decorations
  PulseOrb           — pulsing status dot
  HUDDivider         — glowing horizontal rule
"""

import math
from PySide6.QtWidgets import QWidget, QFrame, QHBoxLayout, QLabel, QVBoxLayout
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    Property, QPointF, QRectF, Signal
)
from PySide6.QtGui import (
    QPainter, QPen, QColor, QBrush, QLinearGradient,
    QRadialGradient, QConicalGradient, QPainterPath, QFont
)


# ── Palette constants ────────────────────────────────────────────────────────
CYAN        = QColor(0, 212, 255)
CYAN_DIM    = QColor(0, 212, 255, 60)
CYAN_MID    = QColor(0, 212, 255, 120)
GOLD        = QColor(255, 215, 0)
GOLD_DIM    = QColor(255, 215, 0, 60)
RED_ARC     = QColor(255, 59, 48)
BG_DEEP     = QColor(5, 10, 18)
BG_CARD     = QColor(10, 22, 40)
TEXT_DIM    = QColor(107, 122, 149)


class ArcReactorWidget(QWidget):
    """
    Animated Iron Man arc reactor — concentric glowing rings with rotation.

    Outer ring rotates clockwise, inner ring counter-clockwise.
    Core pulses with a subtle opacity animation.
    """

    def __init__(self, size: int = 120, color: QColor = None, parent=None):
        super().__init__(parent)
        self._size = size
        self._color = color or CYAN
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Animation angles
        self._outer_angle = 0.0
        self._inner_angle = 0.0
        self._core_opacity = 0.5
        self._core_growing = True

        # Rotation timer
        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60fps
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        self._outer_angle = (self._outer_angle + 0.8) % 360
        self._inner_angle = (self._inner_angle - 1.2) % 360

        # Pulse core opacity
        step = 0.008
        if self._core_growing:
            self._core_opacity = min(1.0, self._core_opacity + step)
            if self._core_opacity >= 1.0:
                self._core_growing = False
        else:
            self._core_opacity = max(0.25, self._core_opacity - step)
            if self._core_opacity <= 0.25:
                self._core_growing = True

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        cx = self._size / 2
        cy = self._size / 2
        r = self._size / 2 - 4

        c = self._color

        # ── Outermost glow ring ──────────────────────────────────────
        glow = QColor(c.red(), c.green(), c.blue(), 25)
        glow_pen = QPen(glow, 12)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # ── Outer dashed arc (rotates CW) ───────────────────────────
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._outer_angle)
        painter.translate(-cx, -cy)

        pen_outer = QPen(QColor(c.red(), c.green(), c.blue(), 200), 2)
        pen_outer.setStyle(Qt.DashLine)
        pen_outer.setDashPattern([8, 6])
        painter.setPen(pen_outer)
        r1 = r - 8
        painter.drawEllipse(QRectF(cx - r1, cy - r1, r1 * 2, r1 * 2))
        painter.restore()

        # ── Middle solid ring ────────────────────────────────────────
        r2 = r - 20
        pen_mid = QPen(QColor(c.red(), c.green(), c.blue(), 140), 1.5)
        painter.setPen(pen_mid)
        painter.drawEllipse(QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2))

        # ── Inner arc (rotates CCW) with bright segments ─────────────
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._inner_angle)
        painter.translate(-cx, -cy)

        r3 = r - 32
        pen_inner = QPen(QColor(c.red(), c.green(), c.blue(), 255), 2.5)
        painter.setPen(pen_inner)
        # Draw 3 arc segments (120° each with gaps)
        for i in range(3):
            start_angle = int(i * 120 * 16)
            span_angle  = int(90 * 16)
            painter.drawArc(QRectF(cx - r3, cy - r3, r3 * 2, r3 * 2),
                            start_angle, span_angle)
        painter.restore()

        # ── 6 tick marks around inner ring ──────────────────────────
        r4 = r - 42
        tick_pen = QPen(QColor(c.red(), c.green(), c.blue(), 160), 1.5)
        painter.setPen(tick_pen)
        for i in range(6):
            angle_rad = math.radians(i * 60)
            x1 = cx + (r4 - 4) * math.cos(angle_rad)
            y1 = cy + (r4 - 4) * math.sin(angle_rad)
            x2 = cx + (r4 + 4) * math.cos(angle_rad)
            y2 = cy + (r4 + 4) * math.sin(angle_rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # ── Core glow ────────────────────────────────────────────────
        core_r = r - 52
        grad = QRadialGradient(cx, cy, core_r)
        core_alpha = int(self._core_opacity * 255)
        grad.setColorAt(0.0, QColor(c.red(), c.green(), c.blue(), core_alpha))
        grad.setColorAt(0.5, QColor(c.red(), c.green(), c.blue(), core_alpha // 2))
        grad.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - core_r, cy - core_r, core_r * 2, core_r * 2))

        # Core bright dot
        dot_r = 6
        dot_grad = QRadialGradient(cx, cy, dot_r)
        dot_grad.setColorAt(0.0, Qt.white)
        dot_grad.setColorAt(0.5, QColor(c.red(), c.green(), c.blue(), 220))
        dot_grad.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 0))
        painter.setBrush(QBrush(dot_grad))
        painter.drawEllipse(QRectF(cx - dot_r, cy - dot_r, dot_r * 2, dot_r * 2))

        painter.end()

    def stop(self):
        self._timer.stop()

    def start(self):
        self._timer.start()


class ScanLineWidget(QWidget):
    """
    Animated horizontal scan line that sweeps top to bottom repeatedly.
    """

    def __init__(self, width: int, height: int, color: QColor = None, parent=None):
        super().__init__(parent)
        self._color = color or CYAN
        self.setFixedSize(width, height)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._scan_y = 0.0
        self._speed = height / 80.0  # sweep in ~80 ticks at 60fps ≈ 1.3s

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        self._scan_y += self._speed
        if self._scan_y > self.height() + 40:
            self._scan_y = -40
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        y = self._scan_y
        c = self._color

        # Horizontal gradient line
        grad = QLinearGradient(0, y, w, y)
        grad.setColorAt(0.0,  QColor(c.red(), c.green(), c.blue(), 0))
        grad.setColorAt(0.2,  QColor(c.red(), c.green(), c.blue(), 80))
        grad.setColorAt(0.5,  QColor(c.red(), c.green(), c.blue(), 180))
        grad.setColorAt(0.8,  QColor(c.red(), c.green(), c.blue(), 80))
        grad.setColorAt(1.0,  QColor(c.red(), c.green(), c.blue(), 0))

        pen = QPen(QBrush(grad), 1.5)
        painter.setPen(pen)
        painter.drawLine(QPointF(0, y), QPointF(w, y))

        # Fading trail above the line
        trail_grad = QLinearGradient(0, y - 30, w, y - 30)
        trail_grad.setColorAt(0.0, QColor(c.red(), c.green(), c.blue(), 0))
        trail_grad.setColorAt(0.5, QColor(c.red(), c.green(), c.blue(), 30))
        trail_grad.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 0))
        trail_pen = QPen(QBrush(trail_grad), 1)
        painter.setPen(trail_pen)
        painter.drawLine(QPointF(0, y - 15), QPointF(w, y - 15))

        painter.end()


class HUDCornerWidget(QWidget):
    """
    Draws HUD-style corner bracket decorations on a rectangle.
    """

    def __init__(self, width: int, height: int, color: QColor = None,
                 corner_size: int = 20, parent=None):
        super().__init__(parent)
        self._color = color or CYAN
        self._corner = corner_size
        self.setFixedSize(width, height)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        c = self._color
        pen = QPen(QColor(c.red(), c.green(), c.blue(), 200), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        w = self.width() - 1
        h = self.height() - 1
        s = self._corner

        # Top-left
        painter.drawLine(0, s, 0, 0)
        painter.drawLine(0, 0, s, 0)

        # Top-right
        painter.drawLine(w - s, 0, w, 0)
        painter.drawLine(w, 0, w, s)

        # Bottom-left
        painter.drawLine(0, h - s, 0, h)
        painter.drawLine(0, h, s, h)

        # Bottom-right
        painter.drawLine(w - s, h, w, h)
        painter.drawLine(w, h - s, w, h)

        painter.end()


class PulseOrb(QWidget):
    """
    A small pulsing status orb for displaying active/inactive states.
    """

    def __init__(self, size: int = 12, color: QColor = None, parent=None):
        super().__init__(parent)
        self._color = color or CYAN
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._opacity = 0.4
        self._growing = True

        self._timer = QTimer(self)
        self._timer.setInterval(20)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        step = 0.015
        if self._growing:
            self._opacity = min(1.0, self._opacity + step)
            if self._opacity >= 1.0:
                self._growing = False
        else:
            self._opacity = max(0.3, self._opacity - step)
            if self._opacity <= 0.3:
                self._growing = True
        self.update()

    def set_color(self, color: QColor):
        self._color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        c = self._color
        s = self.width()
        r = s / 2

        # Outer glow
        glow_alpha = int(self._opacity * 80)
        glow = QRadialGradient(r, r, r)
        glow.setColorAt(0.3, QColor(c.red(), c.green(), c.blue(), glow_alpha))
        glow.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(0, 0, s, s))

        # Core dot
        dot_alpha = int(self._opacity * 255)
        core_r = r * 0.55
        core_grad = QRadialGradient(r, r * 0.8, core_r)
        core_grad.setColorAt(0, QColor(255, 255, 255, min(255, dot_alpha + 60)))
        core_grad.setColorAt(0.5, QColor(c.red(), c.green(), c.blue(), dot_alpha))
        core_grad.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), dot_alpha // 2))
        painter.setBrush(QBrush(core_grad))
        cx, cy = r - core_r, r - core_r
        painter.drawEllipse(QRectF(cx, cy, core_r * 2, core_r * 2))

        painter.end()


class HUDDivider(QWidget):
    """
    A horizontal glowing divider line for separating sections.
    """

    def __init__(self, width: int = 0, color: QColor = None,
                 opacity: float = 0.4, parent=None):
        super().__init__(parent)
        self._color = color or CYAN
        self._opacity = opacity
        self.setFixedHeight(1)
        if width:
            self.setFixedWidth(width)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        c = self._color
        alpha = int(self._opacity * 255)

        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, QColor(c.red(), c.green(), c.blue(), 0))
        grad.setColorAt(0.3, QColor(c.red(), c.green(), c.blue(), alpha))
        grad.setColorAt(0.7, QColor(c.red(), c.green(), c.blue(), alpha))
        grad.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 0))

        painter.setPen(QPen(QBrush(grad), 1))
        painter.drawLine(0, 0, self.width(), 0)
        painter.end()


class DataTickerWidget(QWidget):
    """
    Displays a scrolling HUD-style data readout e.g. "SYS ████ 72%".
    """

    def __init__(self, label: str, value: str = "—",
                 color: QColor = None, parent=None):
        super().__init__(parent)
        self._color = color or CYAN
        self._label = label
        self._value = value
        self.setFixedHeight(28)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_value(self, value: str):
        self._value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        c = self._color
        w = self.width()

        # Label
        label_font = QFont("Consolas", 9)
        label_font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        painter.setFont(label_font)
        painter.setPen(QColor(107, 122, 149))
        painter.drawText(QRectF(0, 0, 60, 28), Qt.AlignVCenter | Qt.AlignLeft,
                         self._label.upper())

        # Value
        val_font = QFont("Consolas", 10)
        val_font.setBold(True)
        painter.setFont(val_font)
        painter.setPen(QColor(c.red(), c.green(), c.blue()))
        painter.drawText(QRectF(65, 0, w - 65, 28), Qt.AlignVCenter | Qt.AlignLeft,
                         self._value)

        painter.end()
