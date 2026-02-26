"""
MessageBubble component - JARVIS styled chat bubbles for PySide6.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QTextBrowser, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDesktopServices

import markdown
from pygments.formatters import HtmlFormatter

# Pre-generate CSS for code blocks (using JARVIS terminal aesthetic)
CODE_CSS = HtmlFormatter(style='monokai').get_style_defs('.codehilite')

class ResizingTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame)
        self.setOpenExternalLinks(False)
        self.anchorClicked.connect(QDesktopServices.openUrl)
        
        self.viewport().setStyleSheet("background: transparent;")
        self.setStyleSheet("background: transparent; border: none;")
        self.document().contentsChanged.connect(self.adjust_height)

    def adjust_height(self):
        doc_height = self.document().size().height()
        self.setFixedHeight(int(doc_height) + 10)
    
    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.adjust_height()

class MessageBubble(QFrame):
    """A styled message bubble for User or AI with Markdown support."""
    
    def __init__(self, role: str, text: str = "", is_thinking: bool = False, parent=None):
        super().__init__(parent)
        self.role = role
        self.is_thinking = is_thinking
        self._text = text
        
        self.setObjectName("messageBubble")
        self._setup_ui()
        self._apply_style()
        self.set_text(text) 
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(0)
        
        self.content_label = ResizingTextBrowser()
        
        if self.is_thinking:
            self.content_label.setFont(QFont("Consolas", 10))
        else:
            self.content_label.setFont(QFont("Segoe UI", 11))
        
        self.content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.content_label)
        
    def _apply_style(self):
        is_user = self.role == "user"
        
        if self.is_thinking:
            bg_color = "rgba(10, 22, 40, 0.5)"
            border = "1px solid rgba(255, 215, 0, 0.2)" # Gold accent for thinking
            border_radius = "12px"
            text_color = "#8b9bb4"
        elif is_user:
            bg_color = "rgba(0, 212, 255, 0.15)" # Cyan-tinted for user prompts
            border = "1px solid rgba(0, 212, 255, 0.4)"
            border_radius = "16px 16px 4px 16px"
            text_color = "#ffffff"
        else:
            bg_color = "rgba(10, 22, 40, 0.85)" # Deep navy for JARVIS
            border = "1px solid rgba(0, 212, 255, 0.15)"
            border_radius = "16px 16px 16px 4px"
            text_color = "#c0c8d8"
        
        self.setStyleSheet(f"""
            QFrame#messageBubble {{
                background-color: {bg_color};
                border: {border};
                border-radius: {border_radius};
            }}
            QTextBrowser {{ color: {text_color}; }}
        """)
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setMinimumWidth(60)
        self.setMaximumWidth(700) 
    
    def set_text(self, text: str, force_markdown: bool = True):
        self._text = text
        has_markdown = any(c in text for c in ['*', '`', '[', '#', '|', '-', '>'])
        
        if not force_markdown and not has_markdown:
             self.content_label.setPlainText(text)
             self.content_label.adjust_height()
             return

        html_content = markdown.markdown(text, extensions=['fenced_code', 'codehilite', 'nl2br'])
        
        styled_html = f"""
        <style>
            body {{ font-family: 'Segoe UI'; font-size: 11pt; margin: 0; padding: 0; line-height: 1.4; }}
            code {{ font-family: 'Consolas', monospace; color: #00d4ff; background-color: rgba(0,0,0,0.4); padding: 2px 5px; border-radius: 4px; }}
            pre {{ background-color: #050a12; border: 1px solid rgba(0, 212, 255, 0.2); padding: 12px; border-radius: 8px; color: #c0c8d8; margin: 8px 0; }}
            a {{ color: #00d4ff; text-decoration: none; }}
            {CODE_CSS}
        </style>
        <body>
            {html_content}
        </body>
        """
        
        self.content_label.setHtml(styled_html)
        self.content_label.adjust_height()
    
    def append_text(self, text: str):
        self._text += text
        self.set_text(self._text, force_markdown=False)
    
    @property
    def alignment(self):
        return Qt.AlignRight if self.role == "user" else Qt.AlignLeft