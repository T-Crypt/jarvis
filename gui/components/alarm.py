from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer, QTime
from qfluentwidgets import MessageBoxBase, SubtitleLabel
from core.tasks import task_manager
import datetime

class AddAlarmDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("INITIALIZE ALERT", self)
        self.titleLabel.setStyleSheet("color: #00d4ff; font-family: Consolas; letter-spacing: 1px;")
        self.viewLayout.addWidget(self.titleLabel)
        
        time_layout = QHBoxLayout()
        time_layout.setSpacing(5)
        
        self.spin_style = """
            QSpinBox {
                background-color: rgba(0, 212, 255, 0.05);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 5px;
                color: #c0c8d8;
                font-family: Consolas;
                font-size: 16px;
                padding: 5px;
            }
            QSpinBox:hover {
                background-color: rgba(0, 212, 255, 0.15);
            }
        """
        
        from PySide6.QtWidgets import QSpinBox, QComboBox
        
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(1, 12)
        self.hour_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.hour_spin.setAlignment(Qt.AlignCenter)
        self.hour_spin.setFixedSize(60, 40)
        self.hour_spin.setStyleSheet(self.spin_style)
        
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.minute_spin.setAlignment(Qt.AlignCenter)
        self.minute_spin.setFixedSize(60, 40)
        self.minute_spin.setStyleSheet(self.spin_style)
        self.minute_spin.setPrefix("") 
        
        self.ampm_combo = QComboBox()
        self.ampm_combo.addItems(["AM", "PM"])
        self.ampm_combo.setFixedSize(70, 40)
        self.ampm_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(0, 212, 255, 0.05);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 5px;
                color: #c0c8d8;
                font-family: Consolas;
                font-size: 16px;
                padding-left: 10px;
            }
            QComboBox::drop-down { border: none; }
        """)
        
        colon = QLabel(":")
        colon.setStyleSheet("color: #00d4ff; font-size: 20px; font-weight: bold;")
        
        time_layout.addStretch()
        time_layout.addWidget(self.hour_spin)
        time_layout.addWidget(colon)
        time_layout.addWidget(self.minute_spin)
        time_layout.addWidget(self.ampm_combo)
        time_layout.addStretch()
        
        self.viewLayout.addLayout(time_layout)
        
        now = QTime.currentTime()
        h, m = now.hour(), now.minute()
        am = True
        
        if h >= 12:
            am = False
            if h > 12: h -= 12
        elif h == 0: h = 12
            
        self.hour_spin.setValue(h)
        self.minute_spin.setValue(m)
        self.ampm_combo.setCurrentIndex(0 if am else 1)
        
        self.yesButton.setText("ARM ALARM")
        self.cancelButton.setText("ABORT")
        self.widget.setStyleSheet("background-color: #050a12; border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 12px;")

    def get_time(self):
        h = self.hour_spin.value()
        m = self.minute_spin.value()
        is_pm = self.ampm_combo.currentText() == "PM"
        
        if is_pm and h != 12: h += 12
        elif not is_pm and h == 12: h = 0
        return QTime(h, m)

class AlarmComponent(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_alarms()
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._check_alarms)
        self.check_timer.start(5000) 

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 22, 40, 0.85);
                border-radius: 12px;
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-top: 1px solid rgba(0, 212, 255, 0.5);
            }
        """)
        self.card_layout = QVBoxLayout(card)
        self.card_layout.setContentsMargins(20, 20, 20, 20)
        self.card_layout.setSpacing(15)
        
        header = QHBoxLayout()
        lbl = QLabel("SYSTEM ALERTS")
        lbl.setStyleSheet("color: #00d4ff; font-family: Consolas; font-size: 13px; font-weight: bold; letter-spacing: 2px; background: transparent; border: none;")
        header.addWidget(lbl)
        header.addStretch()
        
        add_btn = QPushButton("⊕")
        add_btn.setFixedSize(28, 28)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 212, 255, 0.1);
                color: #00d4ff;
                border: 1px solid rgba(0, 212, 255, 0.4);
                border-radius: 14px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover { background-color: rgba(0, 212, 255, 0.25); border: 1px solid #00d4ff; }
        """)
        add_btn.clicked.connect(self._add_alarm_dialog)
        header.addWidget(add_btn)
        
        self.card_layout.addLayout(header)
        
        self.alarm_list = QListWidget()
        self.alarm_list.setStyleSheet("background: transparent; border: none; outline: none;")
        self.card_layout.addWidget(self.alarm_list)
        layout.addWidget(card)
        
    def _add_alarm_dialog(self):
        w = AddAlarmDialog(self.window())
        if w.exec():
            qtime = w.get_time()
            time_str = qtime.toString("HH:mm")
            task_manager.add_alarm(time_str, "Alert")
            self._load_alarms()

    def _load_alarms(self):
        self.alarm_list.clear()
        alarms = task_manager.get_alarms()
        for a in alarms:
            self._create_alarm_item(a)
    
    def reload(self): self._load_alarms()

    def _create_alarm_item(self, alarm):
        item = QListWidgetItem()
        from PySide6.QtCore import QSize
        item.setSizeHint(QSize(0, 45))
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        time_24 = alarm['time']
        try:
            display_time = datetime.datetime.strptime(time_24, "%H:%M").strftime("%I:%M %p").lstrip("0")
        except:
            display_time = time_24
            
        lbl = QLabel(display_time)
        lbl.setStyleSheet("color: #c0c8d8; font-family: Consolas; font-size: 16px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(lbl)
        layout.addStretch()
        
        del_btn = QPushButton("×")
        del_btn.setFixedSize(24, 24)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton { color: #6b7a95; background: transparent; border: none; font-size: 20px; font-weight: bold; }
            QPushButton:hover { color: #ff3b30; }
        """)
        a_id = alarm['id']
        del_btn.clicked.connect(lambda checked=False, aid=a_id: self._delete_alarm(aid))
        layout.addWidget(del_btn)
        
        self.alarm_list.addItem(item)
        self.alarm_list.setItemWidget(item, widget)

    def _delete_alarm(self, alarm_id):
        task_manager.delete_alarm(alarm_id)
        self._load_alarms()

    def _check_alarms(self):
        now = datetime.datetime.now().strftime("%H:%M")
        alarms = task_manager.get_alarms()
        for a in alarms:
            if a['time'] == now: pass