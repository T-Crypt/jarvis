from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QColor, QPainter

from gui.components.jarvis_hud import HUDCornerWidget, PulseOrb, HUDDivider
from core.local_media import local_media
import asyncio
import random
import threading

class AudioVisualizer(QWidget):
    """JARVIS style animated audio visualizer."""
    def __init__(self, num_bars=32, parent=None):
        super().__init__(parent)
        self.num_bars = num_bars
        self.bar_heights = [0.0] * num_bars
        self.target_heights = [0.0] * num_bars
        self.is_playing = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_bars)
        self.timer.start(50)  
        self.setFixedHeight(80)
        
    def set_playing(self, playing: bool):
        self.is_playing = playing
        
    def update_bars(self):
        for i in range(self.num_bars):
            if self.is_playing:
                if random.random() < 0.3:
                    self.target_heights[i] = random.uniform(0.1, 1.0)
            else:
                self.target_heights[i] = 0.05  
            
            self.bar_heights[i] += (self.target_heights[i] - self.bar_heights[i]) * 0.3
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        bar_w = w / self.num_bars
        padding = 3
        
        for i in range(self.num_bars):
            bh = self.bar_heights[i] * h
            bx = i * bar_w + padding / 2
            by = h - bh
            
            painter.setBrush(QColor(0, 212, 255, 180))
            painter.setPen(Qt.NoPen)
            painter.drawRect(int(bx), int(by), int(bar_w - padding), int(bh))


class MediaFetchThread(QThread):
    track_updated = Signal(dict)
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            data = loop.run_until_complete(local_media.get_current_state())
            loop.close()
            self.track_updated.emit(data if data else {})
        except Exception:
            self.track_updated.emit({})


class MediaTab(QWidget):
    """JARVIS Audio Telemetry & Media Control (100% Offline)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mediaInterface")
        self._setup_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._fetch_track)
        self.timer.start(1000)
        self._fetch_track()

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(40, 36, 40, 36)
        main.setSpacing(24)

        hdr = QHBoxLayout()
        hdr_title = QLabel("LOCAL AUDIO TELEMETRY")
        hdr_title.setStyleSheet("color: #00d4ff; font-size: 24px; font-weight: 700; font-family: Consolas; letter-spacing: 3px;")
        hdr.addWidget(hdr_title)
        hdr.addStretch()
        
        self.status_pulse = PulseOrb(12, QColor("#8b9bb4"))
        hdr.addWidget(self.status_pulse)
        self.status_lbl = QLabel("SYSTEM AUDIO: STANDBY")
        self.status_lbl.setStyleSheet("color: #8b9bb4; font-family: Consolas; font-weight: bold; letter-spacing: 1px;")
        hdr.addWidget(self.status_lbl)
        main.addLayout(hdr)
        main.addWidget(HUDDivider(opacity=0.3))

        card = QFrame()
        card.setFixedSize(500, 280)
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 22, 40, 0.85);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-top: 1px solid rgba(0, 212, 255, 0.5);
                border-radius: 16px;
            }
        """)
        self._corners = HUDCornerWidget(500, 280, QColor("#00d4ff"), 18, card)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 25, 30, 25)
        card_layout.setSpacing(15)

        self.track_lbl = QLabel("NO SIGNAL DETECTED")
        self.track_lbl.setAlignment(Qt.AlignCenter)
        self.track_lbl.setStyleSheet("color: #c0c8d8; font-size: 22px; font-weight: 700; font-family: 'Segoe UI'; border: none; background: transparent;")
        
        self.artist_lbl = QLabel("Awaiting Audio Stream...")
        self.artist_lbl.setAlignment(Qt.AlignCenter)
        self.artist_lbl.setStyleSheet("color: #00d4ff; font-size: 14px; font-family: Consolas; letter-spacing: 2px; border: none; background: transparent;")
        
        card_layout.addWidget(self.track_lbl)
        card_layout.addWidget(self.artist_lbl)
        
        self.visualizer = AudioVisualizer()
        card_layout.addWidget(self.visualizer)
        card_layout.addStretch()

        ctrl_layout = QHBoxLayout()
        ctrl_layout.setAlignment(Qt.AlignCenter)
        ctrl_layout.setSpacing(20)

        btn_style = """
            QPushButton {
                background-color: rgba(0, 212, 255, 0.1);
                color: #00d4ff;
                border: 1px solid rgba(0, 212, 255, 0.4);
                border-radius: 25px;
                font-size: 18px;
            }
            QPushButton:hover { background-color: rgba(0, 212, 255, 0.3); }
            QPushButton:pressed { background-color: rgba(0, 212, 255, 0.5); }
        """

        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(50, 50)
        self.prev_btn.setStyleSheet(btn_style)
        self.prev_btn.clicked.connect(lambda: self._exec_media_cmd(local_media.previous_track))

        self.play_btn = QPushButton("⏯")
        self.play_btn.setFixedSize(60, 60)
        self.play_btn.setStyleSheet(btn_style.replace("border-radius: 25px;", "border-radius: 30px; border: 2px solid #00d4ff;"))
        self.play_btn.clicked.connect(lambda: self._exec_media_cmd(local_media.toggle_play_pause))

        self.next_btn = QPushButton("⏭")
        self.next_btn.setFixedSize(50, 50)
        self.next_btn.setStyleSheet(btn_style)
        self.next_btn.clicked.connect(lambda: self._exec_media_cmd(local_media.next_track))

        ctrl_layout.addWidget(self.prev_btn)
        ctrl_layout.addWidget(self.play_btn)
        ctrl_layout.addWidget(self.next_btn)
        
        card_layout.addLayout(ctrl_layout)
        
        wrapper = QHBoxLayout()
        wrapper.addWidget(card, 0, Qt.AlignCenter)
        main.addLayout(wrapper)
        main.addStretch()

    def _fetch_track(self):
        # SAFETY GUARD: Prevent overlapping thread crashes!
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            return
            
        self.worker = MediaFetchThread()
        self.worker.track_updated.connect(self._update_display)
        self.worker.finished.connect(self.worker.deleteLater) # Clear memory properly
        self.worker.start()

    def _update_display(self, data):
        if not data:
            self.status_lbl.setText("SYSTEM AUDIO: STANDBY")
            self.status_lbl.setStyleSheet("color: #8b9bb4;")
            self.status_pulse.set_color(QColor("#8b9bb4"))
            self.track_lbl.setText("NO SIGNAL DETECTED")
            self.artist_lbl.setText("Awaiting Audio Stream...")
            self.visualizer.set_playing(False)
            return

        is_playing = data.get('is_playing', False)
        track_name = data.get('title', 'Unknown Track')
        artist_name = data.get('artist', 'Unknown Artist')

        self.track_lbl.setText(track_name.upper())
        self.artist_lbl.setText(artist_name.upper())
        self.visualizer.set_playing(is_playing)

        if is_playing:
            self.status_lbl.setText("SYSTEM AUDIO: ACTIVE UPLINK")
            self.status_lbl.setStyleSheet("color: #00d4ff;")
            self.status_pulse.set_color(QColor("#00d4ff"))
        else:
            self.status_lbl.setText("SYSTEM AUDIO: PAUSED")
            self.status_lbl.setStyleSheet("color: #ffd700;")
            self.status_pulse.set_color(QColor("#ffd700"))

    def _exec_media_cmd(self, async_func):
        def run_it():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(async_func())
            loop.close()
        threading.Thread(target=run_it, daemon=True).start()
        QTimer.singleShot(500, self._fetch_track)