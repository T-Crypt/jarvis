"""
JARVIS Dashboard — Iron Man HUD aesthetic.

Replaces the Aura-themed dashboard with full JARVIS glassmorphism:
  - Arc reactor header widget
  - Scan-line animation on the intelligence feed
  - HUD corner brackets on all cards
  - Pulse orbs for live status
  - Gold priority card with gradient
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QDate, QTime, QThread, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QBrush

from qfluentwidgets import (
    CardWidget, BodyLabel, StrongBodyLabel,
    FluentIcon as FIF, IconWidget, TransparentToolButton
)

from core.news import news_manager
from core.tasks import task_manager
from core.calendar_manager import calendar_manager
from core.kasa_control import kasa_manager
from datetime import datetime
import asyncio

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
_CARD   = "#0a1628"
_CARD2  = "#0d1f3c"
_TEXT   = "#c0c8d8"
_MUTED  = "#6b7a95"
_BORDER = "rgba(0, 212, 255, 0.15)"


# ── Reusable card base ────────────────────────────────────────────────────────

class HUDCard(QFrame):
    """
    Base card with cyan top-border accent and optional HUD corner brackets.
    """
    def __init__(self, corner_size: int = 14, accent_color: str = _CYAN,
                 parent=None):
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


# ── Greeting Header ──────────────────────────────────────────────────────────

class WeatherWorker(QThread):
    finished = Signal(dict)
    def run(self):
        data = weather_manager.get_weather()
        self.finished.emit(data or {})


class JARVISHeader(QWidget):
    """
    JARVIS-styled header: Arc Reactor + greeting text + live data tickers.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(140)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(30)

        # ── Arc Reactor ───────────────────────────────────────────────
        self.reactor = ArcReactorWidget(size=110)
        outer.addWidget(self.reactor, 0, Qt.AlignVCenter)

        # ── Text block ────────────────────────────────────────────────
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.setContentsMargins(0, 0, 0, 0)

        self.sub_lbl = QLabel("JARVIS  ·  JUST A RATHER VERY INTELLIGENT SYSTEM")
        self.sub_lbl.setStyleSheet(
            f"color: {_MUTED}; font-size: 11px; letter-spacing: 3px; font-family: Consolas;"
        )

        self.greeting_lbl = QLabel("GOOD MORNING")
        self.greeting_lbl.setStyleSheet(
            f"color: {_CYAN}; font-size: 38px; font-weight: 700;"
            " font-family: 'Segoe UI', 'SF Pro Display', sans-serif;"
        )

        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet(
            f"color: {_MUTED}; font-size: 13px; font-family: Consolas; letter-spacing: 1px;"
        )

        text_col.addWidget(self.sub_lbl)
        text_col.addWidget(self.greeting_lbl)
        text_col.addWidget(self.date_lbl)

        outer.addLayout(text_col, 1)

        # ── Right: data tickers + time bubble ─────────────────────────
        right_col = QVBoxLayout()
        right_col.setSpacing(6)
        right_col.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        # Time bubble
        time_frame = QFrame()
        time_frame.setFixedSize(160, 72)
        time_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {_CARD};
                border: 1px solid rgba(0, 212, 255, 0.25);
                border-top: 1px solid rgba(0, 212, 255, 0.6);
                border-radius: 16px;
            }}
        """)
        tf_layout = QVBoxLayout(time_frame)
        tf_layout.setAlignment(Qt.AlignCenter)
        tf_layout.setContentsMargins(0, 0, 0, 0)

        self.clock_lbl = QLabel("00:00 AM")
        self.clock_lbl.setAlignment(Qt.AlignCenter)
        self.clock_lbl.setStyleSheet(
            f"color: {_CYAN}; font-size: 22px; font-weight: 700; font-family: Consolas;"
        )
        tf_layout.addWidget(self.clock_lbl)

        # Weather bubble
        wx_frame = QFrame()
        wx_frame.setFixedSize(160, 72)
        wx_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {_CARD};
                border: 1px solid rgba(0, 212, 255, 0.20);
                border-top: 1px solid rgba(0, 212, 255, 0.50);
                border-radius: 16px;
            }}
        """)
        wx_layout = QVBoxLayout(wx_frame)
        wx_layout.setAlignment(Qt.AlignCenter)
        wx_layout.setContentsMargins(0, 4, 0, 4)
        wx_layout.setSpacing(2)

        self.wx_icon  = QLabel("⛅")
        self.wx_icon.setAlignment(Qt.AlignCenter)
        self.wx_icon.setStyleSheet("font-size: 20px; background: transparent;")

        self.wx_temp  = QLabel("--°F")
        self.wx_temp.setAlignment(Qt.AlignCenter)
        self.wx_temp.setStyleSheet(
            f"color: {_TEXT}; font-size: 14px; font-weight: 600; font-family: Consolas;"
        )

        self.wx_cond  = QLabel("LOADING")
        self.wx_cond.setAlignment(Qt.AlignCenter)
        self.wx_cond.setStyleSheet(
            f"color: {_MUTED}; font-size: 10px; letter-spacing: 2px; font-family: Consolas;"
        )

        wx_layout.addWidget(self.wx_icon)
        wx_layout.addWidget(self.wx_temp)
        wx_layout.addWidget(self.wx_cond)

        right_col.addWidget(time_frame)
        right_col.addWidget(wx_frame)
        outer.addLayout(right_col)

        # ── Timers ────────────────────────────────────────────────────
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
        self.date_lbl.setText(
            "[ " + QDate.currentDate().toString("dddd, MMMM d").upper() + " ]"
        )
        self.clock_lbl.setText(QTime.currentTime().toString("h:mm AP"))

    def _fetch_weather(self):
        self._wx_worker = WeatherWorker()
        self._wx_worker.finished.connect(self._on_weather)
        self._wx_worker.start()

    def _on_weather(self, data):
        if not data:
            self.wx_cond.setText("OFFLINE")
            return
        temp = data.get("temp", "--")
        code = data.get("code", -1)
        self.wx_temp.setText(f"{int(temp)}°F")
        mapping = {
            0: ("☀️", "CLEAR"),
            1: ("🌤️", "MOSTLY CLEAR"),
            2: ("⛅", "PARTLY CLOUDY"),
            3: ("☁️", "OVERCAST"),
        }
        if code in mapping:
            icon, text = mapping[code]
        elif code in [45, 48]:
            icon, text = "🌫️", "FOG"
        elif 51 <= code <= 65:
            icon, text = "🌧️", "RAIN"
        elif 71 <= code <= 77:
            icon, text = "❄️", "SNOW"
        elif code >= 95:
            icon, text = "⚡", "STORM"
        else:
            icon, text = "🌡️", "UNKNOWN"
        self.wx_icon.setText(icon)
        self.wx_cond.setText(text)


# ── Stat Cards ────────────────────────────────────────────────────────────────

class JARVISStatCard(HUDCard):
    """
    Compact stat card — icon + label + big number, clickable.
    """
    navigate_requested = Signal(str)

    def __init__(self, icon: FIF, title: str, count: str,
                 route_key: str = None,
                 accent_color: str = _CYAN,
                 parent=None):
        super().__init__(corner_size=12, accent_color=accent_color, parent=parent)
        self.setFixedSize(265, 106)
        self.route_key = route_key
        if route_key:
            self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 20, 16)

        # Left: icon bubble + label
        left = QVBoxLayout()
        left.setSpacing(12)

        ib = QFrame()
        ib.setFixedSize(36, 36)
        ib.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 212, 255, 0.08);
                border: 1px solid rgba(0, 212, 255, 0.25);
                border-radius: 10px;
            }}
        """)
        ib_l = QVBoxLayout(ib)
        ib_l.setContentsMargins(0, 0, 0, 0)
        ib_l.setAlignment(Qt.AlignCenter)
        iw = IconWidget(icon)
        iw.setFixedSize(18, 18)
        ib_l.addWidget(iw)

        lbl = QLabel(title.upper())
        lbl.setStyleSheet(
            f"color: {_MUTED}; font-size: 11px; font-weight: 500; "
            "letter-spacing: 1px; font-family: Consolas;"
        )

        left.addWidget(ib)
        left.addWidget(lbl)
        layout.addLayout(left)
        layout.addStretch()

        # Right: pulsing status orb + number
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
        self.num_lbl.setStyleSheet(
            f"color: {accent_color}; font-size: 32px; font-weight: 700; font-family: Consolas;"
        )
        right.addWidget(self.num_lbl)

        layout.addLayout(right)

    def set_count(self, count):
        self.num_lbl.setText(str(count))

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if self.route_key:
            self.navigate_requested.emit(self.route_key)


# ── Home Scenes ───────────────────────────────────────────────────────────────

class HomeScenesCard(HUDCard):
    """
    Quick-access scene buttons with JARVIS styling.
    """
    def __init__(self, parent=None):
        super().__init__(corner_size=14, accent_color=_GOLD, parent=parent)
        self.setFixedSize(265, 148)
        self._devices = []
        self._action_thread = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        title_lbl = QLabel("HOME SCENES")
        title_lbl.setStyleSheet(
            f"color: {_GOLD}; font-size: 11px; font-weight: 700; letter-spacing: 2px; font-family: Consolas;"
        )
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        hdr.addWidget(PulseOrb(8, QColor(_GOLD)))
        layout.addLayout(hdr)

        layout.addWidget(HUDDivider(color=QColor(_GOLD), opacity=0.3))

        sub = QLabel("Instant environmental adjustments")
        sub.setStyleSheet(f"color: {_MUTED}; font-size: 11px;")
        layout.addWidget(sub)

        # Buttons
        btns = QHBoxLayout()
        btns.setSpacing(10)

        self.focus_btn = QPushButton("⬛  FOCUS")
        self.focus_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 215, 0, 0.12);
                color: {_GOLD};
                border: 1px solid rgba(255, 215, 0, 0.35);
                border-radius: 8px;
                padding: 7px 10px;
                font-weight: 700;
                font-size: 11px;
                font-family: Consolas;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 215, 0, 0.22);
                border: 1px solid rgba(255, 215, 0, 0.6);
            }}
        """)
        self.focus_btn.clicked.connect(self._on_focus_mode)

        self.relax_btn = QPushButton("◎  RELAX")
        self.relax_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 212, 255, 0.08);
                color: {_CYAN};
                border: 1px solid rgba(0, 212, 255, 0.25);
                border-radius: 8px;
                padding: 7px 10px;
                font-weight: 700;
                font-size: 11px;
                font-family: Consolas;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 212, 255, 0.16);
                border: 1px solid rgba(0, 212, 255, 0.5);
            }}
        """)
        self.relax_btn.clicked.connect(self._on_relax_mode)

        btns.addWidget(self.focus_btn)
        btns.addWidget(self.relax_btn)
        layout.addLayout(btns)

    def set_devices(self, devices):
        self._devices = devices

    def _on_focus_mode(self):
        if not self._devices:
            return
        self._run_action(self._focus_action)

    def _on_relax_mode(self):
        if not self._devices:
            return
        self._run_action(self._relax_action)

    def _run_action(self, fn):
        from PySide6.QtCore import QThread

        class T(QThread):
            def __init__(self, f):
                super().__init__()
                self.f = f
            def run(self):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.f())
                    loop.close()
                except Exception as e:
                    print(f"[Scenes] {e}")

        try:
            if self._action_thread and self._action_thread.isRunning():
                self._action_thread.wait()
        except RuntimeError:
            pass
        self._action_thread = T(fn)
        self._action_thread.finished.connect(lambda: setattr(self, '_action_thread', None))
        self._action_thread.start()

    async def _focus_action(self):
        for d in self._devices:
            try:
                await kasa_manager.turn_off(d['ip'], dev=d.get('obj'))
            except Exception as e:
                print(f"[Focus] {e}")

    async def _relax_action(self):
        for d in self._devices:
            try:
                if d.get('brightness') is not None:
                    await kasa_manager.set_brightness(d['ip'], 40, dev=d.get('obj'))
                    await kasa_manager.turn_on(d['ip'], dev=d.get('obj'))
                else:
                    await kasa_manager.turn_on(d['ip'], dev=d.get('obj'))
            except Exception as e:
                print(f"[Relax] {e}")


# ── Intelligence Feed ─────────────────────────────────────────────────────────

class IntelItem(QFrame):
    """
    Single row in the Intelligence Feed — JARVIS styled.
    """
    def __init__(self, icon: FIF, title: str, description: str, ts: str,
                 accent: str = _CYAN, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 8, 0, 8)
        row.setSpacing(14)

        # Icon
        ib = QFrame()
        ib.setFixedSize(34, 34)
        ib.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 212, 255, 0.07);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 9px;
            }}
        """)
        il = QVBoxLayout(ib)
        il.setContentsMargins(0, 0, 0, 0)
        il.setAlignment(Qt.AlignCenter)
        iw = IconWidget(icon)
        iw.setFixedSize(17, 17)
        il.addWidget(iw)
        row.addWidget(ib)

        # Content
        col = QVBoxLayout()
        col.setSpacing(3)

        top = QHBoxLayout()
        self._title = QLabel(title.upper())
        self._title.setStyleSheet(
            f"color: {_TEXT}; font-size: 12px; font-weight: 600; letter-spacing: 1px; font-family: Consolas;"
        )
        self._ts = QLabel(ts)
        self._ts.setStyleSheet(
            f"color: {accent}; font-size: 10px; font-family: Consolas; letter-spacing: 1px;"
        )
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
    """
    Gold priority card with gradient — next upcoming event.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(96)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0   #1a1200,
                    stop:0.3 #2a1f00,
                    stop:1   #1a1200
                );
                border: 1px solid rgba(255, 215, 0, 0.35);
                border-top: 1px solid rgba(255, 215, 0, 0.7);
                border-radius: 14px;
            }
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
        l_pri.setStyleSheet(
            f"color: {_GOLD}; font-weight: 700; font-size: 11px; "
            "letter-spacing: 2px; font-family: Consolas;"
        )
        top_row.addWidget(orb)
        top_row.addWidget(l_pri)
        top_row.addStretch()

        self._event_lbl = QLabel("No upcoming events")
        self._event_lbl.setStyleSheet(
            f"color: {_TEXT}; font-size: 14px; font-weight: 600;"
        )
        self._time_lbl = QLabel("Enjoy your free time.")
        self._time_lbl.setStyleSheet(f"color: {_MUTED}; font-size: 12px;")

        txt.addLayout(top_row)
        txt.addWidget(self._event_lbl)
        txt.addWidget(self._time_lbl)

        layout.addLayout(txt)
        layout.addStretch()

        detail_btn = QPushButton("DETAILS")
        detail_btn.setFixedSize(80, 30)
        detail_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 215, 0, 0.12);
                color: {_GOLD};
                border: 1px solid rgba(255, 215, 0, 0.4);
                border-radius: 8px;
                font-weight: 700;
                font-size: 10px;
                font-family: Consolas;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 215, 0, 0.22);
            }}
        """)
        layout.addWidget(detail_btn)

    def update_event(self, events: list):
        now = datetime.now()
        nxt = None
        for ev in events:
            try:
                t = datetime.strptime(ev['start_time'], "%Y-%m-%d %H:%M:%S")
                if t > now and (nxt is None or t < datetime.strptime(
                        nxt['start_time'], "%Y-%m-%d %H:%M:%S")):
                    nxt = ev
            except (KeyError, ValueError):
                continue

        if nxt:
            self._event_lbl.setText(nxt['title'])
            t = datetime.strptime(nxt['start_time'], "%Y-%m-%d %H:%M:%S")
            mins = int((t - now).total_seconds() / 60)
            self._time_lbl.setText(
                f"T-{mins} MIN" if mins < 60 else f"T-{mins // 60} HR"
            )
        else:
            self._event_lbl.setText("No upcoming events")
            self._time_lbl.setText("Standby mode.")


class IntelligenceFeed(QFrame):
    """
    Main intel feed card with animated scan line overlay.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {_CARD};
                border: 1px solid rgba(0, 212, 255, 0.15);
                border-top: 1px solid rgba(0, 212, 255, 0.45);
                border-radius: 18px;
            }}
        """)
        self.setMinimumWidth(420)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 22, 28, 22)
        self._layout.setSpacing(0)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("SYSTEM INTELLIGENCE")
        title.setStyleSheet(
            f"color: {_TEXT}; font-size: 16px; font-weight: 700; "
            "letter-spacing: 2px; font-family: Consolas;"
        )
        live_tag = QLabel("◉  LIVE")
        live_tag.setStyleSheet(
            f"color: {_CYAN}; font-size: 10px; font-weight: 700; "
            f"background-color: rgba(0, 212, 255, 0.08); "
            f"border: 1px solid rgba(0, 212, 255, 0.3); "
            "border-radius: 6px; padding: 3px 10px; font-family: Consolas; letter-spacing: 2px;"
        )
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(live_tag)
        self._layout.addLayout(hdr)
        self._layout.addSpacing(14)

        # Items
        self.focus_item   = IntelItem(FIF.TILES, "Daily Focus",
                                      "Analyzing schedule…", "NOW")
        self._layout.addWidget(self.focus_item)
        self._layout.addWidget(HUDDivider(opacity=0.25))

        self.news_item    = IntelItem(FIF.WIFI, "Intel Alert",
                                      "Syncing intelligence…", "NOW")
        self._layout.addWidget(self.news_item)
        self._layout.addWidget(HUDDivider(opacity=0.25))

        self.devices_item = IntelItem(FIF.IOT, "Smart Home",
                                      "Scanning devices…", "NOW")
        self._layout.addWidget(self.devices_item)

        self._layout.addStretch()

        # Priority card
        self.priority = PriorityCard()
        self._layout.addWidget(self.priority)

        # Scan line overlay — positioned on top of all content
        self._scan = ScanLineWidget(self.width(), self.height(), parent=self)
        self._scan.lower()
        self._scan.raise_()

        # HUD corners
        self._corners = HUDCornerWidget(
            self.width(), self.height(), QColor(_CYAN), 18, self
        )
        self._corners.raise_()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._scan.resize(self.width(), self.height())
        self._corners.resize(self.width(), self.height())
        self._scan.raise_()
        self._corners.raise_()

    def update_news(self, news):
        if news:
            self.news_item.update_content("Intel Alert", news[0]['title'], "JUST NOW")
        else:
            self.news_item.update_content("Intel Alert", "No active streams.", "NOW")

    def update_devices(self, devices):
        n  = len(devices) if devices else 0
        on = sum(1 for d in devices if d.get('is_on')) if devices else 0
        if n:
            self.devices_item.update_content(
                "Smart Home", f"{n} devices online — {on} active.", "LIVE"
            )
        else:
            self.devices_item.update_content(
                "Smart Home", "No Kasa devices found on network.", "NOW"
            )

    def update_focus(self, tasks):
        active = [t for t in tasks if not t.get('completed')]
        if active:
            count = len(active)
            self.focus_item.update_content(
                "Daily Focus",
                f"{count} active task{'s' if count != 1 else ''} pending.",
                "NOW"
            )
        else:
            self.focus_item.update_content(
                "Daily Focus", "All tasks completed. System nominal.", "NOW"
            )


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
                print(f"[Dashboard] Kasa: {e}")

            today_str = datetime.now().strftime("%Y-%m-%d")
            events = calendar_manager.get_events(today_str)

            self.finished.emit({
                "tasks": tasks, "news": news,
                "devices": devices, "events": events
            })
        except Exception as e:
            print(f"[Dashboard] Loader error: {e}")
            self.finished.emit({"tasks": [], "news": [], "devices": [], "events": []})


# ── Main DashboardView ────────────────────────────────────────────────────────

class DashboardView(QWidget):
    """
    JARVIS System Intelligence Dashboard.
    """
    navigate_to = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardView")

        main = QVBoxLayout(self)
        main.setContentsMargins(40, 36, 40, 36)
        main.setSpacing(28)

        # Header
        self.header = JARVISHeader()
        main.addWidget(self.header)

        # Thin divider
        main.addWidget(HUDDivider(opacity=0.35))

        # 2-column content
        content = QHBoxLayout()
        content.setSpacing(24)

        # Left column
        left = QVBoxLayout()
        left.setSpacing(14)

        self.planner_stat = JARVISStatCard(
            FIF.CALENDAR, "Planner Agenda", "--", "plannerInterface"
        )
        self.planner_stat.navigate_requested.connect(self._on_navigate)
        left.addWidget(self.planner_stat)

        self.devices_stat = JARVISStatCard(
            FIF.IOT, "Active Devices", "--", "homeInterface",
            accent_color=_GOLD
        )
        self.devices_stat.navigate_requested.connect(self._on_navigate)
        left.addWidget(self.devices_stat)

        self.news_stat = JARVISStatCard(
            FIF.TILES, "Unread Intel", "--", "briefingInterface",
            accent_color=_CYAN
        )
        self.news_stat.navigate_requested.connect(self._on_navigate)
        left.addWidget(self.news_stat)

        self.home_scenes = HomeScenesCard()
        left.addWidget(self.home_scenes)

        left.addStretch()
        content.addLayout(left)

        # Right column — intelligence feed
        self.feed = IntelligenceFeed()
        content.addWidget(self.feed, 1)

        main.addLayout(content)

        self._devices  = []
        self.loader    = None
        QTimer.singleShot(120, self._start_loading)

    def _start_loading(self):
        if self.loader and self.loader.isRunning():
            return
        self.loader = DashboardLoader(self)
        self.loader.finished.connect(self._on_data_loaded)
        self.loader.finished.connect(self.loader.deleteLater)
        self.loader.start()

    def _on_data_loaded(self, data):
        tasks   = data.get("tasks", [])
        news    = data.get("news", [])
        devices = data.get("devices", [])
        events  = data.get("events", [])

        self._devices = devices
        self.home_scenes.set_devices(devices)

        active = [t for t in tasks if not t.get('completed')]
        self.planner_stat.set_count(len(active))
        self.news_stat.set_count(len(news))
        self.devices_stat.set_count(len(devices))

        self.feed.update_news(news)
        self.feed.update_devices(devices)
        self.feed.update_focus(tasks)
        self.feed.priority.update_event(events)

    def _on_navigate(self, route_key: str):
        self.navigate_to.emit(route_key)