"""
JARVIS Dashboard — Iron Man HUD aesthetic.
Added: Network Telemetry, Global Uplink Clocks, and AI Core Visualizer.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QDate, QTime, QThread, Signal, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QBrush, QPolygonF

from qfluentwidgets import (
    CardWidget, BodyLabel, StrongBodyLabel,
    FluentIcon as FIF, IconWidget, TransparentToolButton
)

from core.news import news_manager
from core.tasks import task_manager
from core.calendar_manager import calendar_manager
from core.kasa_control import kasa_manager
from core.signalrgb import signalrgb_client
from datetime import datetime
import asyncio
import psutil
import random

try:
    from zoneinfo import ZoneInfo
except ImportError:
    pass # Fallback handled gracefully in the code

from core.weather import weather_manager
from gui.components.jarvis_hud import (
    ArcReactorWidget, ScanLineWidget, HUDCornerWidget,
    PulseOrb, HUDDivider, DataTickerWidget, CYAN, GOLD, RED_ARC
)


# ── Palette ──────────────────────────────────────────────────────────────────
_CYAN   = "#00d4ff"
_GOLD   = "#ffd700"
_RED    = "#ff3b30"
_BG     = "#050a12"
_CARD   = "rgba(10, 22, 40, 0.85)" 
_CARD2  = "#0d1f3c"
_TEXT   = "#c0c8d8"
_MUTED  = "#8b9bb4" 
_BORDER = "rgba(0, 212, 255, 0.15)"


# ── Reusable card base ────────────────────────────────────────────────────────

class HUDCard(QFrame):
    def __init__(self, corner_size: int = 14, accent_color: str = _CYAN, parent=None):
        super().__init__(parent)
        self._corners = HUDCornerWidget(
            self.width(), self.height(),
            QColor(accent_color), corner_size, self
        )
        self._corners.lower()

        border_hex = "rgba(0, 212, 255, 0.18)"
        top_hex    = "rgba(0, 212, 255, 0.50)"
        if accent_color == _GOLD:
            border_hex = "rgba(255, 215, 0, 0.18)"
            top_hex    = "rgba(255, 215, 0, 0.50)"
        elif accent_color == _RED:
            border_hex = "rgba(255, 59, 48, 0.20)"
            top_hex    = "rgba(255, 59, 48, 0.55)"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {_CARD};
                border: 1px solid {border_hex};
                border-top: 1px solid {top_hex};
                border-radius: 14px;
            }}
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._corners.resize(self.width(), self.height())


# ── AI Core Visualizer ────────────────────────────────────────────────────────

class AICoreVisualizer(QWidget):
    """Grid of flashing blocks simulating neural network activity."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 48)
        self.grid_x = 12
        self.grid_y = 4
        self.blocks = [[random.random() for _ in range(self.grid_y)] for _ in range(self.grid_x)]
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_blocks)
        self.timer.start(80) # Fast pulse update

    def update_blocks(self):
        for x in range(self.grid_x):
            for y in range(self.grid_y):
                self.blocks[x][y] = (self.blocks[x][y] + random.uniform(-0.3, 0.3))
                self.blocks[x][y] = max(0.1, min(0.95, self.blocks[x][y]))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()
        bw = (w - (self.grid_x - 1) * 2) / self.grid_x
        bh = (h - (self.grid_y - 1) * 2) / self.grid_y

        for x in range(self.grid_x):
            for y in range(self.grid_y):
                alpha = int(self.blocks[x][y] * 255)
                painter.setBrush(QColor(0, 212, 255, alpha))
                painter.setPen(Qt.NoPen)
                painter.drawRect(int(x * (bw + 2)), int(y * (bh + 2)), int(bw), int(bh))


# ── Global Uplink Clocks ─────────────────────────────────────────────────────

class GlobalUplinkWidget(QWidget):
    """Horizontal strip of world clocks."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(25)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.clocks = []
        locations = [
            ("TOKYO", "Asia/Tokyo"),
            ("LONDON", "Europe/London"),
            ("NEW YORK", "America/New_York"),
            ("SILICON VALLEY", "America/Los_Angeles")
        ]

        for city, tz in locations:
            row = QHBoxLayout()
            row.setSpacing(6)
            orb = PulseOrb(6, QColor(_CYAN))
            lbl = QLabel(f"{city}: --:--")
            lbl.setStyleSheet(f"color: {_MUTED}; font-family: Consolas; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
            
            row.addWidget(orb)
            row.addWidget(lbl)
            self.clocks.append((lbl, city, tz))
            layout.addLayout(row)
            layout.addStretch()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_times)
        self.timer.start(1000)
        self.update_times()

    def update_times(self):
        for lbl, city, tz_str in self.clocks:
            try:
                t = datetime.now(ZoneInfo(tz_str)).strftime("%H:%M")
            except:
                t = datetime.now().strftime("%H:%M") # Safe Fallback
            lbl.setText(f"{city}: {t}")


# ── Greeting Header ──────────────────────────────────────────────────────────

class WeatherWorker(QThread):
    finished = Signal(dict)
    def run(self):
        data = weather_manager.get_weather()
        self.finished.emit(data or {})


class JARVISHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(140)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(30)

        self.reactor = ArcReactorWidget(size=110)
        outer.addWidget(self.reactor, 0, Qt.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.setContentsMargins(0, 0, 0, 0)

        self.sub_lbl = QLabel("J.A.R.V.I.S.  ·  SYSTEM INTERFACE ONLINE")
        self.sub_lbl.setStyleSheet(f"color: {_MUTED}; font-size: 12px; letter-spacing: 3px; font-family: Consolas;")

        self.greeting_lbl = QLabel("GOOD MORNING")
        self.greeting_lbl.setStyleSheet(f"color: {_CYAN}; font-size: 38px; font-weight: 700; font-family: 'Segoe UI', 'SF Pro Display', sans-serif;")

        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet(f"color: {_MUTED}; font-size: 14px; font-family: Consolas; letter-spacing: 1px;")

        text_col.addWidget(self.sub_lbl)
        text_col.addWidget(self.greeting_lbl)
        text_col.addWidget(self.date_lbl)
        outer.addLayout(text_col, 1)

        # ── AI Core Visualizer Injected Here ──
        core_col = QVBoxLayout()
        core_col.setAlignment(Qt.AlignCenter)
        core_lbl = QLabel("NEURAL CORE")
        core_lbl.setStyleSheet(f"color: {_CYAN}; font-size: 10px; font-family: Consolas; letter-spacing: 2px;")
        core_lbl.setAlignment(Qt.AlignCenter)
        self.ai_core = AICoreVisualizer()
        core_col.addWidget(core_lbl)
        core_col.addWidget(self.ai_core)
        outer.addLayout(core_col)

        right_col = QVBoxLayout()
        right_col.setSpacing(6)
        right_col.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        time_frame = QFrame()
        time_frame.setFixedSize(160, 72)
        time_frame.setStyleSheet(f"""
            QFrame {{ background-color: {_CARD}; border: 1px solid rgba(0, 212, 255, 0.25); border-top: 1px solid rgba(0, 212, 255, 0.6); border-radius: 16px; }}
        """)
        tf_layout = QVBoxLayout(time_frame)
        tf_layout.setAlignment(Qt.AlignCenter)
        tf_layout.setContentsMargins(0, 0, 0, 0)

        self.clock_lbl = QLabel("00:00 AM")
        self.clock_lbl.setAlignment(Qt.AlignCenter)
        self.clock_lbl.setStyleSheet(f"color: {_CYAN}; font-size: 22px; font-weight: 700; font-family: Consolas;")
        tf_layout.addWidget(self.clock_lbl)

        wx_frame = QFrame()
        wx_frame.setFixedSize(160, 72)
        wx_frame.setStyleSheet(f"""
            QFrame {{ background-color: {_CARD}; border: 1px solid rgba(0, 212, 255, 0.20); border-top: 1px solid rgba(0, 212, 255, 0.50); border-radius: 16px; }}
        """)
        wx_layout = QVBoxLayout(wx_frame)
        wx_layout.setAlignment(Qt.AlignCenter)
        wx_layout.setContentsMargins(0, 4, 0, 4)
        wx_layout.setSpacing(2)

        self.wx_icon  = QLabel("⛅")
        self.wx_icon.setAlignment(Qt.AlignCenter)
        self.wx_icon.setStyleSheet("font-size: 20px; background: transparent;")

        self.wx_temp  = QLabel("--°")
        self.wx_temp.setAlignment(Qt.AlignCenter)
        self.wx_temp.setStyleSheet(f"color: {_TEXT}; font-size: 14px; font-weight: 600; font-family: Consolas;")

        self.wx_cond  = QLabel("LOADING")
        self.wx_cond.setAlignment(Qt.AlignCenter)
        self.wx_cond.setStyleSheet(f"color: {_MUTED}; font-size: 11px; letter-spacing: 2px; font-family: Consolas;")

        wx_layout.addWidget(self.wx_icon)
        wx_layout.addWidget(self.wx_temp)
        wx_layout.addWidget(self.wx_cond)

        right_col.addWidget(time_frame)
        right_col.addWidget(wx_frame)
        outer.addLayout(right_col)

        self._update_time()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)

        self._fetch_weather()
        self._wx_timer = QTimer(self)
        self._wx_timer.timeout.connect(self._fetch_weather)
        self._wx_timer.start(900_000)

    def _update_time(self):
        now = datetime.now()
        h = now.hour
        greeting = ("GOOD MORNING" if 5 <= h < 12 else
                    "GOOD AFTERNOON" if 12 <= h < 18 else
                    "GOOD EVENING")
        self.greeting_lbl.setText(greeting)
        self.date_lbl.setText("[ " + QDate.currentDate().toString("dddd, MMMM d").upper() + " ]")
        self.clock_lbl.setText(QTime.currentTime().toString("h:mm AP"))

    def _fetch_weather(self):
        # SAFETY GUARD
        if hasattr(self, '_wx_worker') and self._wx_worker and self._wx_worker.isRunning():
            return
            
        self._wx_worker = WeatherWorker()
        self._wx_worker.finished.connect(self._on_weather)
        self._wx_worker.finished.connect(self._wx_worker.deleteLater)
        self._wx_worker.start()

    def _on_weather(self, data):
        if not data:
            self.wx_cond.setText("OFFLINE")
            return
            
        temp_raw = data.get("temp")
        unit = data.get("unit", "°F") 
        if temp_raw is not None:
            try:
                self.wx_temp.setText(f"{round(float(temp_raw))}{unit}")
            except ValueError:
                self.wx_temp.setText("--")
        else:
            self.wx_temp.setText("--")
            
        code = data.get("code", -1)
        mapping = {
            0: ("☀️", "CLEAR"), 1: ("🌤️", "MOSTLY CLEAR"), 2: ("⛅", "PARTLY CLOUDY"),
            3: ("☁️", "OVERCAST"), 45: ("🌫️", "FOG"), 48: ("🌫️", "FOG")
        }
        icon, text = mapping.get(code, ("🌡️", "UNKNOWN"))
        if 51 <= code <= 65: icon, text = "🌧️", "RAIN"
        elif 71 <= code <= 77: icon, text = "❄️", "SNOW"
        elif code >= 95: icon, text = "⚡", "STORM"
            
        self.wx_icon.setText(icon)
        self.wx_cond.setText(text)


# ── Live Network Telemetry ────────────────────────────────────────────────────

class NetworkGraph(QWidget):
    """Draws a scrolling real-time network graph."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.history_size = 40
        self.dl_history = [0] * self.history_size
        self.ul_history = [0] * self.history_size
        self.max_val = 1024 * 500 # Default 500KB/s scale

    def update_data(self, dl, ul):
        self.dl_history.pop(0)
        self.dl_history.append(dl)
        self.ul_history.pop(0)
        self.ul_history.append(ul)
        
        current_max = max(max(self.dl_history), max(self.ul_history))
        if current_max > self.max_val:
            self.max_val = current_max
        elif current_max < self.max_val * 0.5 and self.max_val > 1024 * 500:
            self.max_val = max(1024 * 500, current_max * 1.5)
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        dl_poly = QPolygonF()
        dl_poly.append(QPointF(0, h))
        
        ul_poly = QPolygonF()
        
        step = w / (self.history_size - 1)
        for i in range(self.history_size):
            x = i * step
            
            dl_y = h - (self.dl_history[i] / self.max_val) * h
            dl_poly.append(QPointF(x, dl_y))
            
            ul_y = h - (self.ul_history[i] / self.max_val) * h
            ul_poly.append(QPointF(x, ul_y))
            
        dl_poly.append(QPointF(w, h))

        # Fill Download (Cyan)
        painter.setBrush(QColor(0, 212, 255, 60))
        painter.setPen(QPen(QColor(0, 212, 255, 180), 1.5))
        painter.drawPolygon(dl_poly)

        # Line Upload (Gold)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 215, 0, 200), 1.5))
        painter.drawPolyline(ul_poly)


class NetworkTelemetryCard(HUDCard):
    """Dashboard card showing live Network I/O."""
    def __init__(self, parent=None):
        super().__init__(corner_size=12, accent_color=_CYAN, parent=parent)
        self.setFixedSize(265, 140)
        
        self.last_io = psutil.net_io_counters()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        hdr = QHBoxLayout()
        title = QLabel("NETWORK TELEMETRY")
        title.setStyleSheet(f"color: {_CYAN}; font-size: 11px; font-weight: 700; letter-spacing: 2px; font-family: Consolas;")
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(PulseOrb(8, QColor(_CYAN)))
        layout.addLayout(hdr)
        layout.addWidget(HUDDivider(color=QColor(_CYAN), opacity=0.3))

        stats_row = QHBoxLayout()
        self.dl_lbl = QLabel("DL: 0 KB/s")
        self.dl_lbl.setStyleSheet(f"color: {_CYAN}; font-size: 11px; font-family: Consolas; font-weight: bold;")
        
        self.ul_lbl = QLabel("UL: 0 KB/s")
        self.ul_lbl.setStyleSheet(f"color: {_GOLD}; font-size: 11px; font-family: Consolas; font-weight: bold;")
        
        stats_row.addWidget(self.dl_lbl)
        stats_row.addStretch()
        stats_row.addWidget(self.ul_lbl)
        layout.addLayout(stats_row)

        self.graph = NetworkGraph()
        layout.addWidget(self.graph)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_metrics)
        self.timer.start(1000)

    def _update_metrics(self):
        curr_io = psutil.net_io_counters()
        dl = curr_io.bytes_recv - self.last_io.bytes_recv
        ul = curr_io.bytes_sent - self.last_io.bytes_sent
        self.last_io = curr_io

        def format_speed(bytes_per_sec):
            if bytes_per_sec > 1024 * 1024: return f"{bytes_per_sec / (1024*1024):.1f} MB/s"
            return f"{bytes_per_sec / 1024:.1f} KB/s"

        self.dl_lbl.setText(f"DL: {format_speed(dl)}")
        self.ul_lbl.setText(f"UL: {format_speed(ul)}")
        self.graph.update_data(dl, ul)


# ── SignalRGB Control Card ──────────────────────────────────────────────────

class SignalRGBCard(HUDCard):
    def __init__(self, parent=None):
        super().__init__(corner_size=12, accent_color=_CYAN, parent=parent)
        self.setFixedSize(265, 140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        title_lbl = QLabel("CHROMA CONTROL")
        title_lbl.setStyleSheet(f"color: {_CYAN}; font-size: 11px; font-weight: 700; letter-spacing: 2px; font-family: Consolas;")
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        hdr.addWidget(PulseOrb(8, QColor(_CYAN)))
        layout.addLayout(hdr)

        layout.addWidget(HUDDivider(color=QColor(_CYAN), opacity=0.3))

        sub = QLabel("SignalRGB system illumination")
        sub.setStyleSheet(f"color: {_MUTED}; font-size: 11px; font-family: Consolas;")
        layout.addWidget(sub)

        btns = QHBoxLayout()
        btns.setSpacing(10)

        self.cyber_btn = QPushButton("CYBER RAIN")
        self.cyber_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(0, 212, 255, 0.12); color: {_CYAN}; border: 1px solid rgba(0, 212, 255, 0.35); border-radius: 8px; padding: 7px 10px; font-weight: 700; font-size: 11px; font-family: Consolas; letter-spacing: 1px; }}
            QPushButton:hover {{ background-color: rgba(0, 212, 255, 0.25); border: 1px solid rgba(0, 212, 255, 0.6); }}
        """)
        self.cyber_btn.clicked.connect(lambda: self._apply_effect("Cyber Rain"))

        self.fire_btn = QPushButton("NEON FIRE")
        self.fire_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255, 59, 48, 0.12); color: {_RED}; border: 1px solid rgba(255, 59, 48, 0.35); border-radius: 8px; padding: 7px 10px; font-weight: 700; font-size: 11px; font-family: Consolas; letter-spacing: 1px; }}
            QPushButton:hover {{ background-color: rgba(255, 59, 48, 0.25); border: 1px solid rgba(255, 59, 48, 0.6); }}
        """)
        self.fire_btn.clicked.connect(lambda: self._apply_effect("Neon Fire"))

        btns.addWidget(self.cyber_btn)
        btns.addWidget(self.fire_btn)
        layout.addLayout(btns)

    def _apply_effect(self, effect_name):
        import threading
        thread = threading.Thread(target=signalrgb_client.apply_effect, args=(effect_name,), daemon=True)
        thread.start()


# ── Daily Directive Card ─────────────────────────────────────────────────────

class DailyDirectiveCard(HUDCard):
    def __init__(self, parent=None):
        super().__init__(corner_size=12, accent_color=_GOLD, parent=parent)
        self.setFixedSize(265, 140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        title_lbl = QLabel("SYSTEM DIRECTIVE")
        title_lbl.setStyleSheet(f"color: {_GOLD}; font-size: 11px; font-weight: 700; letter-spacing: 2px; font-family: Consolas;")
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        hdr.addWidget(PulseOrb(8, QColor(_GOLD)))
        layout.addLayout(hdr)

        layout.addWidget(HUDDivider(color=QColor(_GOLD), opacity=0.3))

        self.quote_lbl = QLabel()
        self.quote_lbl.setWordWrap(True)
        self.quote_lbl.setStyleSheet(f"color: {_TEXT}; font-size: 12px; font-style: italic; font-family: 'Segoe UI', sans-serif; padding: 2px;")
        
        self.author_lbl = QLabel()
        self.author_lbl.setAlignment(Qt.AlignRight)
        self.author_lbl.setStyleSheet(f"color: {_MUTED}; font-size: 10px; font-weight: bold; font-family: Consolas; letter-spacing: 1px;")

        self._set_daily_quote()
        layout.addWidget(self.quote_lbl)
        layout.addWidget(self.author_lbl)
        layout.addStretch()

    def _set_daily_quote(self):
        quotes = [
            ("The best way to predict the future is to invent it.", "Alan Kay"),
            ("Any sufficiently advanced technology is indistinguishable from magic.", "Arthur C. Clarke"),
            ("We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "Aristotle"),
            ("It is not that we have a short time to live, but that we waste a lot of it.", "Seneca"),
            ("I am not afraid of computers. I am afraid of the lack of them.", "Isaac Asimov"),
            ("Sometimes it is the people no one can imagine anything of who do the things no one can imagine.", "Alan Turing"),
            ("The limit of your language is the limit of your world.", "Ludwig Wittgenstein"),
            ("We suffer more often in imagination than in reality.", "Seneca")
        ]
        day_of_year = datetime.now().timetuple().tm_yday
        quote, author = quotes[day_of_year % len(quotes)]
        self.quote_lbl.setText(f"\"{quote}\"")
        self.author_lbl.setText(f"— {author.upper()}")


# ── Intelligence Feed ─────────────────────────────────────────────────────────

class IntelItem(QFrame):
    def __init__(self, icon: FIF, title: str, description: str, ts: str, accent: str = _CYAN, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 8, 0, 8)
        row.setSpacing(14)

        ib = QFrame()
        ib.setFixedSize(34, 34)
        ib.setStyleSheet(f"""
            QFrame {{ background-color: rgba(0, 212, 255, 0.07); border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 9px; }}
        """)
        il = QVBoxLayout(ib)
        il.setContentsMargins(0, 0, 0, 0)
        il.setAlignment(Qt.AlignCenter)
        iw = IconWidget(icon)
        iw.setFixedSize(17, 17)
        il.addWidget(iw)
        row.addWidget(ib)

        col = QVBoxLayout()
        col.setSpacing(3)

        top = QHBoxLayout()
        self._title = QLabel(title.upper())
        self._title.setStyleSheet(f"color: {_TEXT}; font-size: 12px; font-weight: 600; letter-spacing: 1px; font-family: Consolas;")
        self._ts = QLabel(ts)
        self._ts.setStyleSheet(f"color: {accent}; font-size: 11px; font-family: Consolas; letter-spacing: 1px;")
        top.addWidget(self._title)
        top.addStretch()
        top.addWidget(self._ts)

        self._desc = QLabel(description)
        self._desc.setStyleSheet(f"color: {_MUTED}; font-size: 12px;")
        self._desc.setWordWrap(True)

        col.addLayout(top)
        col.addWidget(self._desc)
        row.addLayout(col)

    def update_content(self, title, description, ts):
        self._title.setText(title.upper())
        self._desc.setText(description)
        self._ts.setText(ts)

class PriorityCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(96)
        self.setStyleSheet("""
            QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1200, stop:0.3 #2a1f00, stop:1 #1a1200); border: 1px solid rgba(255, 215, 0, 0.35); border-top: 1px solid rgba(255, 215, 0, 0.7); border-radius: 14px; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 0, 22, 0)

        txt = QVBoxLayout()
        txt.setAlignment(Qt.AlignVCenter)
        txt.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        orb = PulseOrb(8, QColor(_GOLD))
        l_pri = QLabel("UPCOMING PRIORITY")
        l_pri.setStyleSheet(f"color: {_GOLD}; font-weight: 700; font-size: 12px; letter-spacing: 2px; font-family: Consolas;")
        top_row.addWidget(orb)
        top_row.addWidget(l_pri)
        top_row.addStretch()

        self._event_lbl = QLabel("NO UPCOMING EVENTS")
        self._event_lbl.setStyleSheet(f"color: {_TEXT}; font-size: 14px; font-weight: 600; font-family: Consolas;")
        self._time_lbl = QLabel("SYSTEM STANDBY")
        self._time_lbl.setStyleSheet(f"color: {_MUTED}; font-size: 12px; font-family: Consolas;")

        txt.addLayout(top_row)
        txt.addWidget(self._event_lbl)
        txt.addWidget(self._time_lbl)

        layout.addLayout(txt)
        layout.addStretch()

        detail_btn = QPushButton("DETAILS")
        detail_btn.setFixedSize(80, 30)
        detail_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255, 215, 0, 0.12); color: {_GOLD}; border: 1px solid rgba(255, 215, 0, 0.4); border-radius: 8px; font-weight: 700; font-size: 11px; font-family: Consolas; letter-spacing: 1px; }}
            QPushButton:hover {{ background-color: rgba(255, 215, 0, 0.22); }}
        """)
        layout.addWidget(detail_btn)

    def update_event(self, events: list):
        now = datetime.now()
        nxt = None
        for ev in events:
            try:
                t = datetime.strptime(ev['start_time'], "%Y-%m-%d %H:%M:%S")
                if t > now and (nxt is None or t < datetime.strptime(nxt['start_time'], "%Y-%m-%d %H:%M:%S")):
                    nxt = ev
            except (KeyError, ValueError):
                continue

        if nxt:
            self._event_lbl.setText(nxt['title'].upper())
            t = datetime.strptime(nxt['start_time'], "%Y-%m-%d %H:%M:%S")
            mins = int((t - now).total_seconds() / 60)
            self._time_lbl.setText(f"T-{mins} MIN" if mins < 60 else f"T-{mins // 60} HR")
        else:
            self._event_lbl.setText("NO UPCOMING EVENTS")
            self._time_lbl.setText("SYSTEM STANDBY")

class IntelligenceFeed(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{ background-color: {_CARD}; border: 1px solid rgba(0, 212, 255, 0.15); border-top: 1px solid rgba(0, 212, 255, 0.45); border-radius: 18px; }}
        """)
        self.setMinimumWidth(420)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 22, 28, 22)
        self._layout.setSpacing(0)

        hdr = QHBoxLayout()
        title = QLabel("SYSTEM INTELLIGENCE")
        title.setStyleSheet(f"color: {_TEXT}; font-size: 16px; font-weight: 700; letter-spacing: 2px; font-family: Consolas;")
        live_tag = QLabel("◉  LIVE")
        live_tag.setStyleSheet(f"""
            color: {_CYAN}; font-size: 11px; font-weight: 700; 
            background-color: rgba(0, 212, 255, 0.08); border: 1px solid rgba(0, 212, 255, 0.3); 
            border-radius: 6px; padding: 3px 10px; font-family: Consolas; letter-spacing: 2px;
        """)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(live_tag)
        self._layout.addLayout(hdr)
        self._layout.addSpacing(14)

        self.focus_item = IntelItem(FIF.TILES, "Daily Focus", "Analyzing timeline...", "NOW")
        self._layout.addWidget(self.focus_item)
        self._layout.addWidget(HUDDivider(opacity=0.25))

        self.news_item = IntelItem(FIF.WIFI, "Intel Alert", "Syncing intelligence streams...", "NOW")
        self._layout.addWidget(self.news_item)
        self._layout.addWidget(HUDDivider(opacity=0.25))

        self.devices_item = IntelItem(FIF.IOT, "Node Network", "Scanning local devices...", "NOW")
        self._layout.addWidget(self.devices_item)

        self._layout.addStretch()

        self.priority = PriorityCard()
        self._layout.addWidget(self.priority)

        self._scan = ScanLineWidget(self.width(), self.height(), parent=self)
        self._scan.lower()
        self._scan.raise_()

        self._corners = HUDCornerWidget(self.width(), self.height(), QColor(_CYAN), 18, self)
        self._corners.raise_()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._scan.resize(self.width(), self.height())
        self._corners.resize(self.width(), self.height())
        self._scan.raise_()
        self._corners.raise_()

    def update_news(self, news):
        if news: self.news_item.update_content("Intel Alert", news[0]['title'], "JUST NOW")
        else: self.news_item.update_content("Intel Alert", "No active streams.", "NOW")

    def update_devices(self, devices):
        n = len(devices) if devices else 0
        on = sum(1 for d in devices if d.get('is_on')) if devices else 0
        if n: self.devices_item.update_content("Node Network", f"{n} devices online — {on} active.", "LIVE")
        else: self.devices_item.update_content("Node Network", "No nodes found on network.", "NOW")

    def update_focus(self, tasks):
        active = [t for t in tasks if not t.get('completed')]
        if active: self.focus_item.update_content("Daily Focus", f"{len(active)} active objective{'s' if len(active) != 1 else ''} pending.", "NOW")
        else: self.focus_item.update_content("Daily Focus", "All objectives complete. System nominal.", "NOW")


# ── Data loader ───────────────────────────────────────────────────────────────

class DashboardLoader(QThread):
    finished = Signal(dict)

    def run(self):
        try:
            tasks = task_manager.get_tasks()
            news  = news_manager.get_briefing(use_ai=False)
            devices = []
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                dd = loop.run_until_complete(kasa_manager.discover_devices())
                loop.close()
                devices = list(dd.values()) if isinstance(dd, dict) else dd
            except Exception as e:
                pass
            events = calendar_manager.get_events(datetime.now().strftime("%Y-%m-%d"))
            self.finished.emit({"tasks": tasks, "news": news, "devices": devices, "events": events})
        except Exception:
            self.finished.emit({"tasks": [], "news": [], "devices": [], "events": []})


class JARVISStatCard(HUDCard):
    """Compact stat card."""
    navigate_requested = Signal(str)
    def __init__(self, icon: FIF, title: str, count: str, route_key: str = None, accent_color: str = _CYAN, parent=None):
        super().__init__(corner_size=12, accent_color=accent_color, parent=parent)
        self.setFixedSize(265, 106)
        self.route_key = route_key
        if route_key: self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 20, 16)

        left = QVBoxLayout()
        left.setSpacing(12)
        ib = QFrame()
        ib.setFixedSize(36, 36)
        ib.setStyleSheet("QFrame { background-color: rgba(0, 212, 255, 0.08); border: 1px solid rgba(0, 212, 255, 0.25); border-radius: 10px; }")
        ib_l = QVBoxLayout(ib)
        ib_l.setContentsMargins(0, 0, 0, 0)
        ib_l.setAlignment(Qt.AlignCenter)
        iw = IconWidget(icon)
        iw.setFixedSize(18, 18)
        ib_l.addWidget(iw)

        lbl = QLabel(title.upper())
        lbl.setStyleSheet(f"color: {_MUTED}; font-size: 11px; font-weight: 500; letter-spacing: 1px; font-family: Consolas;")

        left.addWidget(ib)
        left.addWidget(lbl)
        layout.addLayout(left)
        layout.addStretch()

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignRight | Qt.AlignTop)
        right.setSpacing(8)

        orb_row = QHBoxLayout()
        orb_row.setAlignment(Qt.AlignRight)
        self._orb = PulseOrb(10, QColor(accent_color))
        orb_row.addWidget(self._orb)
        right.addLayout(orb_row)
        right.addStretch()

        self.num_lbl = QLabel(str(count))
        self.num_lbl.setAlignment(Qt.AlignRight)
        self.num_lbl.setStyleSheet(f"color: {accent_color}; font-size: 32px; font-weight: 700; font-family: Consolas;")
        right.addWidget(self.num_lbl)
        layout.addLayout(right)

    def set_count(self, count): self.num_lbl.setText(str(count))
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if self.route_key: self.navigate_requested.emit(self.route_key)


# ── Main DashboardView ────────────────────────────────────────────────────────

class DashboardView(QWidget):
    navigate_to = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardView")

        main = QVBoxLayout(self)
        main.setContentsMargins(40, 36, 40, 36)
        main.setSpacing(20)

        # Top Header
        self.header = JARVISHeader()
        main.addWidget(self.header)

        # Global Uplink Strip 
        self.global_uplink = GlobalUplinkWidget()
        main.addWidget(self.global_uplink)

        main.addWidget(HUDDivider(opacity=0.35))
        main.addSpacing(8)

        content = QHBoxLayout()
        content.setSpacing(24)

        # Wrap left column in a scroll area to prevent overlapping
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet("background: transparent; border: none;")
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        left_widget = QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left = QVBoxLayout(left_widget)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(14)

        self.planner_stat = JARVISStatCard(FIF.CALENDAR, "Planner Agenda", "--", "plannerInterface")
        self.planner_stat.navigate_requested.connect(self._on_navigate)
        left.addWidget(self.planner_stat)

        self.devices_stat = JARVISStatCard(FIF.IOT, "Active Nodes", "--", "homeInterface", accent_color=_GOLD)
        self.devices_stat.navigate_requested.connect(self._on_navigate)
        left.addWidget(self.devices_stat)

        self.telemetry_card = NetworkTelemetryCard()
        left.addWidget(self.telemetry_card)

        self.rgb_card = SignalRGBCard()
        left.addWidget(self.rgb_card)

        self.directive_card = DailyDirectiveCard()
        left.addWidget(self.directive_card)

        left.addStretch()
        left_scroll.setWidget(left_widget)
        
        # Add to Layout
        content.addWidget(left_scroll)

        self.feed = IntelligenceFeed()
        content.addWidget(self.feed, 1)

        main.addLayout(content)

        self.loader = None
        QTimer.singleShot(120, self._start_loading)

    def _start_loading(self):
        if self.loader and self.loader.isRunning(): return
        self.loader = DashboardLoader(self)
        self.loader.finished.connect(self._on_data_loaded)
        self.loader.finished.connect(self.loader.deleteLater)
        self.loader.start()

    def _on_data_loaded(self, data):
        tasks = data.get("tasks", [])
        news = data.get("news", [])
        devices = data.get("devices", [])
        events = data.get("events", [])

        active = [t for t in tasks if not t.get('completed')]
        self.planner_stat.set_count(len(active))
        self.devices_stat.set_count(len(devices))

        self.feed.update_news(news)
        self.feed.update_devices(devices)
        self.feed.update_focus(tasks)
        self.feed.priority.update_event(events)

    def _on_navigate(self, route_key: str):
        self.navigate_to.emit(route_key)