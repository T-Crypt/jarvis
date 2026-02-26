"""
Comprehensive Settings Tab with model selection, connection settings, and preferences.
Updated with JARVIS aesthetics.
"""

from config import LOCAL_ROUTER_PATH, RESPONDER_MODEL

import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QColor

from qfluentwidgets import (
    ScrollArea, ExpandLayout, SettingCardGroup, PushSettingCard, FluentIcon as FIF,
    setTheme, Theme, PrimaryPushSettingCard, ComboBox, LineEdit, 
    PrimaryPushButton, InfoBar, InfoBarPosition, SettingCard, Slider, 
    StrongBodyLabel, SwitchButton
)

from core.settings_store import settings
from gui.components.jarvis_hud import HUDDivider, PulseOrb

# --- Worker Threads (unchanged logic) ---
class ModelFetcher(QThread):
    models_fetched = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, ollama_url: str):
        super().__init__()
        self.ollama_url = ollama_url
    
    def run(self):
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                self.models_fetched.emit(models)
            else:
                self.error_occurred.emit(f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("Cannot connect to Ollama")
        except Exception as e:
            self.error_occurred.emit(str(e))

class ConnectionTester(QThread):
    success = Signal()
    failed = Signal(str)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.success.emit()
            else:
                self.failed.emit(f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.failed.emit("Connection refused")
        except Exception as e:
            self.failed.emit(str(e))

# --- Setting Cards ---
class ComboBoxCard(SettingCard):
    value_changed = Signal(str)
    def __init__(self, icon, title, description, options: list, key_path: str, parent=None):
        super().__init__(icon, title, description, parent)
        self.key_path = key_path
        self.combo = ComboBox(self)
        self.combo.setMinimumWidth(180)
        self.combo.addItems(options)
        
        current = settings.get(key_path, options[0] if options else "")
        if current in options:
            self.combo.setCurrentText(current)
        
        self.combo.currentTextChanged.connect(self._on_changed)
        self.hBoxLayout.addWidget(self.combo, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
    
    def _on_changed(self, text: str):
        settings.set(self.key_path, text)
        self.value_changed.emit(text)

class ModelSelectCard(SettingCard):
    model_changed = Signal(str)
    def __init__(self, icon, title, description, key_path: str, parent=None):
        super().__init__(icon, title, description, parent)
        self.key_path = key_path
        self.combo = ComboBox(self)
        self.combo.setMinimumWidth(180)
        self.combo.setPlaceholderText("Select model...")
        
        current = settings.get(key_path, "")
        if current:
            self.combo.addItem(current)
            self.combo.setCurrentText(current)
        
        self.combo.currentTextChanged.connect(self._on_changed)
        self.hBoxLayout.addWidget(self.combo, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
    
    def _on_changed(self, text: str):
        if text:
            settings.set(self.key_path, text)
            self.model_changed.emit(text)
    
    def update_models(self, models: list):
        current = self.combo.currentText()
        self.combo.clear()
        self.combo.addItems(models)
        if current in models:
            self.combo.setCurrentText(current)
        elif models:
            self.combo.setCurrentIndex(0)

class UrlInputCard(SettingCard):
    def __init__(self, icon, title, description, key_path: str, parent=None):
        super().__init__(icon, title, description, parent)
        self.key_path = key_path
        self.tester = None
        self.url_input = LineEdit(self)
        self.url_input.setMinimumWidth(250)
        self.url_input.setText(settings.get(key_path, "http://localhost:11434"))
        self.url_input.textChanged.connect(self._on_url_changed)
        
        self.test_btn = PrimaryPushButton("Test", self)
        self.test_btn.setFixedWidth(70)
        self.test_btn.clicked.connect(self._test_connection)
        
        self.hBoxLayout.addWidget(self.url_input, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.test_btn, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
    
    def _on_url_changed(self, text: str):
        settings.set(self.key_path, text)
    
    def _test_connection(self):
        url = self.url_input.text().strip()
        if not url: return
        self.test_btn.setEnabled(False)
        self.test_btn.setText("...")
        self.tester = ConnectionTester(url)
        self.tester.success.connect(self._on_test_success)
        self.tester.failed.connect(self._on_test_failed)
        self.tester.finished.connect(self._on_test_done)
        self.tester.start()
    
    @Slot()
    def _on_test_success(self):
        InfoBar.success(title="Connected", content="Ollama is reachable!", orient=Qt.Horizontal, position=InfoBarPosition.TOP, duration=3000, parent=self.window())
    
    @Slot(str)
    def _on_test_failed(self, error: str):
        InfoBar.error(title="Connection Failed", content=error, orient=Qt.Horizontal, position=InfoBarPosition.TOP, duration=5000, parent=self.window())
    
    @Slot()
    def _on_test_done(self):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("Test")

class SliderCard(SettingCard):
    value_changed = Signal(int)
    def __init__(self, icon, title, description, key_path: str, min_val: int, max_val: int, parent=None):
        super().__init__(icon, title, description, parent)
        self.key_path = key_path
        self.value_label = StrongBodyLabel(self)
        self.value_label.setMinimumWidth(30)
        self.slider = Slider(Qt.Horizontal, self)
        self.slider.setMinimumWidth(150)
        self.slider.setRange(min_val, max_val)
        
        current = settings.get(key_path, min_val)
        self.slider.setValue(current)
        self.value_label.setText(str(current))
        self.slider.valueChanged.connect(self._on_changed)
        
        self.hBoxLayout.addWidget(self.value_label, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.slider, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
    
    def _on_changed(self, value: int):
        self.value_label.setText(str(value))
        settings.set(self.key_path, value)
        self.value_changed.emit(value)

class SwitchCard(SettingCard):
    checked_changed = Signal(bool)
    def __init__(self, icon, title, description, key_path: str, parent=None):
        super().__init__(icon, title, description, parent)
        self.key_path = key_path
        self.switch = SwitchButton(self)
        self.switch.setChecked(settings.get(key_path, False))
        self.switch.checkedChanged.connect(self._on_changed)
        self.hBoxLayout.addWidget(self.switch, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
    
    def _on_changed(self, checked: bool):
        settings.set(self.key_path, checked)
        self.checked_changed.emit(checked)

class TextInputCard(SettingCard):
    value_changed = Signal(str)
    def __init__(self, icon, title, description, key_path: str, placeholder: str = "", parent=None):
        super().__init__(icon, title, description, parent)
        self.key_path = key_path
        self.input = LineEdit(self)
        self.input.setMinimumWidth(200)
        self.input.setPlaceholderText(placeholder)
        
        current = settings.get(key_path, "")
        self.input.setText(str(current))
        self.input.textChanged.connect(self._on_changed)
        self.hBoxLayout.addWidget(self.input, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
    
    def _on_changed(self, text: str):
        try:
            value = float(text) if text else text
            settings.set(self.key_path, value)
            self.value_changed.emit(text)
        except ValueError:
            settings.set(self.key_path, text)
            self.value_changed.emit(text)

class SettingsTab(ScrollArea):
    """
    JARVIS System Preferences & Configurations.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        
        self.setStyleSheet("background-color: transparent; border: none;")
        self.scrollWidget.setObjectName("scrollWidget")
        
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
        self.model_fetcher = None
        self._available_models = []
        
        self._init_ui()
        self._fetch_models() 

    def _init_ui(self):
        # ── JARVIS Header ───────────────────────────────────────────────
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 20, 30, 10)
        
        row = QHBoxLayout()
        row.addWidget(PulseOrb(10, QColor("#00d4ff")))
        title = QLabel("SYSTEM CONFIGURATION")
        title.setStyleSheet("color: #00d4ff; font-family: Consolas; font-weight: 700; font-size: 24px; letter-spacing: 3px;")
        row.addWidget(title)
        row.addStretch()
        header_layout.addLayout(row)
        
        sub = QLabel("Modify core directives and intelligence routing")
        sub.setStyleSheet("color: #8b9bb4; font-size: 13px;")
        header_layout.addWidget(sub)
        header_layout.addWidget(HUDDivider(opacity=0.3))
        
        self.expandLayout.addWidget(header_widget)

        # ── Groups ───────────────────────────────────────────────────────
        self.personal_group = SettingCardGroup("Personalization", self.scrollWidget)
        self.theme_card = ComboBoxCard(FIF.BRUSH, "Application Theme", "Change the appearance of the application", ["Light", "Dark", "Auto"], "theme", self.personal_group)
        self.theme_card.value_changed.connect(self._on_theme_changed)
        self.personal_group.addSettingCard(self.theme_card)
        self.expandLayout.addWidget(self.personal_group)

        self.ai_group = SettingCardGroup("AI Models", self.scrollWidget)
        self.chat_model_card = ModelSelectCard(FIF.CHAT, "Chat Model", "Ollama model for general chat responses", "models.chat", self.ai_group)
        self.ai_group.addSettingCard(self.chat_model_card)
        
        self.web_agent_model_card = ModelSelectCard(FIF.GLOBE, "Web Agent Model", "Vision-language model for browser automation", "models.web_agent", self.ai_group)
        self.ai_group.addSettingCard(self.web_agent_model_card)
        
        self.router_model_card = SettingCard(FIF.ROBOT, "Function Router Model", f"Local FunctionGemma model at: {LOCAL_ROUTER_PATH}", self.ai_group)
        self.ai_group.addSettingCard(self.router_model_card)
        
        self.refresh_models_card = PushSettingCard("Refresh", FIF.SYNC, "Refresh Models", "Fetch available models from Ollama", self.ai_group)
        self.refresh_models_card.clicked.connect(self._fetch_models)
        self.ai_group.addSettingCard(self.refresh_models_card)
        self.expandLayout.addWidget(self.ai_group)

        self.connection_group = SettingCardGroup("Connection", self.scrollWidget)
        self.ollama_url_card = UrlInputCard(FIF.LINK, "Ollama URL", "API endpoint for Ollama server", "ollama_url", self.connection_group)
        self.connection_group.addSettingCard(self.ollama_url_card)
        self.expandLayout.addWidget(self.connection_group)

        self.voice_group = SettingCardGroup("Voice & Audio", self.scrollWidget)
        piper_voices = ["en_GB-alba-medium", "en_US-amy-medium", "en_US-lessac-medium", "en_US-libritts-high"]
        self.tts_voice_card = ComboBoxCard(FIF.VOLUME, "TTS Voice", "Voice model for text-to-speech", piper_voices, "tts.voice", self.voice_group)
        self.voice_group.addSettingCard(self.tts_voice_card)
        self.expandLayout.addWidget(self.voice_group)

        self.weather_group = SettingCardGroup("Weather Location", self.scrollWidget)
        self.city_card = TextInputCard(FIF.PIN, "City Name", "Display name for your location", "weather.city", "New York, NY", self.weather_group)
        self.weather_group.addSettingCard(self.city_card)
        self.latitude_card = TextInputCard(FIF.PIN, "Latitude", "Latitude coordinate (-90 to 90)", "weather.latitude", "40.7128", self.weather_group)
        self.weather_group.addSettingCard(self.latitude_card)
        self.longitude_card = TextInputCard(FIF.GLOBE, "Longitude", "Longitude coordinate (-180 to 180)", "weather.longitude", "-74.0060", self.weather_group)
        self.weather_group.addSettingCard(self.longitude_card)
        self.expandLayout.addWidget(self.weather_group)

        self.general_group = SettingCardGroup("General", self.scrollWidget)
        self.max_history_card = SliderCard(FIF.HISTORY, "Max Chat History", "Number of messages to keep in context", "general.max_history", 5, 50, self.general_group)
        self.general_group.addSettingCard(self.max_history_card)
        self.auto_news_card = SwitchCard(FIF.DOCUMENT, "Auto-fetch News", "Automatically fetch news on startup", "general.auto_fetch_news", self.general_group)
        self.general_group.addSettingCard(self.auto_news_card)
        self.expandLayout.addWidget(self.general_group)

        self.about_group = SettingCardGroup("About", self.scrollWidget)
        self.about_card = PrimaryPushSettingCard("Check Update", FIF.INFO, "About A.D.A", "Version 0.2.0 (Alpha)", self.about_group)
        self.about_group.addSettingCard(self.about_card)
        self.reset_card = PushSettingCard("Reset", FIF.CANCEL, "Reset Settings", "Restore all settings to defaults", self.about_group)
        self.reset_card.clicked.connect(self._on_reset)
        self.about_group.addSettingCard(self.reset_card)
        self.expandLayout.addWidget(self.about_group)

    def _on_theme_changed(self, value: str):
        theme_map = {"Dark": Theme.DARK, "Light": Theme.LIGHT, "Auto": Theme.AUTO}
        setTheme(theme_map.get(value, Theme.DARK))
    
    def _on_reset(self):
        settings.reset_to_defaults()
        InfoBar.success(title="Settings Reset", content="All settings restored to defaults. Please restart the app.", orient=Qt.Horizontal, position=InfoBarPosition.TOP, duration=5000, parent=self.window())
    
    def _fetch_models(self):
        url = settings.get("ollama_url", "http://localhost:11434")
        self.model_fetcher = ModelFetcher(url)
        self.model_fetcher.models_fetched.connect(self._on_models_fetched)
        self.model_fetcher.error_occurred.connect(self._on_models_error)
        self.model_fetcher.start()
    
    @Slot(list)
    def _on_models_fetched(self, models: list):
        self._available_models = models
        self.chat_model_card.update_models(models)
        self.web_agent_model_card.update_models(models)
        InfoBar.success(title="Models Loaded", content=f"Found {len(models)} models", orient=Qt.Horizontal, position=InfoBarPosition.TOP, duration=2000, parent=self.window())
    
    @Slot(str)
    def _on_models_error(self, error: str):
        InfoBar.warning(title="Could not fetch models", content=error, orient=Qt.Horizontal, position=InfoBarPosition.TOP, duration=4000, parent=self.window())