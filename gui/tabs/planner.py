from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, 
    QListWidgetItem, QSizePolicy, QWidget, QPushButton
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor

from qfluentwidgets import (
    LineEdit, ListWidget, CheckBox, TransparentToolButton, FluentIcon as FIF
)

from gui.components.schedule import ScheduleComponent
from gui.components.timer import TimerComponent
from gui.components.alarm import AlarmComponent
from core.tasks import task_manager
from gui.components.jarvis_hud import HUDCornerWidget, HUDDivider, PulseOrb

class PlannerTab(QFrame):
    """
    JARVIS Strategic Planner & Timeline.
    """
    
    def __init__(self):
        super().__init__()
        self.setObjectName("plannerPanel")
        self.setStyleSheet("background: transparent;")
        
        self.completed_expanded = False
        
        self._setup_ui()
        self._load_tasks()

    def _setup_ui(self):
        planner_layout = QHBoxLayout(self)
        planner_layout.setContentsMargins(30, 30, 30, 30)
        planner_layout.setSpacing(25)
        
        # ── Column 1: Focus Tasks (HUD Frame) ─────────────────────────
        tasks_col = QFrame()
        tasks_col.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 22, 40, 0.85);
                border: 1px solid rgba(0, 212, 255, 0.15);
                border-top: 1px solid rgba(0, 212, 255, 0.45);
                border-radius: 14px;
            }
        """)
        self._tasks_corners = HUDCornerWidget(0, 0, QColor("#00d4ff"), 18, tasks_col)
        
        t_layout = QVBoxLayout(tasks_col)
        t_layout.setContentsMargins(25, 25, 25, 25)
        t_layout.setSpacing(15)
        
        t_header = QHBoxLayout()
        t_title = QLabel("CURRENT OBJECTIVES")
        t_title.setStyleSheet("color: #00d4ff; font-family: Consolas; font-weight: 700; font-size: 14px; letter-spacing: 2px; border: none; background: transparent;")
        t_header.addWidget(PulseOrb(8, QColor("#00d4ff")))
        t_header.addWidget(t_title)
        t_header.addStretch()
        t_layout.addLayout(t_header)
        t_layout.addWidget(HUDDivider(opacity=0.3))
        
        self.task_input = LineEdit()
        self.task_input.setPlaceholderText("Append new objective...")
        self.task_input.returnPressed.connect(self._add_task)
        self.task_input.setClearButtonEnabled(True)
        self.task_input.setStyleSheet("font-family: Consolas; font-size: 13px;")
        t_layout.addWidget(self.task_input)
        
        self.task_list = ListWidget()
        self.task_list.setStyleSheet("background: transparent; border: none;")
        t_layout.addWidget(self.task_list, 1) 
        
        header_layout = QHBoxLayout()
        self.completed_header_btn = TransparentToolButton(FIF.CHEVRON_RIGHT)
        self.completed_header_btn.clicked.connect(self._toggle_completed_section)
        header_layout.addWidget(self.completed_header_btn)
        
        self.completed_label = QLabel("ARCHIVED OBJECTIVES: 0")
        self.completed_label.setStyleSheet("color: #8b9bb4; font-family: Consolas; font-size: 12px; letter-spacing: 1px; border: none; background: transparent;")
        header_layout.addWidget(self.completed_label)
        header_layout.addStretch()
        
        t_layout.addLayout(header_layout)
        
        self.completed_list = ListWidget()
        self.completed_list.setStyleSheet("background: transparent; border: none;")
        self.completed_list.setVisible(False)
        t_layout.addWidget(self.completed_list)
        
        planner_layout.addWidget(tasks_col, 1)
        
        # ── Column 2: Schedule (HUD Frame) ────────────────────────────
        schedule_col = QFrame()
        schedule_col.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 22, 40, 0.85);
                border: 1px solid rgba(0, 212, 255, 0.15);
                border-top: 1px solid rgba(0, 212, 255, 0.45);
                border-radius: 14px;
            }
        """)
        self._sched_corners = HUDCornerWidget(0, 0, QColor("#00d4ff"), 18, schedule_col)
        
        s_layout = QVBoxLayout(schedule_col)
        s_layout.setContentsMargins(25, 25, 25, 25)
        
        s_header = QHBoxLayout()
        s_title = QLabel("SYSTEM TIMELINE")
        s_title.setStyleSheet("color: #00d4ff; font-family: Consolas; font-weight: 700; font-size: 14px; letter-spacing: 2px; border: none; background: transparent;")
        s_header.addWidget(s_title)
        s_header.addStretch()
        s_layout.addLayout(s_header)
        s_layout.addWidget(HUDDivider(opacity=0.3))
        
        self.schedule_component = ScheduleComponent()
        s_layout.addWidget(self.schedule_component)
        
        planner_layout.addWidget(schedule_col, 1)
        
        # ── Column 3: Performance Timers ──────────────────────────────
        flow_col = QFrame()
        flow_col.setFixedWidth(320)
        flow_col.setStyleSheet("background: transparent; border: none;")
        flow_layout = QVBoxLayout(flow_col)
        flow_layout.setContentsMargins(0, 0, 0, 0)
        flow_layout.setSpacing(25)
        
        p_title = QLabel("PERFORMANCE METRICS")
        p_title.setStyleSheet("color: #00d4ff; font-family: Consolas; font-weight: bold; font-size: 14px; letter-spacing: 2px;")
        flow_layout.addWidget(p_title)
        
        self.timer_component = TimerComponent()
        flow_layout.addWidget(self.timer_component)
        
        self.alarm_component = AlarmComponent() 
        flow_layout.addWidget(self.alarm_component)
        
        flow_layout.addStretch()
        planner_layout.addWidget(flow_col)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Assuming children index based on layout
        cols = self.findChildren(QFrame)
        if len(cols) >= 2:
            self._tasks_corners.resize(cols[0].width(), cols[0].height())
            self._sched_corners.resize(cols[1].width(), cols[1].height())

    def _load_tasks(self):
        tasks = task_manager.get_tasks()
        self.task_list.clear()
        self.completed_list.clear() 
        for task in tasks:
            self._create_task_item(task)
            
        self._update_task_counter()
        
    def _add_task(self):
        if hasattr(self, 'task_input'):
            task_text = self.task_input.text().strip()
            if task_text:
                self._add_task_from_text(task_text)
                self.task_input.clear()
    
    def _add_task_from_text(self, task_text):
        new_task = task_manager.add_task(task_text)
        if new_task:
            self._create_task_item(new_task)
        self._update_task_counter()
    
    def _on_task_checked(self, state: int, item: QListWidgetItem, source_list: ListWidget):
        widget = source_list.itemWidget(item)
        if not widget: return
        task_id = item.data(Qt.UserRole)
        label = widget.findChild(QLabel)
        if not label: return
        
        task_text = label.text()
        row = source_list.row(item)
        is_completed = (state == Qt.Checked.value)
        
        task_manager.toggle_task(task_id, is_completed)
        source_list.takeItem(row)
        
        task_data = {"id": task_id, "text": task_text, "completed": is_completed}
        self._create_task_item(task_data)
        self._update_task_counter()
    
    def _create_task_item(self, task_data: dict):
        completed = task_data.get('completed', False)
        text = task_data.get('text', '')
        task_id = task_data.get('id')
        
        target_list = self.completed_list if completed else self.task_list
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 50))
        item.setData(Qt.UserRole, task_id)
        
        task_widget = QWidget()
        task_layout = QHBoxLayout(task_widget)
        task_layout.setContentsMargins(10, 5, 10, 5)
        task_layout.setSpacing(12)
        
        checkbox = CheckBox()
        checkbox.setChecked(completed)
        checkbox.stateChanged.connect(lambda state, i=item, l=target_list: self._on_task_checked(state, i, l))
        task_layout.addWidget(checkbox)
        
        task_label = QLabel(text)
        if completed:
            task_label.setStyleSheet("color: #8b9bb4; text-decoration: line-through; font-family: 'Segoe UI'; font-size: 14px; background: transparent;")
        else:
            task_label.setStyleSheet("color: #c0c8d8; font-family: 'Segoe UI'; font-size: 14px; background: transparent;") 
            
        task_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        task_layout.addWidget(task_label, 1)
        
        delete_btn = TransparentToolButton(FIF.DELETE)
        delete_btn.clicked.connect(lambda: self._delete_task(item, target_list))
        task_layout.addWidget(delete_btn)
        
        target_list.addItem(item)
        target_list.setItemWidget(item, task_widget)
    
    def _delete_task(self, item: QListWidgetItem, source_list: ListWidget = None):
        if source_list is None:
            source_list = self.task_list
        task_id = item.data(Qt.UserRole)
        task_manager.delete_task(task_id)
        
        row = source_list.row(item)
        if row >= 0:
            source_list.takeItem(row)
            self._update_task_counter()
    
    def _toggle_completed_section(self):
        self.completed_expanded = not self.completed_expanded
        self.completed_list.setVisible(self.completed_expanded)
        if self.completed_expanded:
            self.completed_header_btn.setIcon(FIF.CHEVRON_DOWN_MED)
        else:
            self.completed_header_btn.setIcon(FIF.CHEVRON_RIGHT)
    
    def _update_task_counter(self):
        completed_count = self.completed_list.count()
        self.completed_label.setText(f"ARCHIVED OBJECTIVES: {completed_count}")