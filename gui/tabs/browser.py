from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Slot, Signal
from PySide6.QtGui import QPixmap, QImage, QColor

from qfluentwidgets import LineEdit, ScrollArea
from gui.components.thinking_expander import ThinkingExpander
from gui.components.jarvis_hud import HUDCornerWidget, PulseOrb, HUDDivider
from core.agent import BrowserAgent

class BrowserTab(QWidget):
    """
    JARVIS Web Surveillance & Automation Tab.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BrowserTab")
        self.agent_thread = QThread()
        self.agent = None 
        
        self._setup_ui()
        self._setup_agent()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(24)

        # ── Left Column: Browser Viewport (HUD Frame) ────────────────
        viewport_container = QFrame(self)
        viewport_container.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 22, 40, 0.85);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-top: 1px solid rgba(0, 212, 255, 0.5);
                border-radius: 14px;
            }
        """)
        viewport_layout = QVBoxLayout(viewport_container)
        viewport_layout.setContentsMargins(15, 15, 15, 15)
        
        # HUD Corners
        self._corners = HUDCornerWidget(0, 0, QColor("#00d4ff"), 18, viewport_container)
        
        lbl_row = QHBoxLayout()
        vp_icon = PulseOrb(10, QColor("#00d4ff"))
        lbl_row.addWidget(vp_icon)
        
        viewport_label = QLabel("LIVE SURVEILLANCE FEED")
        viewport_label.setStyleSheet("color: #00d4ff; font-family: Consolas; font-weight: 700; letter-spacing: 2px; font-size: 13px; border: none; background: transparent;")
        lbl_row.addWidget(viewport_label)
        lbl_row.addStretch()
        viewport_layout.addLayout(lbl_row)
        
        viewport_layout.addWidget(HUDDivider(opacity=0.3))
        
        self.image_label = QLabel("NO FEED SIGNAL")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #050a12; border: 1px solid rgba(0,212,255,0.1); border-radius: 8px; color: #8b9bb4; font-family: Consolas; font-size: 14px; letter-spacing: 2px;")
        self.image_label.setMinimumSize(640, 360)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        viewport_layout.addWidget(self.image_label)
        
        layout.addWidget(viewport_container, stretch=3)

        # ── Right Column: Controls & Terminal ───────────────────────
        controls_container = QWidget()
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(14)

        # Status
        stat_row = QHBoxLayout()
        self.status_pulse = PulseOrb(10, QColor("#8b9bb4"))
        stat_row.addWidget(self.status_pulse)
        self.status_label = QLabel("STATUS: IDLE")
        self.status_label.setStyleSheet("color: #c0c8d8; font-family: Consolas; font-weight: 700; letter-spacing: 1px;")
        stat_row.addWidget(self.status_label)
        stat_row.addStretch()
        controls_layout.addLayout(stat_row)

        # Thinking Stream
        self.thinking_expander = ThinkingExpander(self)
        controls_layout.addWidget(self.thinking_expander)

        # Action Log Terminal
        log_label = QLabel("SYSTEM ACTION LOG")
        log_label.setStyleSheet("color: #00d4ff; font-family: Consolas; letter-spacing: 1px; font-weight: bold; font-size: 12px;")
        controls_layout.addWidget(log_label)
        
        self.action_log = QTextEdit()
        self.action_log.setReadOnly(True)
        self.action_log.setStyleSheet("""
            QTextEdit {
                background-color: rgba(5, 10, 18, 0.9);
                border: 1px solid rgba(0, 212, 255, 0.15);
                border-radius: 8px;
                color: #00d4ff;
                font-family: Consolas;
                font-size: 12px;
                padding: 10px;
            }
        """)
        controls_layout.addWidget(self.action_log)

        # Input Area
        input_layout = QHBoxLayout()
        self.url_input = LineEdit()
        self.url_input.setPlaceholderText("Enter target directive...")
        self.url_input.setStyleSheet("font-family: Consolas;")
        input_layout.addWidget(self.url_input)
        
        self.go_btn = QPushButton("EXECUTE")
        self.go_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 212, 255, 0.15);
                color: #00d4ff;
                border: 1px solid rgba(0, 212, 255, 0.5);
                border-radius: 8px;
                font-family: Consolas;
                font-weight: 700;
                letter-spacing: 1px;
                padding: 6px 16px;
                height: 32px;
            }
            QPushButton:hover { background-color: rgba(0, 212, 255, 0.25); }
        """)
        self.go_btn.clicked.connect(self._on_execute)
        input_layout.addWidget(self.go_btn)
        
        controls_layout.addLayout(input_layout)
        layout.addWidget(controls_container, stretch=2)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Assuming the first child is the container
        container = self.findChild(QFrame)
        if hasattr(self, '_corners') and container:
            self._corners.resize(container.width(), container.height())

    def _setup_agent(self):
        from core.settings_store import settings
        model_name = settings.get("models.web_agent", "qwen3-vl:4b")
        self.agent = BrowserAgent(model_name=model_name) 
        self.agent.moveToThread(self.agent_thread)
        
        self.agent.screenshot_updated.connect(self._update_screenshot)
        self.agent.thinking_update.connect(self._update_thinking)
        self.agent.action_updated.connect(self._log_action)
        self.agent.finished.connect(self._on_finished)
        self.agent.error_occurred.connect(self._on_error)
        self.run_signal.connect(self.agent.start_task)
        self.agent_thread.start()

    def _on_execute(self):
        instruction = self.url_input.text()
        if not instruction.strip(): return
            
        self.status_label.setText("STATUS: EXECUTING DIRECTIVE...")
        self.status_label.setStyleSheet("color: #00d4ff; font-family: Consolas; font-weight: 700; letter-spacing: 1px;")
        self.status_pulse.set_color(QColor("#00d4ff"))
        self.go_btn.setEnabled(False)
        self.action_log.clear()
        self.run_signal.emit(instruction)

    run_signal = Signal(str)

    def closeEvent(self, event):
        if self.agent:
            self.agent.stop()
            self.agent.cleanup()
        self.agent_thread.quit()
        self.agent_thread.wait()
        super().closeEvent(event)

    @Slot(QImage)
    def _update_screenshot(self, image):
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)

    @Slot(str)
    def _update_thinking(self, text):
        self.thinking_expander.add_text(text)

    @Slot(str)
    def _log_action(self, text):
        self.action_log.append(f"> {text}")

    @Slot()
    def _on_finished(self):
        self.status_label.setText("STATUS: SEQUENCE COMPLETE")
        self.status_label.setStyleSheet("color: #ffd700; font-family: Consolas; font-weight: 700; letter-spacing: 1px;")
        self.status_pulse.set_color(QColor("#ffd700"))
        self.go_btn.setEnabled(True)
        self.thinking_expander.complete()

    @Slot(str)
    def _on_error(self, err):
        self.status_label.setText("STATUS: ERROR DETECTED")
        self.status_label.setStyleSheet("color: #ff3b30; font-family: Consolas; font-weight: 700; letter-spacing: 1px;")
        self.status_pulse.set_color(QColor("#ff3b30"))
        self.action_log.append(f"[!] CRITICAL: {err}")
        self.go_btn.setEnabled(True)