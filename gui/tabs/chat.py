from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QListWidgetItem, QSizePolicy, QMenu, QPushButton
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QFont, QIcon, QColor

from qfluentwidgets import (
    LineEdit, SwitchButton, ListWidget, ScrollArea,
    FluentIcon as FIF, Action, RoundMenu
)

from gui.components.message_bubble import MessageBubble
from gui.components import ThinkingExpander
from core.history import history_manager
from gui.components.jarvis_hud import HUDDivider, PulseOrb

class ChatTab(QWidget):
    """
    JARVIS Primary Communications Interface.
    """
    
    send_message_requested = Signal(str)
    stop_generation_requested = Signal()
    tts_toggled = Signal(bool)
    new_chat_requested = Signal()
    session_selected = Signal(str)
    
    session_pin_requested = Signal(str)
    session_rename_requested = Signal(str, str)
    session_delete_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("ChatTab")
        self._setup_ui()
        self._connect_internal_signals()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Sidebar (Session List) ──────────────────────────────────────────
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet("background-color: rgba(7, 13, 26, 0.7); border-right: 1px solid rgba(0, 212, 255, 0.2);")
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 10)
        sidebar_layout.setSpacing(15)

        self.new_chat_btn = QPushButton("⊕ NEW LINK")
        self.new_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 212, 255, 0.1);
                color: #00d4ff;
                border: 1px solid rgba(0, 212, 255, 0.4);
                border-radius: 8px;
                padding: 8px;
                font-family: Consolas;
                font-weight: bold;
                letter-spacing: 2px;
            }
            QPushButton:hover { background-color: rgba(0, 212, 255, 0.2); }
        """)
        sidebar_layout.addWidget(self.new_chat_btn)
        sidebar_layout.addWidget(HUDDivider(opacity=0.3))

        self.session_list = ListWidget()
        self.session_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self._show_session_context_menu)
        self.session_list.setStyleSheet("background: transparent; border: none;")
        sidebar_layout.addWidget(self.session_list)

        layout.addWidget(self.sidebar)

        # ── Chat Content Area ───────────────────────────────────────────────
        self.chat_content = QFrame()
        self.chat_content.setObjectName("chatContent")
        self.chat_content.setStyleSheet("background-color: transparent;")
        chat_layout = QVBoxLayout(self.chat_content)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: rgba(10, 22, 40, 0.6); border-bottom: 1px solid rgba(0, 212, 255, 0.2);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        status_row = QHBoxLayout()
        self.status_pulse = PulseOrb(10, QColor("#00d4ff"))
        status_row.addWidget(self.status_pulse)
        self.status_label = QLabel("COMMS: READY")
        self.status_label.setStyleSheet("color: #00d4ff; font-size: 13px; font-family: Consolas; letter-spacing: 2px; font-weight: bold; border: none;")
        status_row.addWidget(self.status_label)
        header_layout.addLayout(status_row)
        
        header_layout.addStretch()

        self.tts_toggle = SwitchButton()
        self.tts_toggle.setOnText("VOICE SYSTEM: ONLINE")
        self.tts_toggle.setOffText("VOICE SYSTEM: MUTED")
        header_layout.addWidget(self.tts_toggle)

        chat_layout.addWidget(header)

        # Chat Scroll Area
        self.chat_scroll = ScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("background: transparent; border: none;")
        self.chat_scroll.viewport().setStyleSheet("background: transparent;")

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_container_layout = QVBoxLayout(self.chat_container)
        self.chat_container_layout.setContentsMargins(30, 20, 30, 20)
        self.chat_container_layout.setSpacing(20)
        self.chat_container_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        chat_layout.addWidget(self.chat_scroll)

        # Input Bar
        input_bar = QFrame()
        input_bar.setFixedHeight(90)
        input_bar.setStyleSheet("background-color: rgba(10, 22, 40, 0.85); border-top: 1px solid rgba(0, 212, 255, 0.3);")
        
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(30, 20, 30, 20)
        input_layout.setSpacing(15)

        self.user_input = LineEdit()
        self.user_input.setPlaceholderText("Awaiting prompt input...")
        self.user_input.setClearButtonEnabled(True)
        self.user_input.setFixedHeight(45)
        self.user_input.setStyleSheet("font-size: 14px; font-family: 'Segoe UI';")
        input_layout.addWidget(self.user_input, 1)

        self.stop_btn = QPushButton("ABORT")
        self.stop_btn.setVisible(False)
        self.stop_btn.setFixedWidth(120)
        self.stop_btn.setFixedHeight(45)
        self.stop_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255, 59, 48, 0.15); color: #ff3b30; border: 1px solid #ff3b30; border-radius: 8px; font-family: Consolas; font-weight: bold; letter-spacing: 2px; }
            QPushButton:hover { background-color: rgba(255, 59, 48, 0.3); }
        """)
        input_layout.addWidget(self.stop_btn)

        self.send_btn = QPushButton("TRANSMIT")
        self.send_btn.setFixedWidth(120)
        self.send_btn.setFixedHeight(45)
        self.send_btn.setStyleSheet("""
            QPushButton { background-color: rgba(0, 212, 255, 0.15); color: #00d4ff; border: 1px solid #00d4ff; border-radius: 8px; font-family: Consolas; font-weight: bold; letter-spacing: 2px; }
            QPushButton:hover { background-color: rgba(0, 212, 255, 0.3); }
        """)
        input_layout.addWidget(self.send_btn)

        chat_layout.addWidget(input_bar)
        layout.addWidget(self.chat_content)

    def _connect_internal_signals(self):
        self.new_chat_btn.clicked.connect(self.new_chat_requested.emit)
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.user_input.returnPressed.connect(self._on_send_clicked)
        self.stop_btn.clicked.connect(self.stop_generation_requested.emit)
        self.tts_toggle.checkedChanged.connect(self.tts_toggled.emit)
        self.session_list.itemClicked.connect(self._on_session_clicked)

    def _on_send_clicked(self):
        text = self.user_input.text()
        if text.strip():
            self.send_message_requested.emit(text)

    def _on_session_clicked(self, item: QListWidgetItem):
        session_id = item.data(Qt.UserRole)
        if session_id:
            self.session_selected.emit(session_id)

    def set_status(self, text: str):
        QTimer.singleShot(0, lambda: self.status_label.setText(f"COMMS: {text.upper()}"))

    def clear_input(self):
        self.user_input.clear()

    def set_generating_state(self, is_generating: bool):
         self.send_btn.setVisible(not is_generating)
         self.stop_btn.setVisible(is_generating)
         self.user_input.setEnabled(not is_generating)
         self.status_pulse.set_color(QColor("#ffd700") if is_generating else QColor("#00d4ff"))
         if not is_generating:
             self.user_input.setFocus()

    def add_message_bubble(self, role: str, text: str, is_thinking: bool = False):
        bubble = MessageBubble(role, text, is_thinking)
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        
        if role == "user":
            wrapper_layout.addStretch()
            wrapper_layout.addWidget(bubble)
        else:
            wrapper_layout.addWidget(bubble)
            wrapper_layout.addStretch()
        
        count = self.chat_container_layout.count()
        self.chat_container_layout.insertWidget(count - 1, wrapper)
        QTimer.singleShot(50, self.scroll_to_bottom)

    def add_streaming_widgets(self, thinking_ui, search_indicator, response_bubble):
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(8)
        
        wrapper_layout.addWidget(thinking_ui)
        wrapper_layout.addWidget(search_indicator)
        
        bubble_wrapper = QWidget()
        bubble_wrapper.setStyleSheet("background: transparent;")
        bubble_layout = QHBoxLayout(bubble_wrapper)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.addWidget(response_bubble)
        bubble_layout.addStretch()
        wrapper_layout.addWidget(bubble_wrapper)
        
        count = self.chat_container_layout.count()
        self.chat_container_layout.insertWidget(count - 1, wrapper)
        QTimer.singleShot(50, self.scroll_to_bottom)

    def clear_chat_display(self):
        while self.chat_container_layout.count() > 1:
            item = self.chat_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def scroll_to_bottom(self):
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def refresh_sidebar(self, current_session_id: str = None):
        self.session_list.clear()
        sessions = history_manager.get_sessions()
        
        for sess in sessions:
            title = sess['title']
            sid = sess['id']
            is_pinned = sess.get('pinned', False)
            is_current = sid == current_session_id
            
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, sid)
            
            if is_pinned:
                item.setIcon(FIF.PIN.icon())
            else:
                item.setIcon(FIF.CHAT.icon())
                
            self.session_list.addItem(item)
            if is_current:
                self.session_list.setCurrentItem(item)

    def _show_session_context_menu(self, position):
        item = self.session_list.itemAt(position)
        if not item: return
        session_id = item.data(Qt.UserRole)
        if not session_id: return

        menu = RoundMenu(parent=self)
        menu.addAction(Action(FIF.PIN, "Pin/Unpin", triggered=lambda: self.session_pin_requested.emit(session_id)))
        menu.addAction(Action(FIF.EDIT, "Rename", triggered=lambda: self._prompt_rename(session_id)))
        menu.addSeparator()
        menu.addAction(Action(FIF.DELETE, "Delete", triggered=lambda: self.session_delete_requested.emit(session_id)))
        menu.exec(self.session_list.mapToGlobal(position))

    def _prompt_rename(self, session_id):
        from PySide6.QtWidgets import QInputDialog
        new_title, ok = QInputDialog.getText(self, "Rename Chat", "Enter new name:")
        if ok and new_title.strip():
            self.session_rename_requested.emit(session_id, new_title.strip())