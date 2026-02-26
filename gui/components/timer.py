from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
)
from PySide6.QtCore import Qt, QTimer

class TimerComponent(QWidget):
    """JARVIS Countdown & Performance Metric Component."""
    
    def __init__(self):
        super().__init__()
        self.duration = 25 * 60  
        self.remaining = self.duration
        self.is_running = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)
        self.timer.setInterval(1000)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) 
        
        # --- Timer Card (HUD Style) ---
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 22, 40, 0.85);
                border-radius: 14px;
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-top: 1px solid rgba(0, 212, 255, 0.5);
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        lbl = QLabel("COUNTDOWN METRIC")
        lbl.setStyleSheet("color: #00d4ff; font-family: Consolas; font-size: 13px; font-weight: bold; letter-spacing: 2px; background: transparent; border: none;")
        header_layout.addWidget(lbl)
        header_layout.addStretch()
        
        self.edit_btn = QPushButton("⚙")
        self.edit_btn.setToolTip("Configure Metric")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedSize(28, 28)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 212, 255, 0.05);
                color: #8b9bb4;
                border-radius: 14px;
                border: 1px solid rgba(0, 212, 255, 0.2);
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(0, 212, 255, 0.2); 
                color: #00d4ff;
            }
        """)
        self.edit_btn.clicked.connect(self._edit_duration)
        header_layout.addWidget(self.edit_btn)
        card_layout.addLayout(header_layout)
        
        # Timer Display
        self.time_display = QLabel("25:00")
        self.time_display.setAlignment(Qt.AlignCenter)
        self.time_display.setStyleSheet("""
            color: #00d4ff; 
            font-size: 48px; 
            font-weight: bold;
            font-family: Consolas;
            background: transparent;
            border: none;
        """)
        card_layout.addWidget(self.time_display)
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.start_btn = QPushButton("INITIALIZE")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFixedHeight(40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 212, 255, 0.15); 
                color: #00d4ff;
                border: 1px solid rgba(0, 212, 255, 0.5);
                border-radius: 8px;
                font-family: Consolas;
                font-weight: bold;
                font-size: 14px;
                letter-spacing: 2px;
            }
            QPushButton:hover { background: rgba(0, 212, 255, 0.3); }
            QPushButton:pressed { background: rgba(0, 212, 255, 0.5); }
        """)
        self.start_btn.clicked.connect(self._toggle_timer)
        controls_layout.addWidget(self.start_btn, 1) 
        
        self.reset_btn = QPushButton("⟲")
        self.reset_btn.setToolTip("Reset Metric")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setFixedSize(40, 40)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 59, 48, 0.1);
                color: #ff3b30;
                border-radius: 8px;
                font-size: 20px;
                border: 1px solid rgba(255, 59, 48, 0.3);
            }
            QPushButton:hover { background: rgba(255, 59, 48, 0.25); }
        """)
        self.reset_btn.clicked.connect(self._reset_timer)
        controls_layout.addWidget(self.reset_btn)
        
        card_layout.addLayout(controls_layout)
        layout.addWidget(card)
        layout.addStretch()

    def _toggle_timer(self):
        if self.is_running:
            self.timer.stop()
            self.start_btn.setText("RESUME")
            self.is_running = False
        else:
            self.timer.start()
            self.start_btn.setText("HALT")
            self.is_running = True
            
    def _reset_timer(self):
        self.timer.stop()
        self.is_running = False
        self.start_btn.setText("INITIALIZE")
        self.remaining = self.duration
        self._update_display()
    
    def set_and_start(self, seconds: int, label: str = None):
        if seconds <= 0: return
        self.duration = seconds
        self.remaining = seconds
        self._update_display()
        self.timer.start()
        self.start_btn.setText("HALT")
        self.is_running = True

    def _edit_duration(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSpinBox, QLabel, QPushButton
        from PySide6.QtCore import Qt
        
        d = QDialog(self)
        d.setWindowTitle("Configure Metric")
        d.setFixedSize(320, 180)
        d.setStyleSheet("""
            QDialog { background-color: #050a12; color: #c0c8d8; border: 1px solid #00d4ff; }
            QLabel { color: #00d4ff; font-family: Consolas; font-size: 14px; letter-spacing: 1px;}
            QSpinBox {
                background: rgba(0, 212, 255, 0.05);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 4px;
                color: #c0c8d8;
                font-family: Consolas;
                font-size: 16px;
                padding: 4px;
            }
            QPushButton {
                background-color: rgba(0, 212, 255, 0.15);
                color: #00d4ff;
                border: 1px solid rgba(0, 212, 255, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                font-family: Consolas;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover { background-color: rgba(0, 212, 255, 0.3); }
        """)
        
        layout = QVBoxLayout(d)
        title = QLabel("SET DURATION")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        spin_layout = QHBoxLayout()
        spin_layout.setSpacing(10)
        
        current_h = self.duration // 3600
        current_m = (self.duration % 3600) // 60
        current_s = self.duration % 60
        
        def create_spinner(val, max_val, label_text):
            v_layout = QVBoxLayout()
            s = QSpinBox()
            s.setRange(0, max_val)
            s.setValue(val)
            s.setButtonSymbols(QSpinBox.NoButtons)
            s.setAlignment(Qt.AlignCenter)
            s.setFixedSize(60, 40)
            l = QLabel(label_text)
            l.setAlignment(Qt.AlignCenter)
            l.setStyleSheet("font-size: 12px; color: #8b9bb4;")
            v_layout.addWidget(s)
            v_layout.addWidget(l)
            spin_layout.addLayout(v_layout)
            return s
            
        h_spin = create_spinner(current_h, 99, "HRS")
        m_spin = create_spinner(current_m, 59, "MIN")
        s_spin = create_spinner(current_s, 59, "SEC")
        layout.addLayout(spin_layout)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("APPLY")
        save_btn.clicked.connect(d.accept)
        cancel_btn = QPushButton("ABORT")
        cancel_btn.clicked.connect(d.reject)
        cancel_btn.setStyleSheet("background: rgba(255, 59, 48, 0.1); border: 1px solid rgba(255, 59, 48, 0.4); color: #ff3b30;")
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        if d.exec():
            h, m, s = h_spin.value(), m_spin.value(), s_spin.value()
            total = (h * 3600) + (m * 60) + s
            if total > 0:
                self.duration = total
                self._reset_timer()

    def _update_timer(self):
        if self.remaining > 0:
            self.remaining -= 1
            self._update_display()
        else:
            self.timer.stop()
            self.is_running = False
            self.start_btn.setText("INITIALIZE")
            self.remaining = self.duration
            self._update_display()

    def _update_display(self):
        h = self.remaining // 3600
        m = (self.remaining % 3600) // 60
        s = self.remaining % 60
        
        if h > 0:
            self.time_display.setText(f"{h:02d}:{m:02d}:{s:02d}")
            self.time_display.setStyleSheet("color: #00d4ff; font-size: 36px; font-weight: bold; font-family: Consolas; background: transparent; border: none;")
        else:
            self.time_display.setText(f"{m:02d}:{s:02d}")
            self.time_display.setStyleSheet("color: #00d4ff; font-size: 48px; font-weight: bold; font-family: Consolas; background: transparent; border: none;")