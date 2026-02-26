"""
System Monitor Component - Displays CPU, RAM, GPU usage and running Ollama models.
Updated for JARVIS Iron Man HUD Glassmorphism.
"""

import psutil
import requests
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import QTimer, Qt, QObject, Signal, QThread
from PySide6.QtGui import QFont

from config import OLLAMA_URL
from core.llm import is_router_loaded

try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except Exception:
    GPU_AVAILABLE = False


class MonitorWorker(QObject):
    stats_updated = Signal(dict)

    def __init__(self):
        super().__init__()

    def collect(self):
        try:
            stats = {}
            # CPU
            stats['cpu'] = psutil.cpu_percent(interval=None)
            # RAM
            ram = psutil.virtual_memory()
            stats['ram'] = {
                'percent': ram.percent,
                'used': ram.used / (1024 ** 3),
                'total': ram.total / (1024 ** 3)
            }
            # GPU
            if GPU_AVAILABLE:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    
                    stats['gpu'] = {
                        'percent': util.gpu,
                        'vram_used': mem_info.used / (1024 ** 3),
                        'vram_total': mem_info.total / (1024 ** 3),
                        'vram_percent': (mem_info.used / mem_info.total) * 100
                    }
                except Exception:
                    stats['gpu'] = None
            else:
                stats['gpu'] = None

            # Ollama Models
            try:
                response = requests.get(f"{OLLAMA_URL}/ps", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    if models:
                        model_names = [m.get("name", "?").split(":")[0] for m in models]
                        stats['models'] = model_names
                    else:
                        stats['models'] = []
                else:
                    stats['models'] = "Offline"
            except Exception:
                stats['models'] = "Offline"
            
            # Local Router Model (Gemma)
            stats['router_loaded'] = is_router_loaded()

            self.stats_updated.emit(stats)
        except Exception as e:
            print(f"MonitorWorker Error: {e}")


class SystemMonitor(QFrame):
    """
    A status bar showing system resource usage and running models.
    Styled with JARVIS HUD elements.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("systemMonitor")
        self._setup_ui()
        self._init_worker()
        self._init_voice_indicator()
    
    def _setup_ui(self):
        self.setFixedHeight(32)
        # JARVIS Glassmorphism Palette Integration
        self.setStyleSheet("""
            QFrame#systemMonitor {
                background: rgba(10, 22, 40, 0.6);
                border-bottom: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
            }
            QLabel {
                color: #8b9bb4;
                font-size: 12px;
                padding: 0 6px;
                font-family: Consolas;
            }
            QLabel#valueLabel {
                color: #c0c8d8;
                font-weight: bold;
            }
            QLabel#modelsLabel {
                color: #00d4ff; /* JARVIS Cyan */
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(24)
        
        # CPU
        cpu_container = QHBoxLayout()
        cpu_container.setSpacing(4)
        cpu_label = QLabel("CPU:")
        cpu_container.addWidget(cpu_label)
        self.cpu_value = QLabel("0%")
        self.cpu_value.setObjectName("valueLabel")
        cpu_container.addWidget(self.cpu_value)
        layout.addLayout(cpu_container)
        
        # RAM
        ram_container = QHBoxLayout()
        ram_container.setSpacing(4)
        ram_label = QLabel("RAM:")
        ram_container.addWidget(ram_label)
        self.ram_value = QLabel("0%")
        self.ram_value.setObjectName("valueLabel")
        ram_container.addWidget(self.ram_value)
        layout.addLayout(ram_container)
        
        # GPU
        gpu_container = QHBoxLayout()
        gpu_container.setSpacing(4)
        gpu_label = QLabel("GPU:")
        gpu_container.addWidget(gpu_label)
        self.gpu_value = QLabel("N/A" if not GPU_AVAILABLE else "0%")
        self.gpu_value.setObjectName("valueLabel")
        gpu_container.addWidget(self.gpu_value)
        layout.addLayout(gpu_container)
        
        # VRAM
        vram_container = QHBoxLayout()
        vram_container.setSpacing(4)
        vram_label = QLabel("VRAM:")
        vram_container.addWidget(vram_label)
        self.vram_value = QLabel("N/A" if not GPU_AVAILABLE else "0.0 GB")
        self.vram_value.setObjectName("valueLabel")
        vram_container.addWidget(self.vram_value)
        layout.addLayout(vram_container)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background: rgba(0, 212, 255, 0.2);")
        separator.setFixedWidth(1)
        layout.addWidget(separator)
        
        # Running Models
        models_container = QHBoxLayout()
        models_container.setSpacing(4)
        models_label = QLabel("AI CORES:")
        models_container.addWidget(models_label)
        self.models_value = QLabel("LOADING...")
        self.models_value.setObjectName("modelsLabel")
        models_container.addWidget(self.models_value)
        layout.addLayout(models_container)
        
        self.voice_indicator = QFrame()
        self.voice_indicator.setFixedSize(4, 20)
        self.voice_indicator.hide()
        layout.addWidget(self.voice_indicator)
        layout.addStretch()
    
    def _init_voice_indicator(self):
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        self.voice_animation = QPropertyAnimation(self.voice_indicator, b"styleSheet")
        self.voice_animation.setDuration(1000)
        self.voice_animation.setLoopCount(-1)
        self.voice_animation.setEasingCurve(QEasingCurve.InOutSine)
        
        # JARVIS Cyan pulsing glow
        self.voice_animation.setStartValue("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 212, 255, 100),
                    stop:0.5 rgba(0, 212, 255, 255),
                    stop:1 rgba(0, 212, 255, 100));
                border-radius: 2px;
            }
        """)
        self.voice_animation.setEndValue("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 212, 255, 255),
                    stop:0.5 rgba(0, 212, 255, 100),
                    stop:1 rgba(0, 212, 255, 255));
                border-radius: 2px;
            }
        """)
    
    def show_listening(self):
        if not self.voice_indicator.isVisible():
            self.voice_indicator.show()
            self.voice_animation.start()
    
    def hide_listening(self):
        self.voice_animation.stop()
        self.voice_indicator.hide()
    
    def _init_worker(self):
        self.monitor_thread = QThread()
        self.worker = MonitorWorker()
        self.worker.moveToThread(self.monitor_thread)
        self.worker.stats_updated.connect(self._on_stats_updated)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.worker.collect)
        self.timer.start(3000) 
        
        self.monitor_thread.start()
        QTimer.singleShot(100, self.worker.collect)

    def _on_stats_updated(self, stats):
        # CPU
        cpu_val = stats.get('cpu', 0)
        self.cpu_value.setText(f"{round(cpu_val)}%")
        self._color_by_usage(self.cpu_value, cpu_val)
        
        # RAM
        ram_data = stats.get('ram', {})
        ram_percent = ram_data.get('percent', 0)
        self.ram_value.setText(f"{round(ram_percent)}% ({ram_data.get('used',0):.1f} GB)")
        self._color_by_usage(self.ram_value, ram_percent)
        
        # GPU
        gpu_data = stats.get('gpu')
        if gpu_data:
            gpu_percent = gpu_data.get('percent', 0)
            self.gpu_value.setText(f"{round(gpu_percent)}%")
            self._color_by_usage(self.gpu_value, gpu_percent)
            
            vram_text = f"{gpu_data.get('vram_used',0):.1f}/{gpu_data.get('vram_total',0):.1f} GB"
            self.vram_value.setText(vram_text)
            self._color_by_usage(self.vram_value, gpu_data.get('vram_percent', 0))
        elif not GPU_AVAILABLE:
             self.gpu_value.setText("N/A")
             self.vram_value.setText("N/A")
             
        # Models
        models = stats.get('models', [])
        router_loaded = stats.get('router_loaded', False)
        display_parts = []
        
        if isinstance(models, list):
            if models:
                if len(models) <= 2:
                    display_parts.extend([m.upper() for m in models])
                else:
                    display_parts.append(f"{models[0].upper()} +{len(models)-1}")
        elif models == "Offline":
            display_parts.append("OFFLINE")
        
        if router_loaded:
            display_parts.append("ROUTER")
        
        self.models_value.setText(", ".join(display_parts) if display_parts else "IDLE")

    def _color_by_usage(self, label: QLabel, percent: float):
        """Color the label using the JARVIS HUD alert palette."""
        if percent >= 90:
            color = "#ff3b30"  # Arc Red (Critical)
        elif percent >= 75:
            color = "#ffd700"  # Gold (Warning)
        else:
            color = "#00d4ff"  # Jarvis Cyan (Nominal)
            
        label.setStyleSheet(f"color: {color}; font-weight: bold; font-family: Consolas;")

    def __del__(self):
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.quit()
            self.monitor_thread.wait()