from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget, QHBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor, QFont

class NewsCard(QFrame):
    """
    A card widget representing a single news story.
    Styling completely updated for the JARVIS Iron Man HUD Glassmorphism.
    """
    def __init__(self, article, parent=None):
        super().__init__(parent)
        self.article = article
        self.url = article.get('url')
        
        self.setObjectName("newsCard")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(140) 
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Image placeholder (Left side)
        self.image_area = QLabel()
        self.image_area.setFixedSize(60, 60)
        self.image_area.setAlignment(Qt.AlignCenter)
        
        icon_color = self._get_category_color(article.get('category'))
        
        # Jarvis styled icon bubble
        self.image_area.setStyleSheet(f"""
            background-color: {icon_color}15; 
            border: 1px solid {icon_color}40;
            border-radius: 12px;
            font-size: 28px;
        """)
        self.image_area.setText(self._get_category_icon(article.get('category')))
        layout.addWidget(self.image_area)
        
        # Content (Right side)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        content_layout.setAlignment(Qt.AlignVCenter)
        
        # Headline - larger, inclusive font sizing
        headline = QLabel(article.get('title', 'No Title'))
        headline.setWordWrap(True)
        headline.setStyleSheet("color: #c0c8d8; font-size: 16px; font-weight: 600; font-family: 'Segoe UI', sans-serif;")
        content_layout.addWidget(headline)
        
        # Metadata Row
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(10)
        
        # Source (styled like JARVIS cyan data)
        source = QLabel(article.get('source', 'Unknown').upper())
        source.setStyleSheet(f"color: {icon_color}; font-weight: bold; font-size: 12px; font-family: Consolas; letter-spacing: 1px;")
        meta_layout.addWidget(source)
        
        # Divider
        div = QLabel("·")
        div.setStyleSheet("color: #6b7a95; font-weight: bold;")
        meta_layout.addWidget(div)
        
        # Time
        date = QLabel(article.get('date', 'JUST NOW').upper())
        date.setStyleSheet("color: #8b9bb4; font-size: 12px; font-family: Consolas;")
        meta_layout.addWidget(date)
        
        meta_layout.addStretch()
        content_layout.addLayout(meta_layout)
        
        layout.addLayout(content_layout)
        
        # Styling matching HUDCard from dashboard.py
        self.setStyleSheet("""
            QFrame#newsCard {
                background-color: rgba(10, 22, 40, 0.85); /* Deep Navy Glass */
                border: 1px solid rgba(0, 212, 255, 0.18);
                border-top: 1px solid rgba(0, 212, 255, 0.35);
                border-radius: 14px;
            }
            QFrame#newsCard:hover {
                background-color: #0d1f3c; /* Elevated surface */
                border: 1px solid rgba(0, 212, 255, 0.45);
                border-top: 1px solid #00d4ff;
            }
        """)

    def _get_category_color(self, category):
        """Return JARVIS-compliant color based on category."""
        cat = str(category).lower()
        if "tech" in cat: return "#00d4ff" # Jarvis Cyan
        if "market" in cat or "finance" in cat: return "#ffd700" # Gold
        if "science" in cat: return "#aa66cc" # Purple
        if "culture" in cat: return "#ff3b30" # Arc Red
        return "#0ea5c9" # Cyan Mid default

    def _get_category_icon(self, category):
        cat = str(category).lower()
        if "tech" in cat: return "💻"
        if "market" in cat: return "📊"
        if "science" in cat: return "🧬"
        if "culture" in cat: return "🌐" 
        return "📰"
    
    def mousePressEvent(self, event):
        """Open URL on click."""
        import webbrowser
        if self.url:
            webbrowser.open(self.url)