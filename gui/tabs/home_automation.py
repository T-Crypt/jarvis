"""
JARVIS Home Automation Tab — glassmorphism device cards.
"""

import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QPushButton
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QColor
from qfluentwidgets import (
    TitleLabel, BodyLabel,
    FluentIcon as FIF, IconWidget, SwitchButton, Slider,
    ColorPickerButton, ToolButton
)

from core.kasa_control import kasa_manager
from gui.components.jarvis_hud import HUDCornerWidget, PulseOrb, HUDDivider

_CYAN   = "#00d4ff"
_GOLD   = "#ffd700"
_RED    = "#ff3b30"
_BG     = "#050a12"
_CARD   = "#0a1628"
_CARD2  = "#0d1f3c"
_TEXT   = "#c0c8d8"
_MUTED  = "#6b7a95"


# ── Threads (unchanged logic) ─────────────────────────────────────────────────

class DataFetchThread(QThread):
    devices_found = Signal(list)

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            devices_dict = loop.run_until_complete(kasa_manager.discover_devices())
            loop.close()
            devices = list(devices_dict.values()) if isinstance(devices_dict, dict) else devices_dict
            self.devices_found.emit(devices)
        except Exception as e:
            print(f"[HomeAutomation] Discovery error: {e}")
            self.devices_found.emit([])


class ActionThread(QThread):
    finished = Signal(bool)

    def __init__(self, action, ip, *args):
        super().__init__()
        self.action = action
        self.ip = ip
        self.args = tuple(a for a in args if not hasattr(a, 'turn_on'))

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = False
            if self.action == "on":
                success = loop.run_until_complete(kasa_manager.turn_on(self.ip, dev=None))
            elif self.action == "off":
                success = loop.run_until_complete(kasa_manager.turn_off(self.ip, dev=None))
            elif self.action == "brightness":
                level = self.args[0] if self.args else 100
                success = loop.run_until_complete(
                    kasa_manager.set_brightness(self.ip, level, dev=None)
                )
            elif self.action == "color":
                h, s, v = self.args[0], self.args[1], self.args[2]
                success = loop.run_until_complete(
                    kasa_manager.set_hsv(self.ip, h, s, v, dev=None)
                )
            loop.close()
            self.finished.emit(success)
        except Exception as e:
            print(f"[HomeAutomation] Action '{self.action}' error: {e}")
            self.finished.emit(False)


# ── Device Card ───────────────────────────────────────────────────────────────

class DeviceCard(QFrame):
    """
    Glassmorphism JARVIS device card.
    """
    def __init__(self, device_info, parent=None):
        super().__init__(parent)
        self.device_info = device_info
        self.ip = device_info['ip']
        self.is_bulb  = ("Bulb" in device_info.get("type", "") or
                         device_info.get("brightness") is not None)
        is_on = device_info.get('is_on', False)

        self.setFixedSize(300, 165)

        # Card style — cyan when on, muted when off
        self._on_style = f"""
            QFrame {{
                background-color: {_CARD};
                border: 1px solid rgba(0, 212, 255, 0.25);
                border-top: 1px solid rgba(0, 212, 255, 0.55);
                border-radius: 18px;
            }}
        """
        self._off_style = f"""
            QFrame {{
                background-color: #080f1e;
                border: 1px solid rgba(0, 212, 255, 0.08);
                border-top: 1px solid rgba(0, 212, 255, 0.20);
                border-radius: 18px;
            }}
        """
        self.setStyleSheet(self._on_style if is_on else self._off_style)

        # HUD corners
        self._corners = HUDCornerWidget(300, 165, QColor(_CYAN), 14, self)
        self._corners.raise_()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(0)

        # ── Header row ────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(10)

        # Icon
        icon_type = FIF.BRIGHTNESS if self.is_bulb else FIF.TILES
        ib = QFrame()
        ib.setFixedSize(38, 38)
        ib.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 212, 255, 0.07);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 11px;
            }}
        """)
        il = QVBoxLayout(ib)
        il.setContentsMargins(0, 0, 0, 0)
        il.setAlignment(Qt.AlignCenter)
        iw = IconWidget(icon_type)
        iw.setFixedSize(18, 18)
        il.addWidget(iw)
        header.addWidget(ib)
        header.addStretch()

        # Toggle
        self.toggle = SwitchButton()
        self.toggle.setChecked(is_on)
        self.toggle.checkedChanged.connect(self._on_toggle)
        header.addWidget(self.toggle)
        layout.addLayout(header)
        layout.addSpacing(10)

        # ── Device name ───────────────────────────────────────────────
        name = QLabel(device_info['alias'].upper())
        name.setStyleSheet(
            f"color: {_TEXT}; font-weight: 700; font-size: 13px; "
            "letter-spacing: 1px; font-family: Consolas;"
        )
        layout.addWidget(name)

        # Status row
        status_row = QHBoxLayout()
        self._orb = PulseOrb(8, QColor(_CYAN) if is_on else QColor(_MUTED))
        self._status_lbl = QLabel("ONLINE" if is_on else "STANDBY")
        self._status_lbl.setStyleSheet(
            f"color: {_CYAN if is_on else _MUTED}; font-size: 10px; "
            "font-family: Consolas; letter-spacing: 2px;"
        )
        status_row.addWidget(self._orb)
        status_row.addWidget(self._status_lbl)
        status_row.addStretch()
        layout.addLayout(status_row)
        layout.addSpacing(10)

        layout.addWidget(HUDDivider(opacity=0.2))
        layout.addSpacing(8)

        # ── Controls ──────────────────────────────────────────────────
        ctrl = QHBoxLayout()
        ctrl.setSpacing(10)

        if self.is_bulb:
            self.slider = Slider(Qt.Horizontal)
            self.slider.setRange(0, 100)
            val = device_info.get('brightness')
            self.slider.setValue(val if val is not None else 100)
            self.slider.sliderReleased.connect(self._on_brightness)
            ctrl.addWidget(self.slider, 1)

        if device_info.get('is_color'):
            self.color_btn = ColorPickerButton(QColor("#ffffff"), "")
            self.color_btn.setFixedSize(30, 26)
            self.color_btn.colorChanged.connect(self._on_color)
            ctrl.addWidget(self.color_btn)

        if self.is_bulb or device_info.get('is_color'):
            layout.addLayout(ctrl)
        else:
            layout.addStretch()

    def _set_state(self, is_on: bool):
        """Update card visual state."""
        self.setStyleSheet(self._on_style if is_on else self._off_style)
        self._orb.set_color(QColor(_CYAN) if is_on else QColor(_MUTED))
        self._status_lbl.setText("ONLINE" if is_on else "STANDBY")
        self._status_lbl.setStyleSheet(
            f"color: {_CYAN if is_on else _MUTED}; font-size: 10px; "
            "font-family: Consolas; letter-spacing: 2px;"
        )

    def _on_toggle(self, checked):
        self._set_state(checked)
        t = ActionThread("on" if checked else "off", self.ip)
        t.start()
        self._worker = t

    def _on_brightness(self):
        t = ActionThread("brightness", self.ip, self.slider.value())
        t.start()
        self._worker_b = t

    def _on_color(self, color: QColor):
        h = color.hsvHue()
        s = int(color.hsvSaturationF() * 100)
        v = int(color.valueF() * 100)
        t = ActionThread("color", self.ip, h, s, v)
        t.start()
        self._worker_c = t


# ── Room filter buttons ───────────────────────────────────────────────────────

def _filter_btn_style(active: bool) -> str:
    if active:
        return f"""
            QPushButton {{
                background-color: rgba(0, 212, 255, 0.15);
                color: {_CYAN};
                border: 1px solid rgba(0, 212, 255, 0.5);
                border-radius: 14px;
                padding: 7px 18px;
                font-weight: 700;
                font-size: 11px;
                font-family: Consolas;
                letter-spacing: 1px;
            }}
        """
    return f"""
        QPushButton {{
            background-color: rgba(0, 212, 255, 0.04);
            color: {_MUTED};
            border: 1px solid rgba(0, 212, 255, 0.12);
            border-radius: 14px;
            padding: 7px 18px;
            font-weight: 600;
            font-size: 11px;
            font-family: Consolas;
            letter-spacing: 1px;
        }}
        QPushButton:hover {{
            background-color: rgba(0, 212, 255, 0.09);
            color: {_TEXT};
        }}
    """


# ── Main Tab ──────────────────────────────────────────────────────────────────

class HomeAutomationTab(QWidget):
    """
    JARVIS Environmental Control Dashboard.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homeAutomationView")
        self.all_devices = []
        self.room_groups = {}
        self.current_filter = "All"
        self._filter_btns = []

        main = QVBoxLayout(self)
        main.setContentsMargins(40, 36, 40, 36)
        main.setSpacing(24)

        self._setup_header(main)
        self._setup_filters(main)

        # Device grid scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll.viewport().setStyleSheet("background: transparent;")

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.grid_widget)
        main.addWidget(self.scroll)

        # Load
        if kasa_manager.devices:
            self._on_devices_loaded(list(kasa_manager.devices.values()))
        else:
            self._load_devices()

    def _setup_header(self, parent):
        row = QHBoxLayout()

        col = QVBoxLayout()
        col.setSpacing(4)

        title = QLabel("ENVIRONMENTAL CONTROL")
        title.setStyleSheet(
            f"color: {_TEXT}; font-size: 24px; font-weight: 700; "
            "letter-spacing: 3px; font-family: Consolas;"
        )
        sub = QLabel("Localized automation interface · Kasa network")
        sub.setStyleSheet(f"color: {_MUTED}; font-size: 13px;")
        col.addWidget(title)
        col.addWidget(sub)

        row.addLayout(col)
        row.addStretch()

        refresh_btn = ToolButton(FIF.SYNC, self)
        refresh_btn.setToolTip("Refresh Devices")
        refresh_btn.clicked.connect(self._load_devices)
        refresh_btn.setStyleSheet(f"""
            ToolButton {{
                background-color: rgba(0, 212, 255, 0.07);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 8px;
            }}
            ToolButton:hover {{
                background-color: rgba(0, 212, 255, 0.14);
            }}
        """)
        row.addWidget(refresh_btn)
        row.addSpacing(12)

        # Status badge
        self._status_badge = QLabel("◉  SCANNING")
        self._status_badge.setStyleSheet(f"""
            color: {_CYAN};
            background-color: rgba(0, 212, 255, 0.07);
            border: 1px solid rgba(0, 212, 255, 0.25);
            border-radius: 14px;
            padding: 7px 16px;
            font-weight: 700;
            font-size: 11px;
            font-family: Consolas;
            letter-spacing: 2px;
        """)
        row.addWidget(self._status_badge)

        parent.addLayout(row)
        parent.addWidget(HUDDivider(opacity=0.3))

    def _setup_filters(self, parent):
        self.filter_row = QHBoxLayout()
        self.filter_row.setSpacing(10)
        parent.addLayout(self.filter_row)

    def _update_filters(self):
        # Clear existing
        while self.filter_row.count():
            item = self.filter_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._filter_btns = []
        rooms = ["All"] + sorted(self.room_groups.keys())

        for i, room in enumerate(rooms):
            btn = QPushButton(room.upper())
            btn.setCheckable(True)
            active = (i == 0)
            btn.setChecked(active)
            btn.setStyleSheet(_filter_btn_style(active))
            btn.clicked.connect(lambda _, r=room, b=btn: self._filter_grid(r, b))
            self._filter_btns.append(btn)
            self.filter_row.addWidget(btn)

        self.filter_row.addStretch()

    def _filter_grid(self, room_name: str, clicked_btn=None):
        # Update button styles
        for btn in self._filter_btns:
            active = (btn is clicked_btn)
            btn.setChecked(active)
            btn.setStyleSheet(_filter_btn_style(active))

        # Clear grid
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        devices = self.all_devices if room_name == "All" else self.room_groups.get(room_name, [])
        row = col = 0
        max_cols = 3
        for dev in devices:
            card = DeviceCard(dev)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _load_devices(self):
        if hasattr(self, 'loader') and self.loader and self.loader.isRunning():
            return
        self._status_badge.setText("◉  SCANNING")
        self.loader = DataFetchThread()
        self.loader.devices_found.connect(self._on_devices_loaded)
        self.loader.finished.connect(self.loader.deleteLater)
        self.loader.start()

    def _on_devices_loaded(self, devices):
        self.all_devices = devices
        self.room_groups = {}

        keywords = {
            "Office":      ["office", "desk", "work", "pc", "monitor"],
            "Living Room": ["living", "sofa", "tv", "lounge"],
            "Kitchen":     ["kitchen", "dining", "cook"],
            "Bedroom":     ["bed", "sleep", "night"],
            "Exterior":    ["exterior", "garden", "patio", "porch", "garage"],
            "Hallway":     ["hall", "corridor", "stairs"],
        }

        for dev in devices:
            alias = dev['alias'].lower()
            assigned = False
            for room, keys in keywords.items():
                if any(k in alias for k in keys):
                    self.room_groups.setdefault(room, []).append(dev)
                    assigned = True
                    break
            if not assigned:
                self.room_groups.setdefault("Other", []).append(dev)

        n = len(devices)
        self._status_badge.setText(f"◉  {n} DEVICE{'S' if n != 1 else ''} ONLINE")

        self._update_filters()
        self._filter_grid("All", self._filter_btns[0] if self._filter_btns else None)