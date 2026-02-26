"""
Main PySide6 application setup and layout using Fluent Widgets.
Updated for J.A.R.V.I.S. System Interface.
"""

import threading
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QSize, QThread
from PySide6.QtGui import QIcon

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon as FIF,
    SplashScreen
)

from gui.handlers import ChatHandlers
from core.model_manager import unload_all_models
from core.voice_assistant import voice_assistant
from core.tts import tts
from config import VOICE_ASSISTANT_ENABLED, GREEN, GRAY, RESET

from gui.styles import JARVIS_STYLESHEET

from gui.tabs.dashboard import DashboardView
from gui.tabs.chat import ChatTab
from gui.tabs.planner import PlannerTab
from gui.tabs.settings import SettingsTab
from gui.tabs.briefing import BriefingView
from gui.tabs.browser import BrowserTab
from gui.tabs.home_automation import HomeAutomationTab
from gui.components.system_monitor import SystemMonitor
from core.llm import preload_models


class ModelPreloaderThread(QThread):
    """Background thread to preload models at startup."""
    def run(self):
        preload_models()


class LazyTab(QWidget):
    """Placeholder widget that loads the actual tab on demand."""
    def __init__(self, factory, object_name):
        super().__init__()
        self.setObjectName(object_name)
        self.factory = factory
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.actual_widget = None

    def initialize(self):
        if not self.actual_widget:
            self.actual_widget = self.factory()
            self.layout.addWidget(self.actual_widget)
            return self.actual_widget
        return self.actual_widget

class MainWindow(FluentWindow):
    """Main application window using Fluent Design."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S. System Interface")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)
        
        self.setStyleSheet(JARVIS_STYLESHEET)
        
        # Initialize handlers
        self.handlers = ChatHandlers(self)
        
        # Add system monitor to title bar
        self._init_system_monitor()
        
        # Initialize sub-interfaces pointers
        self.chat_tab = None
        self.planner_tab = None
        self.briefing_view = None
        self.home_tab = None
        
        # Flag to prevent duplicate signal connections
        self._chat_signals_connected = False

        self._init_window()
        self._connect_signals()
        self._init_background()
        self._preload_models()
        self._init_voice_assistant()
        
    def _preload_models(self):
        """Start the background thread to preload models."""
        self.preloader_thread = ModelPreloaderThread()
        self.preloader_thread.start()
    
    def _init_voice_assistant(self):
        """Initialize and start voice assistant if enabled."""
        print(f"[System] Initializing voice protocols (enabled={VOICE_ASSISTANT_ENABLED})...")
        if VOICE_ASSISTANT_ENABLED:
            # Connect voice assistant signals to UI
            print(f"[System] Connecting telemetry signals...")
            voice_assistant.wake_word_detected.connect(self._on_wake_word_detected)
            voice_assistant.speech_recognized.connect(self._on_speech_recognized)
            voice_assistant.processing_finished.connect(self._on_processing_finished)
            
            # Connect GUI update signals
            voice_assistant.timer_set.connect(self._on_voice_timer_set)
            voice_assistant.alarm_added.connect(self._on_voice_alarm_added)
            voice_assistant.calendar_updated.connect(self._on_voice_calendar_updated)
            voice_assistant.task_added.connect(self._on_voice_task_added)
            print(f"[System] ✓ Signals connected")
            
            # Initialize in background thread to avoid blocking UI
            def init_va():
                print(f"[System] Background thread: Initializing voice subsystem...")
                if voice_assistant.initialize():
                    print(f"[System] Background thread: ✓ Voice subsystem nominal")
                    tts.toggle(True)
                    print(f"[System] Background thread: TTS active")
                    print(f"[System] Background thread: Starting audio surveillance...")
                    voice_assistant.start()
                    print(f"[System] Background thread: ✓ Audio surveillance online")
                else:
                    print(f"[System] Background thread: ✗ Failed to initialize voice protocols")
            
            threading.Thread(target=init_va, daemon=True).start()
        else:
            print(f"[System] Voice assistant disabled via configuration.")
    
    def _on_wake_word_detected(self):
        """Handle wake word detection - show listening indicator."""
        print(f"{GREEN}[System] ✓ Voice trigger acquired!{RESET}")
        if VOICE_ASSISTANT_ENABLED:
            self.system_monitor.show_listening()
        else:
            print(f"{GRAY}[System] Voice assistant disabled via configuration.{RESET}")
    
    def _on_speech_recognized(self, text: str):
        """Handle speech recognition - update indicator text if needed."""
        pass
    
    def _on_processing_finished(self):
        """Handle processing finished - hide listening indicator."""
        if VOICE_ASSISTANT_ENABLED:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, lambda: self.system_monitor.hide_listening())
    
    def _on_voice_timer_set(self, seconds: int, label: str):
        """Handle timer set via voice - update GUI."""
        if not self.planner_tab:
            if hasattr(self, 'planner_lazy'):
                self.planner_tab = self.planner_lazy.initialize()
        
        if self.planner_tab and hasattr(self.planner_tab, 'timer_component'):
            self.planner_tab.timer_component.set_and_start(seconds, label)
            print(f"[System] Metric updated via voice: {seconds}s, {label}")
    
    def _on_voice_alarm_added(self):
        """Handle alarm added via voice - update GUI."""
        if not self.planner_tab:
            if hasattr(self, 'planner_lazy'):
                self.planner_tab = self.planner_lazy.initialize()
        
        if self.planner_tab and hasattr(self.planner_tab, 'alarm_component'):
            self.planner_tab.alarm_component.reload()
            print(f"[System] Alerts refreshed via voice")
    
    def _on_voice_calendar_updated(self):
        """Handle calendar event added via voice - refresh calendar."""
        if not self.planner_tab:
            if hasattr(self, 'planner_lazy'):
                self.planner_tab = self.planner_lazy.initialize()
        
        if self.planner_tab and hasattr(self.planner_tab, 'schedule_component'):
            self.planner_tab.schedule_component.refresh_events()
            print(f"[System] Timeline refreshed via voice")
    
    def _on_voice_task_added(self):
        """Handle task added via voice - refresh task list."""
        if not self.planner_tab:
            if hasattr(self, 'planner_lazy'):
                self.planner_tab = self.planner_lazy.initialize()
        
        if self.planner_tab and hasattr(self.planner_tab, '_load_tasks'):
            self.planner_tab._load_tasks()
            print(f"[System] Objectives refreshed via voice")
        
    def _init_window(self):
        # Dashboard is loaded immediately as it's the home screen
        self.dashboard_view = DashboardView()
        self.dashboard_view.setObjectName("dashboardInterface")
        self.dashboard_view.navigate_to.connect(self._navigate_to_tab)
        self.addSubInterface(self.dashboard_view, FIF.LAYOUT, "Dashboard")

        # Lazy load other tabs
        self.chat_lazy = LazyTab(ChatTab, "chatInterface")
        self.planner_lazy = LazyTab(PlannerTab, "plannerInterface")
        
        self.briefing_view = BriefingView()
        self.briefing_view.setObjectName("briefingInterface")

        self.home_lazy = LazyTab(HomeAutomationTab, "homeInterface")
        self.browser_lazy = LazyTab(BrowserTab, "browserInterface")
        
        self.addSubInterface(self.chat_lazy, FIF.CHAT, "Comms")
        self.addSubInterface(self.planner_lazy, FIF.CALENDAR, "Planner")
        self.addSubInterface(self.briefing_view, FIF.DATE_TIME, "Intel")
        self.addSubInterface(self.home_lazy, FIF.HOME, "Home Auto")
        self.addSubInterface(self.browser_lazy, FIF.GLOBE, "Web Agent")
        
        # Settings at bottom
        self.settings_lazy = LazyTab(SettingsTab, "settingsInterface")
        self.addSubInterface(
            self.settings_lazy, FIF.SETTING, "Settings",
            NavigationItemPosition.BOTTOM
        )
        
    def _connect_signals(self):
        self.stackedWidget.currentChanged.connect(self._on_tab_changed)

    def _connect_chat_signals(self):
        if not self.chat_tab or self._chat_signals_connected:
            return
        self._chat_signals_connected = True
        self.chat_tab.new_chat_requested.connect(self.handlers.clear_chat)
        self.chat_tab.send_message_requested.connect(self._on_send)
        self.chat_tab.stop_generation_requested.connect(self.handlers.stop_generation)
        self.chat_tab.tts_toggled.connect(self.handlers.toggle_tts)
        self.chat_tab.session_selected.connect(self._on_session_clicked)
        
        self.chat_tab.session_pin_requested.connect(self.handlers.pin_session)
        self.chat_tab.session_rename_requested.connect(self.handlers.rename_session)
        self.chat_tab.session_delete_requested.connect(self.handlers.delete_session)
        
        self.chat_tab.refresh_sidebar()

    def _on_send(self, text):
        self.handlers.send_message(text)
        
    def _on_session_clicked(self, session_id):
        self.handlers.load_session(session_id)
    
    def _init_background(self):
        self.set_status("SYSTEM ONLINE")
    
    def _init_system_monitor(self):
        """Add system monitor widget to the title bar, centered."""
        self.system_monitor = SystemMonitor()
        layout = self.titleBar.hBoxLayout
        min_btn_index = layout.indexOf(self.titleBar.minBtn)
        
        layout.insertStretch(min_btn_index, 1)
        layout.insertWidget(min_btn_index + 1, self.system_monitor, 0, Qt.AlignmentFlag.AlignCenter)
        layout.insertStretch(min_btn_index + 2, 1)
    
    def _on_tab_changed(self, index):
        widget = self.stackedWidget.widget(index)
        
        if isinstance(widget, LazyTab):
            real_widget = widget.initialize()
            obj_name = widget.objectName()
            
            if obj_name == "chatInterface":
                self.chat_tab = real_widget
                self._connect_chat_signals()
            elif obj_name == "plannerInterface":
                self.planner_tab = real_widget
            elif obj_name == "briefingInterface":
                self.briefing_view = real_widget
            elif obj_name == "homeInterface":
                self.home_tab = real_widget
            elif obj_name == "browserInterface":
                pass
                
        self.set_status("SYSTEM ONLINE")
    
    def _navigate_to_tab(self, route_key: str):
        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if widget.objectName() == route_key:
                self.switchTo(widget)
                return
    
    # --- Public Methods for Handlers (Proxy/Facade) ---
    def set_status(self, text: str):
        if self.chat_tab: self.chat_tab.set_status(text)
    
    def clear_input(self):
        if self.chat_tab: self.chat_tab.clear_input()
    
    def set_generating_state(self, is_generating: bool):
        if self.chat_tab: self.chat_tab.set_generating_state(is_generating)
    
    def add_message_bubble(self, role: str, text: str, is_thinking: bool = False):
        if self.chat_tab: self.chat_tab.add_message_bubble(role, text, is_thinking)
    
    def add_streaming_widgets(self, thinking_ui, search_indicator, response_bubble):
        if self.chat_tab: self.chat_tab.add_streaming_widgets(thinking_ui, search_indicator, response_bubble)
    
    def clear_chat_display(self):
        if self.chat_tab: self.chat_tab.clear_chat_display()
    
    def refresh_sidebar(self, current_session_id: str = None):
        if self.chat_tab: self.chat_tab.refresh_sidebar(current_session_id)
    
    def scroll_to_bottom(self):
        if self.chat_tab: self.chat_tab.scroll_to_bottom()

    def closeEvent(self, event):
        """Handle application close event."""
        print("[System] Closing interface, purging memory cores...")
        self.set_status("INITIATING SHUTDOWN SEQUENCE...")
        
        if VOICE_ASSISTANT_ENABLED:
            voice_assistant.stop()
        
        unload_all_models(sync=True)
        event.accept()

def create_app():
    return MainWindow()