"""
Voice Assistant - Main orchestrator for Alexa-like voice interaction.
Manages: STT → Function Gemma → Qwen → TTS pipeline.
"""

import threading
import json
import requests
from typing import Optional
from PySide6.QtCore import QObject, Signal

from config import (
    RESPONDER_MODEL, OLLAMA_URL, MAX_HISTORY, GRAY, RESET, CYAN, GREEN, WAKE_WORD
)
from core.stt import STTListener
from core.llm import route_query, should_bypass_router, http_session
from core.model_persistence import ensure_qwen_loaded, mark_qwen_used, unload_qwen
from core.tts import tts, SentenceBuffer
from core.function_executor import executor as function_executor

# ── Functions that are direct actions (execute → Qwen confirms) ─────────────
ACTION_FUNCTIONS = {
    "control_light", "set_timer", "set_alarm",
    "create_calendar_event", "add_task", "web_search"
}

# ── RGB functions — all route through function_executor then Qwen confirms ───
# BUG FIX: these were missing entirely, causing every RGB voice command to
# fall into the else-branch and be treated as plain chat (signalrgb never called).
RGB_FUNCTIONS = {
    "control_rgb_lighting",          # high-level dispatcher
    "check_signalrgb_connection",    # no args
    "get_current_rgb_effect",        # no args
    "set_rgb_brightness",            # brightness: int
    "enable_rgb_canvas",             # enabled: bool
    "get_installed_rgb_effects",     # no args
    "get_rgb_effect_info",           # effect_id: str
    "apply_rgb_effect",              # effect_id: str
    "get_rgb_effect_presets",        # effect_id: str
}


class VoiceAssistant(QObject):
    """Main voice assistant orchestrator."""

    # Signals for UI updates
    wake_word_detected = Signal()
    speech_recognized = Signal(str)
    processing_started = Signal()
    processing_finished = Signal()
    error_occurred = Signal(str)
    # GUI update signals
    timer_set = Signal(int, str)   # seconds, label
    alarm_added = Signal()
    calendar_updated = Signal()
    task_added = Signal()

    def __init__(self):
        super().__init__()
        self.stt_listener: Optional[STTListener] = None
        self.running = False
        self.messages = [
            {
                'role': 'system',
                'content': (
                    'You are a helpful assistant. Respond in short, complete sentences. '
                    'Never use emojis or special characters. '
                    'Keep responses concise and conversational.'
                )
            }
        ]
        self.current_session_id = None

    def initialize(self) -> bool:
        """Initialize voice assistant components."""
        try:
            print(f"{CYAN}[VoiceAssistant] Initializing voice assistant components...{RESET}")

            print(f"{CYAN}[VoiceAssistant] Creating STT listener...{RESET}")
            self.stt_listener = STTListener(
                wake_word_callback=self._on_wake_word,
                speech_callback=self._on_speech
            )
            print(f"{CYAN}[VoiceAssistant] ✓ STT listener created{RESET}")

            print(f"{CYAN}[VoiceAssistant] Initializing STT models...{RESET}")
            if not self.stt_listener.initialize():
                print(f"{GRAY}[VoiceAssistant] ✗ Failed to initialize STT.{RESET}")
                return False
            print(f"{CYAN}[VoiceAssistant] ✓ STT initialized{RESET}")

            if not tts.piper_exe:
                print(f"{CYAN}[VoiceAssistant] Initializing TTS...{RESET}")
                tts.initialize()
                print(f"{CYAN}[VoiceAssistant] ✓ TTS initialized{RESET}")

            print(f"{CYAN}[VoiceAssistant] ✓ Voice assistant initialized successfully{RESET}")
            return True
        except Exception as e:
            print(f"{GRAY}[VoiceAssistant] ✗ Initialization error: {e}{RESET}")
            import traceback
            traceback.print_exc()
            return False

    def start(self):
        """Start the voice assistant."""
        if self.running:
            return
        if not self.stt_listener:
            if not self.initialize():
                return
        self.running = True
        self.stt_listener.start()
        print(f"{CYAN}[VoiceAssistant] Voice assistant started. Say '{GREEN}{WAKE_WORD}{RESET}{CYAN}' to activate.{RESET}")

    def stop(self):
        """Stop the voice assistant."""
        if not self.running:
            return
        self.running = False
        if self.stt_listener:
            self.stt_listener.stop()
        print(f"{GRAY}[VoiceAssistant] Voice assistant stopped.{RESET}")

    def _on_wake_word(self):
        """Handle wake word detection."""
        print(f"{GREEN}[VoiceAssistant] ✓ Wake word callback received!{RESET}")
        print(f"{GREEN}[VoiceAssistant] Emitting wake_word_detected signal...{RESET}")
        self.wake_word_detected.emit()
        print(f"{GREEN}[VoiceAssistant] ✓ Signal emitted. Listening for speech...{RESET}")

    def _on_speech(self, text: str):
        """Handle recognized speech after wake word."""
        if not text.strip():
            return

        # BUG FIX: original code stripped "ada" but wake word is WAKE_WORD ("jarvis").
        # Strip the actual configured wake word instead so it works regardless of
        # what wake word is set in config.py.
        text = text.lower().replace(WAKE_WORD.lower(), "").strip()
        if not text:
            return

        self.speech_recognized.emit(text)
        self.processing_started.emit()

        print(f"{CYAN}[VoiceAssistant] Processing: {text}{RESET}")

        thread = threading.Thread(
            target=self._process_query,
            args=(text,),
            daemon=True
        )
        thread.start()

    def _process_query(self, user_text: str):
        """Process user query through the pipeline."""
        try:
            # Step 1: Route through FunctionGemma
            if should_bypass_router(user_text):
                func_name = "nonthinking"
                params = {"prompt": user_text}
            else:
                func_name, params = route_query(user_text)

            print(f"{GRAY}[VoiceAssistant] Routed to: {func_name} | params: {params}{RESET}")

            # Step 2: Dispatch based on function type

            if func_name in ACTION_FUNCTIONS:
                # ── Core action functions ────────────────────────────────────
                result = function_executor.execute(func_name, params)
                response_text = result.get("message", "Done.")

                # Emit GUI signals for relevant actions
                if func_name == "set_timer" and result.get("success"):
                    seconds = result.get("data", {}).get("seconds", 0)
                    label = result.get("data", {}).get("label", "Timer")
                    self.timer_set.emit(seconds, label)
                elif func_name == "set_alarm" and result.get("success"):
                    self.alarm_added.emit()
                elif func_name == "create_calendar_event" and result.get("success"):
                    self.calendar_updated.emit()
                elif func_name == "add_task" and result.get("success"):
                    self.task_added.emit()

                self._generate_response_with_context(func_name, result, user_text)

            elif func_name in RGB_FUNCTIONS:
                # ── RGB lighting functions ───────────────────────────────────
                # Route to function_executor which calls signalrgb.py methods.
                # Then pass the result to Qwen so it can give a spoken confirmation.
                print(f"{CYAN}[VoiceAssistant] Executing RGB function: {func_name}{RESET}")
                result = function_executor.execute(func_name, params)
                print(f"{CYAN}[VoiceAssistant] RGB result: {result}{RESET}")
                self._generate_response_with_context(func_name, result, user_text)

            elif func_name == "get_system_info":
                # ── System state query ───────────────────────────────────────
                result = function_executor.execute(func_name, params)
                self._generate_response_with_context(func_name, result, user_text, enable_thinking=True)

            elif func_name in ("thinking", "nonthinking"):
                # ── Direct Qwen passthrough ──────────────────────────────────
                enable_thinking = (func_name == "thinking")
                self._stream_qwen_response(user_text, enable_thinking)

            else:
                # ── Unknown function — fallback to chat ──────────────────────
                print(f"{GRAY}[VoiceAssistant] Unknown function '{func_name}', falling back to chat.{RESET}")
                self._stream_qwen_response(user_text, False)

        except Exception as e:
            error_msg = f"Error processing query: {e}"
            print(f"{GRAY}[VoiceAssistant] {error_msg}{RESET}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(error_msg)
            self.processing_finished.emit()

    def _generate_response_with_context(
        self, func_name: str, result: dict, user_text: str, enable_thinking: bool = False
    ):
        """Generate Qwen response with function execution context."""
        try:
            if not ensure_qwen_loaded():
                print(f"{GRAY}[VoiceAssistant] Failed to load Qwen model.{RESET}")
                self.processing_finished.emit()
                return

            mark_qwen_used()

            success = result.get("success", False)
            message = result.get("message", "")

            # Build context string for Qwen
            if func_name == "get_system_info" and success:
                data = result.get("data", {})
                context_parts = []
                if data.get("timers"):
                    context_parts.append(f"Active timers: {data['timers']}")
                if data.get("alarms"):
                    context_parts.append(f"Alarms: {data['alarms']}")
                if data.get("calendar_today"):
                    context_parts.append(f"Today's events: {data['calendar_today']}")
                if data.get("tasks"):
                    pending = [t for t in data['tasks'] if not t.get('completed')]
                    context_parts.append(f"Pending tasks: {len(pending)} items")
                if data.get("smart_devices"):
                    on_devices = [d['name'] for d in data['smart_devices'] if d.get('is_on')]
                    context_parts.append(f"Devices on: {on_devices if on_devices else 'none'}")
                if data.get("weather"):
                    w = data['weather']
                    context_parts.append(f"Weather: {w.get('temp')}°F, {w.get('condition')}")
                if data.get("news"):
                    titles = [item.get('title', '')[:50] for item in data['news'][:3]]
                    context_parts.append(f"Top news: {', '.join(titles)}")
                context_msg = "SYSTEM CONTEXT:\n" + "\n".join(context_parts) if context_parts else "No system information available."

            elif func_name in RGB_FUNCTIONS:
                # Give Qwen specific context so it can give a natural spoken confirmation
                data = result.get("data", {})
                if success:
                    if func_name == "apply_rgb_effect":
                        effect = params_from_result(data, "effect_id", "the effect")
                        context_msg = f"RGB lighting: successfully applied effect '{effect}'."
                    elif func_name == "set_rgb_brightness":
                        brightness = params_from_result(data, "brightness", "the requested level")
                        context_msg = f"RGB lighting: brightness set to {brightness}%."
                    elif func_name == "enable_rgb_canvas":
                        state = "enabled" if data.get("enabled", True) else "disabled"
                        context_msg = f"RGB lighting canvas has been {state}."
                    elif func_name == "control_rgb_lighting":
                        context_msg = f"RGB lighting control executed successfully. {message}"
                    elif func_name == "check_signalrgb_connection":
                        context_msg = "SignalRGB is connected and available."
                    elif func_name == "get_current_rgb_effect":
                        effect_name = data.get("effect_name") or data.get("name") or "unknown"
                        context_msg = f"The current RGB lighting effect is: {effect_name}."
                    elif func_name == "get_installed_rgb_effects":
                        effects = data.get("effects", [])
                        names = [e.get("name", e.get("id", "?")) for e in effects[:5]]
                        context_msg = f"Installed RGB effects include: {', '.join(names)}." if names else "No effects found."
                    elif func_name in ("get_rgb_effect_info", "get_rgb_effect_presets"):
                        context_msg = f"RGB effect info retrieved. {message}"
                    else:
                        context_msg = f"RGB function {func_name} completed. {message}"
                else:
                    context_msg = f"RGB lighting command failed. {message}"
            else:
                context_msg = f"Function {func_name} executed. Success: {success}. Result: {message}"

            # Trim context window
            if len(self.messages) > MAX_HISTORY:
                self.messages = [self.messages[0]] + self.messages[-(MAX_HISTORY - 1):]

            context_prompt = f"{context_msg}\n\nUser asked: {user_text}\n\nRespond naturally and concisely."
            self.messages.append({'role': 'user', 'content': context_prompt})

            payload = {
                "model": RESPONDER_MODEL,
                "messages": self.messages,
                "stream": True,
                "think": enable_thinking,
                "keep_alive": "5m"
            }

            sentence_buffer = SentenceBuffer()
            full_response = ""

            with http_session.post(f"{OLLAMA_URL}/chat", json=payload, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            msg = chunk.get('message', {})
                            if 'content' in msg and msg['content']:
                                content = msg['content']
                                full_response += content
                                for s in sentence_buffer.add(content):
                                    tts.queue_sentence(s)
                        except Exception:
                            continue

            rem = sentence_buffer.flush()
            if rem:
                tts.queue_sentence(rem)

            self.messages.append({'role': 'assistant', 'content': full_response})
            mark_qwen_used()

            print(f"{GREEN}[VoiceAssistant] Response generated.{RESET}")
            self.processing_finished.emit()

        except Exception as e:
            print(f"{GRAY}[VoiceAssistant] Error generating response: {e}{RESET}")
            import traceback
            traceback.print_exc()
            self.processing_finished.emit()

    def _stream_qwen_response(self, user_text: str, enable_thinking: bool):
        """Stream direct Qwen response (no function execution)."""
        try:
            if not ensure_qwen_loaded():
                print(f"{GRAY}[VoiceAssistant] Failed to load Qwen model.{RESET}")
                self.processing_finished.emit()
                return

            mark_qwen_used()

            if len(self.messages) > MAX_HISTORY:
                self.messages = [self.messages[0]] + self.messages[-(MAX_HISTORY - 1):]

            self.messages.append({'role': 'user', 'content': user_text})

            payload = {
                "model": RESPONDER_MODEL,
                "messages": self.messages,
                "stream": True,
                "think": enable_thinking,
                "keep_alive": "5m"
            }

            sentence_buffer = SentenceBuffer()
            full_response = ""

            with http_session.post(f"{OLLAMA_URL}/chat", json=payload, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            msg = chunk.get('message', {})
                            if 'content' in msg and msg['content']:
                                content = msg['content']
                                full_response += content
                                for s in sentence_buffer.add(content):
                                    tts.queue_sentence(s)
                        except Exception:
                            continue

            rem = sentence_buffer.flush()
            if rem:
                tts.queue_sentence(rem)

            self.messages.append({'role': 'assistant', 'content': full_response})
            mark_qwen_used()

            print(f"{GREEN}[VoiceAssistant] Response generated.{RESET}")
            self.processing_finished.emit()

        except Exception as e:
            print(f"{GRAY}[VoiceAssistant] Error streaming response: {e}{RESET}")
            self.processing_finished.emit()


# ---------------------------------------------------------------------------
# Helper — safely extract a value from result data for response building
# ---------------------------------------------------------------------------
def params_from_result(data: dict, key: str, fallback: str) -> str:
    return str(data.get(key, fallback))


# Global voice assistant instance
voice_assistant = VoiceAssistant()