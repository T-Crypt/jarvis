from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton
)
from PySide6.QtCore import Qt, QDate, QTime, QDateTime
from PySide6.QtGui import QColor

from qfluentwidgets import (
    PushButton, LineEdit, ComboBox, MessageBoxBase, SubtitleLabel
)
from qfluentwidgets.components.date_time.fast_calendar_view import FastCalendarView as CalendarView
from qfluentwidgets.components.date_time.calendar_picker import CalendarPicker
from qfluentwidgets.components.date_time.time_picker import TimePicker

from core.calendar_manager import calendar_manager
from datetime import datetime

class AddEventDialog(MessageBoxBase):
    """Custom Dialog for adding events using Fluent Widgets."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("ADD TIMELINE EVENT", self)
        self.titleLabel.setStyleSheet("color: #00d4ff; font-family: Consolas; letter-spacing: 1px;")
        
        self.viewLayout.addWidget(self.titleLabel)
        
        self.titleEdit = LineEdit(self)
        self.titleEdit.setPlaceholderText("Event Designation")
        self.viewLayout.addWidget(self.titleEdit)
        
        self.datePicker = CalendarPicker(self)
        self.datePicker.setDate(QDate.currentDate())
        self.viewLayout.addWidget(self.datePicker)
        
        self.timePicker = TimePicker(self)
        self.timePicker.setTime(QTime.currentTime())
        self.viewLayout.addWidget(self.timePicker)
        
        self.catCombo = ComboBox(self)
        self.catCombo.addItems(["DIRECTIVE", "PERSONAL", "SYSTEM"])
        self.viewLayout.addWidget(self.catCombo)
        
        self.yesButton.setText("INITIALIZE")
        self.cancelButton.setText("ABORT")
        
        self.widget.setMinimumWidth(350)
        self.widget.setStyleSheet("background-color: #050a12; border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 12px;")
        
    def get_data(self):
        title = self.titleEdit.text()
        date = self.datePicker.date
        time = self.timePicker.time
        cat = self.catCombo.text()
        
        dt = QDateTime(date, time)
        start = dt.toString("yyyy-MM-dd HH:mm:ss")
        end = dt.addSecs(3600).toString("yyyy-MM-dd HH:mm:ss")
        
        return title, start, end, cat

class ScheduleComponent(QWidget):
    """JARVIS Timeline Component."""
    
    def __init__(self):
        super().__init__()
        self.selected_date = QDate.currentDate()
        self._setup_ui()
        self.refresh_events()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # --- Timeline Section ---
        timeline_container = QFrame()
        timeline_container.setStyleSheet("background: transparent;")
        timeline_layout = QVBoxLayout(timeline_container)
        
        # Header
        header_layout = QHBoxLayout()
        self.date_label = QLabel(self.selected_date.toString("dddd, MMMM d").upper())
        self.date_label.setStyleSheet("color: #c0c8d8; font-size: 14px; font-family: Consolas; font-weight: bold; background: transparent; letter-spacing: 1px;")
        header_layout.addWidget(self.date_label)
        header_layout.addStretch()
        
        add_btn = QPushButton("⊕")
        add_btn.setFixedSize(32, 32)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(0, 212, 255, 0.1); 
                color: #00d4ff; 
                border-radius: 16px; 
                border: 1px solid rgba(0, 212, 255, 0.4); 
                font-size: 18px; 
                font-weight: bold;
            }
            QPushButton:hover { 
                background: rgba(0, 212, 255, 0.25); 
                border: 1px solid #00d4ff;
            }
        """)
        add_btn.clicked.connect(self._show_add_event_dialog)
        header_layout.addWidget(add_btn)
        
        timeline_layout.addLayout(header_layout)
        
        # Scrollable Timeline
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.timeline_content = QWidget()
        self.timeline_content.setStyleSheet("background: transparent;")
        self.timeline_layout = QVBoxLayout(self.timeline_content)
        self.timeline_layout.setSpacing(12)
        self.timeline_layout.addStretch()
        
        scroll.setWidget(self.timeline_content)
        timeline_layout.addWidget(scroll, 2) 
        
        layout.addWidget(timeline_container, 2)
        
        # --- Fluent Calendar View ---
        self.calendar = CalendarView()
        self.calendar.hide = lambda: None
        self.calendar.close = lambda: None
        self.calendar.dateChanged.connect(self._on_date_selected)
        
        layout.addWidget(self.calendar, 1)

    def _on_date_selected(self, date):
        self.selected_date = date
        self.date_label.setText(date.toString("dddd, MMMM d").upper())
        self.refresh_events()
        
    def refresh_events(self):
        while self.timeline_layout.count() > 1: 
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        date_str = self.selected_date.toString("yyyy-MM-dd")
        events = calendar_manager.get_events(date_str)
        
        if not events:
            empty = QLabel("NO EVENTS DETECTED")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #6b7a95; padding: 20px; font-family: Consolas; letter-spacing: 2px;")
            self.timeline_layout.insertWidget(0, empty)
        else:
            for event in events:
                self._add_event_card(event)

    def _add_event_card(self, event):
        card = QFrame()
        card.setCursor(Qt.PointingHandCursor)
        
        cat = event['category']
        # JARVIS Palette Mapping
        accent_color = "#00d4ff" if "DIRECTIVE" in cat else "#ffd700" if "PERSONAL" in cat else "#aa66cc"
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 212, 255, 0.03);
                border-radius: 8px;
                border: 1px solid rgba(0, 212, 255, 0.1);
                border-left: 3px solid {accent_color};
            }}
            QFrame:hover {{ 
                background-color: rgba(0, 212, 255, 0.08);
                border: 1px solid rgba(0, 212, 255, 0.3);
            }}
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Time
        start_dt = datetime.strptime(event['start_time'], "%Y-%m-%d %H:%M:%S")
        time_str = start_dt.strftime("%I:%M %p").lstrip("0")
        
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet(f"color: {accent_color}; font-weight: bold; font-family: Consolas; font-size: 13px; background: transparent; border: none;")
        time_lbl.setFixedWidth(75)
        layout.addWidget(time_lbl)
        
        # Details
        details = QVBoxLayout()
        details.setSpacing(4)
        
        title_lbl = QLabel(event['title'].upper())
        title_lbl.setStyleSheet("color: #c0c8d8; font-weight: 600; font-family: Consolas; font-size: 13px; background: transparent; border: none; letter-spacing: 1px;")
        details.addWidget(title_lbl)
        
        cat_lbl = QLabel(cat)
        cat_lbl.setStyleSheet(f"color: {accent_color}; font-size: 10px; font-family: Consolas; letter-spacing: 1px; background: rgba(255,255,255,0.05); padding: 3px 6px; border-radius: 4px; border: none;")
        cat_lbl.setFixedWidth(cat_lbl.sizeHint().width() + 15)
        details.addWidget(cat_lbl)
        
        layout.addLayout(details)
        layout.addStretch()
        
        # Delete button
        del_btn = QPushButton("×")
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet("""
            QPushButton { color: #6b7a95; background: transparent; font-size: 18px; border: none; border-radius: 12px; }
            QPushButton:hover { background: rgba(255, 59, 48, 0.2); color: #ff3b30; }
        """)
        del_btn.clicked.connect(lambda: self._delete_event(event['id']))
        layout.addWidget(del_btn)
        
        self.timeline_layout.insertWidget(self.timeline_layout.count()-1, card)

    def _delete_event(self, event_id):
        calendar_manager.delete_event(event_id)
        self.refresh_events()
        
    def _show_add_event_dialog(self):
        w = AddEventDialog(self.window())
        if w.exec():
            title, start, end, cat = w.get_data()
            if title:
                calendar_manager.add_event(title, start, end, cat)
                self.refresh_events()