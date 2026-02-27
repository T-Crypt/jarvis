from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from gui.components.news_card import NewsCard
from core.news import news_manager

from qfluentwidgets import (
    PushButton, FluentIcon as FIF, ScrollArea, SegmentedWidget,
    InfoBar, InfoBarPosition
)
from gui.components.jarvis_hud import HUDDivider, PulseOrb

class NewsLoaderThread(QThread):
    loaded = Signal(list)
    status_update = Signal(str)
    
    def __init__(self, use_ai=True, parent=None):
        super().__init__(parent)
        self.use_ai = use_ai

    def run(self):
        news = news_manager.get_briefing(status_callback=self.status_update.emit, use_ai=self.use_ai)
        self.loaded.emit(news)

class BriefingView(QWidget):
    """
    JARVIS Intelligence Briefing View.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("briefingView")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 36, 40, 36)
        self.layout.setSpacing(24)
        
        # ── Header Area ──────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        
        title_block = QVBoxLayout()
        title = QLabel("GLOBAL INTELLIGENCE")
        title.setStyleSheet("color: #00d4ff; font-size: 24px; font-weight: 700; font-family: Consolas; letter-spacing: 3px;")
        
        subtitle = QLabel("Curated intelligence streams · AI Analysis")
        subtitle.setStyleSheet("color: #8b9bb4; font-size: 13px;")
        
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        header_layout.addLayout(title_block)
        
        header_layout.addStretch()
        
        refresh_btn = PushButton(FIF.SYNC, " SYNC INTEL")
        refresh_btn.clicked.connect(lambda: self.load_news(use_ai=True))
        refresh_btn.setStyleSheet("""
            PushButton {
                background-color: rgba(0, 212, 255, 0.15);
                color: #00d4ff;
                border: 1px solid rgba(0, 212, 255, 0.5);
                border-radius: 8px;
                font-family: Consolas;
                font-weight: 700;
                letter-spacing: 1px;
                padding: 6px 16px;
            }
            PushButton:hover { background-color: rgba(0, 212, 255, 0.25); }
        """)
        header_layout.addWidget(refresh_btn)
        
        self.layout.addLayout(header_layout)
        self.layout.addWidget(HUDDivider(opacity=0.3))
        
        # ── Breaking News Alert (Red Arc Styling) ───────────────────────
        self.breaking_widget = QFrame()
        self.breaking_widget.setFixedHeight(60)
        self.breaking_widget.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 59, 48, 0.08);
                border: 1px solid rgba(255, 59, 48, 0.3);
                border-left: 4px solid #ff3b30;
                border-radius: 8px;
            }
        """)
        bk_layout = QHBoxLayout(self.breaking_widget)
        bk_layout.setContentsMargins(15, 0, 15, 0)
        
        self.pulse = PulseOrb(10, QColor("#ff3b30"))
        bk_layout.addWidget(self.pulse)
        
        bk_label = QLabel("PRIORITY ALERT :")
        bk_label.setStyleSheet("color: #ff3b30; font-weight: bold; font-family: Consolas; letter-spacing: 1px; font-size: 13px; border: none; background: transparent;")
        bk_layout.addWidget(bk_label)
        
        self.bk_text = QLabel("Standby for intelligence sync...")
        self.bk_text.setStyleSheet("color: #c0c8d8; font-size: 14px; font-family: 'Segoe UI', sans-serif; border: none; background: transparent;")
        bk_layout.addWidget(self.bk_text)
        bk_layout.addStretch()
        
        self.layout.addWidget(self.breaking_widget)
        
        # ── Filters & Feed ───────────────────────────────────────────────
        self.pivot = SegmentedWidget()
        categories = ["Top Stories", "Technology", "Markets", "Science", "Culture"]
        for c in categories:
            self.pivot.addItem(routeKey=c, text=c)
        self.pivot.setCurrentItem("Top Stories")
        self.layout.addWidget(self.pivot)
        
        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.viewport().setStyleSheet("background: transparent;")
        
        container = QWidget()
        self.news_list_layout = QVBoxLayout(container)
        self.news_list_layout.setSpacing(18)
        self.news_list_layout.setContentsMargins(0, 10, 0, 20)
        self.news_list_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(container)
        self.layout.addWidget(scroll)
        
        self.load_news(use_ai=False)

    def load_news(self, use_ai=True):
        # SAFETY GUARD
        if hasattr(self, 'loader_thread') and self.loader_thread and self.loader_thread.isRunning():
            return
            
        if use_ai:
            self.bk_text.setText("Syncing global sources & Curating with AI...")
        else:
            self.bk_text.setText("Fetching latest headlines...")
        
        while self.news_list_layout.count():
            item = self.news_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
        self.loader_thread = NewsLoaderThread(use_ai=use_ai, parent=self)
        self.loader_thread.status_update.connect(self.bk_text.setText)
        self.loader_thread.loaded.connect(self.display_news)
        self.loader_thread.finished.connect(self.loader_thread.deleteLater)
        self.loader_thread.start()
        
    def display_news(self, news_items):
        if not news_items:
            self.bk_text.setText("System offline. No news available.")
            InfoBar.warning(
                title="Comms Offline",
                content="Could not fetch latest streams. Check connection.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return
            
        if news_items:
            first = news_items[0]
            self.bk_text.setText(f"{first['title']} ({first['source']})")
        
        for item in news_items:
            card = NewsCard(item)
            self.news_list_layout.addWidget(card)