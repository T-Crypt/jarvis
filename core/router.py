"""
FunctionGemma Router - Routes user prompts to appropriate functions.
Supports 18 functions: 6 actions, 1 context, 2 passthrough, 1 RGB high-level, 8 RGB low-level.
"""

import os
import warnings

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", message=".*generation flags are not valid.*")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, logging as transformers_logging
from transformers.utils import get_json_schema
from typing import Tuple, Dict, Any
import time
import re
import json
from huggingface_hub import snapshot_download

transformers_logging.set_verbosity_error()

from config import LOCAL_ROUTER_PATH, HF_ROUTER_REPO

DEBUG_ROUTER = False


# ---------------------------------------------------------------------------
# Tool stub definitions — must exactly match train_function_gemma.py stubs
# so the model sees the same schemas at inference time as it did at training.
# ---------------------------------------------------------------------------

# ── Core tools ──────────────────────────────────────────────────────────────

def control_light(action: str, device_name: str = None, brightness: int = None, color: str = None) -> str:
    """
    Control smart lights - turn on, off, dim, or change color.

    Args:
        action: Action to perform: on, off, dim, toggle
        device_name: Name of the light or room
        brightness: Brightness level 0-100
        color: Color name or hex code
    """
    return "result"


def set_timer(duration: str, label: str = None) -> str:
    """
    Set a countdown timer.

    Args:
        duration: Duration like '5 minutes' or '1 hour'
        label: Optional label for the timer
    """
    return "result"


def set_alarm(time: str, label: str = None) -> str:
    """
    Set an alarm for a specific time.

    Args:
        time: Time for alarm like '7am' or '14:30'
        label: Optional label
    """
    return "result"


def create_calendar_event(title: str, date: str = None, time: str = None, duration: int = None) -> str:
    """
    Create a calendar event.

    Args:
        title: Event title
        date: Date like 'tomorrow' or '2024-01-15'
        time: Time like '3pm'
        duration: Duration in minutes
    """
    return "result"


def add_task(text: str, priority: str = None) -> str:
    """
    Add a task to the to-do list.

    Args:
        text: Task description
        priority: Priority level
    """
    return "result"


def web_search(query: str) -> str:
    """
    Search the web for information using DuckDuckGo.
    Returns up to 5 search results including titles, snippets, and URLs.

    Use this when the user asks to:
    - Search for information online
    - Look up current events or news
    - Find facts, definitions, or explanations
    - Research a topic

    Args:
        query: Search query string (e.g., "Python programming best practices")

    Returns:
        Search results with titles, body snippets (200 chars), and URLs
    """
    return "result"


def get_system_info() -> str:
    """
    Get comprehensive current system state snapshot.

    Returns information about:
    - Current time and date
    - Active countdown timers (label, remaining time)
    - Upcoming alarms (time, label)
    - Today's calendar events (title, time)
    - Pending tasks from to-do list (text, completion status)
    - Smart home devices (name, on/off status, type)
    - Current weather (temperature, condition, high/low)
    - Recent news headlines (title, category, URL)

    Use this when the user asks:
    - "What's on my schedule today?"
    - "What's my current status?"
    - "What do I have coming up?"
    - "Give me a summary of everything"
    - Questions about their timers, tasks, or calendar
    """
    return "result"


def thinking(prompt: str) -> str:
    """
    Use for complex queries requiring multi-step reasoning, math, coding,
    debugging, detailed analysis, or long-form writing.

    Args:
        prompt: The user's original prompt
    """
    return "result"


def nonthinking(prompt: str) -> str:
    """
    Use for simple queries: greetings, single-fact questions, short
    acknowledgements, or any request not requiring deep reasoning.

    Args:
        prompt: The user's original prompt
    """
    return "result"


# ── RGB high-level control ────────────────────────────────────────────────────

def control_rgb_lighting(action: str, brightness: int = None, effect_name: str = None) -> str:
    """
    Control PC RGB lighting via SignalRGB - set brightness, enable/disable
    canvas, or apply effects.

    Args:
        action: Action to perform: set_brightness, enable_canvas,
                disable_canvas, apply_effect
        brightness: Brightness level 0-100 (used with set_brightness action)
        effect_name: Name of the effect to apply (used with apply_effect action)
    """
    return "result"


# ── RGB low-level API tools ───────────────────────────────────────────────────

def check_signalrgb_connection() -> str:
    """
    Check if SignalRGB API is available for RGB lighting control.
    """
    return "result"


def get_current_rgb_effect() -> str:
    """
    Get the currently active RGB lighting effect from SignalRGB.
    """
    return "result"


def set_rgb_brightness(brightness: int) -> str:
    """
    Set the global RGB lighting brightness level via SignalRGB API.

    Args:
        brightness: Brightness level 0-100
    """
    return "result"


def enable_rgb_canvas(enabled: bool) -> str:
    """
    Enable or disable the RGB lighting canvas in SignalRGB.

    Args:
        enabled: True to enable the canvas, False to disable it
    """
    return "result"


def get_installed_rgb_effects() -> str:
    """
    Get the list of all installed RGB lighting effects from SignalRGB.
    """
    return "result"


def get_rgb_effect_info(effect_id: str) -> str:
    """
    Get detailed information about a specific RGB lighting effect.

    Args:
        effect_id: The ID of the effect to query
    """
    return "result"


def apply_rgb_effect(effect_id: str) -> str:
    """
    Apply a specific RGB lighting effect by ID via SignalRGB.

    Args:
        effect_id: The ID of the effect to apply
    """
    return "result"


def get_rgb_effect_presets(effect_id: str) -> str:
    """
    Get available presets for a specific RGB lighting effect.

    Args:
        effect_id: The ID of the effect to get presets for
    """
    return "result"


# ---------------------------------------------------------------------------
# Pre-compute tool schemas — must match train_function_gemma.py exactly
# ---------------------------------------------------------------------------
TOOLS = [
    # Core
    get_json_schema(control_light),
    get_json_schema(set_timer),
    get_json_schema(set_alarm),
    get_json_schema(create_calendar_event),
    get_json_schema(add_task),
    get_json_schema(web_search),
    get_json_schema(get_system_info),
    get_json_schema(thinking),
    get_json_schema(nonthinking),
    # RGB
    get_json_schema(control_rgb_lighting),
    get_json_schema(check_signalrgb_connection),
    get_json_schema(get_current_rgb_effect),
    get_json_schema(set_rgb_brightness),
    get_json_schema(enable_rgb_canvas),
    get_json_schema(get_installed_rgb_effects),
    get_json_schema(get_rgb_effect_info),
    get_json_schema(apply_rgb_effect),
    get_json_schema(get_rgb_effect_presets),
]

SYSTEM_MSG = "You are a model that can do function calling with the following functions"

# BUG FIX: was missing all 9 RGB functions — they were never recognized,
# causing _parse_function_call to always fall through to "nonthinking".
VALID_FUNCTIONS = {
    # Core
    "control_light", "set_timer", "set_alarm", "create_calendar_event",
    "add_task", "web_search", "get_system_info", "thinking", "nonthinking",
    # RGB
    "control_rgb_lighting",
    "check_signalrgb_connection", "get_current_rgb_effect",
    "set_rgb_brightness", "enable_rgb_canvas", "get_installed_rgb_effects",
    "get_rgb_effect_info", "apply_rgb_effect", "get_rgb_effect_presets",
}

# Functions that take no arguments
NO_ARG_FUNCTIONS = {
    "get_system_info",
    "check_signalrgb_connection",
    "get_current_rgb_effect",
    "get_installed_rgb_effects",
}


def ensure_model_available(model_path: str = LOCAL_ROUTER_PATH) -> str:
    """
    Ensure the router model is available locally.
    Downloads from Hugging Face if not found.
    """
    if os.path.exists(model_path) and os.path.isdir(model_path):
        if os.path.exists(os.path.join(model_path, "model.safetensors")):
            return model_path

    print(f"[Router] Model not found at {model_path}")
    print(f"[Router] Downloading from Hugging Face: {HF_ROUTER_REPO}...")

    try:
        downloaded_path = snapshot_download(
            repo_id=HF_ROUTER_REPO,
            local_dir=model_path,
            local_dir_use_symlinks=False
        )
        print(f"[Router] ✓ Model downloaded to {downloaded_path}")
        return downloaded_path
    except Exception as e:
        raise RuntimeError(
            f"Failed to download model from {HF_ROUTER_REPO}: {e}\n"
            f"Train the model locally with: python train_function_gemma.py"
        )


class FunctionGemmaRouter:
    """Routes user prompts to appropriate functions using fine-tuned FunctionGemma."""

    def __init__(self, model_path: str = LOCAL_ROUTER_PATH, compile_model: bool = False):
        model_path = ensure_model_available(model_path)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading FunctionGemma Router on {device.upper()}...")
        start = time.time()

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        dtype = torch.bfloat16 if device == "cuda" else torch.float32

        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=dtype,
            device_map=device,
        )
        self.model.eval()

        if compile_model:
            try:
                self.model = torch.compile(self.model, mode="reduce-overhead")
                print("Model compiled with torch.compile()")
            except Exception as e:
                print(f"torch.compile() not available: {e}")

        print(f"Router loaded in {time.time() - start:.2f}s")
        print(f"Device: {self.model.device}, Dtype: {self.model.dtype}")

    @torch.inference_mode()
    def route(self, user_prompt: str) -> Tuple[str, Dict[str, Any]]:
        """
        Route a user prompt to the appropriate function.

        Returns:
            Tuple of (function_name, arguments_dict)
        """
        messages = [
            {"role": "developer", "content": SYSTEM_MSG},
            {"role": "user", "content": user_prompt},
        ]

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tools=TOOLS,
            add_generation_prompt=True,
            tokenize=False
        )

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=False,
            use_cache=True,
            pad_token_id=self.tokenizer.pad_token_id,
        )

        new_tokens = outputs[0][inputs['input_ids'].shape[1]:]
        response = self.tokenizer.decode(new_tokens, skip_special_tokens=False)

        if DEBUG_ROUTER:
            print(f"\n{'='*50}")
            print(f"[Router DEBUG] User prompt: {user_prompt}")
            print(f"[Router DEBUG] Raw response: {repr(response)}")
            print(f"{'='*50}")

        return self._parse_function_call(response, user_prompt)

    def _parse_function_call(self, response: str, user_prompt: str) -> Tuple[str, Dict[str, Any]]:
        """Parse the model's response to extract function name and arguments."""
        for func_name in VALID_FUNCTIONS:
            if f"call:{func_name}" in response:
                args = self._extract_arguments(response, func_name, user_prompt)
                return func_name, args

        return "nonthinking", {"prompt": user_prompt}

    def _extract_arguments(self, response: str, func_name: str, user_prompt: str) -> Dict[str, Any]:
        """Extract arguments from the response."""

        # Passthrough functions always get the prompt
        if func_name in ("thinking", "nonthinking"):
            return {"prompt": user_prompt}

        # No-argument functions
        if func_name in NO_ARG_FUNCTIONS:
            return {}

        # Parse custom format: call:func_name{key:<escape>value<escape>, ...}
        pattern = rf"call:{func_name}\{{([^}}]+)\}}"
        match = re.search(pattern, response)

        if match:
            args_str = match.group(1)
            args = {}
            arg_pattern = r'(\w+):(?:<escape>([^<]*)<escape>|([^,]+))'
            for arg_match in re.finditer(arg_pattern, args_str):
                key = arg_match.group(1)
                val_escaped = arg_match.group(2)
                val_unescaped = arg_match.group(3)
                value = val_escaped if val_escaped is not None else val_unescaped

                if value is None:
                    continue
                value = value.strip()
                if value.isdigit():
                    args[key] = int(value)
                elif value.lower() in ('true', 'false'):
                    args[key] = value.lower() == 'true'
                else:
                    args[key] = value

            if args:
                return args

        # ---------------------------------------------------------------------------
        # Fallback argument extraction — used when model output can't be parsed.
        # These are last-resort sensible defaults, not primary parsing.
        # ---------------------------------------------------------------------------

        # Core functions
        if func_name == "control_light":
            return {"action": "toggle", "device_name": user_prompt}
        elif func_name == "set_timer":
            return {"duration": user_prompt}
        elif func_name == "set_alarm":
            return {"time": user_prompt}
        elif func_name == "create_calendar_event":
            return {"title": user_prompt}
        elif func_name == "add_task":
            return {"text": user_prompt}
        elif func_name == "web_search":
            return {"query": user_prompt}

        # RGB high-level
        elif func_name == "control_rgb_lighting":
            return {"action": "apply_effect", "effect_name": user_prompt}

        # RGB low-level — single required arg functions
        elif func_name == "set_rgb_brightness":
            return {"brightness": 75}   # safe default
        elif func_name == "enable_rgb_canvas":
            return {"enabled": True}    # safe default: turn on
        elif func_name in ("get_rgb_effect_info", "apply_rgb_effect", "get_rgb_effect_presets"):
            return {"effect_id": user_prompt}

        return {}

    def route_with_timing(self, user_prompt: str) -> Tuple[Tuple[str, Dict], float]:
        """Route with timing info."""
        start = time.time()
        result = self.route(user_prompt)
        elapsed = time.time() - start
        return result, elapsed


if __name__ == "__main__":
    router = FunctionGemmaRouter(compile_model=False)

    test_prompts = [
        # Core actions
        ("Turn on the living room lights", "control_light"),
        ("Set a timer for 10 minutes", "set_timer"),
        ("Wake me up at 7am", "set_alarm"),
        ("Schedule meeting tomorrow at 3pm", "create_calendar_event"),
        ("Add buy groceries to my list", "add_task"),
        ("Search for Italian recipes", "web_search"),
        ("What's on my calendar today?", "get_system_info"),
        # Passthrough
        ("Explain quantum computing", "thinking"),
        ("Hello there!", "nonthinking"),
        # RGB high-level
        ("Set RGB brightness to 75", "control_rgb_lighting"),
        ("Apply Rainbow effect", "control_rgb_lighting"),
        ("Enable RGB canvas", "control_rgb_lighting"),
        # RGB low-level
        ("Is SignalRGB connected?", "check_signalrgb_connection"),
        ("What RGB effect is active?", "get_current_rgb_effect"),
        ("Set RGB brightness to 50", "set_rgb_brightness"),
        ("Turn off the RGB canvas", "enable_rgb_canvas"),
        ("List installed RGB effects", "get_installed_rgb_effects"),
        ("Tell me about the Breathing effect", "get_rgb_effect_info"),
        ("Load the Aurora effect", "apply_rgb_effect"),
        ("Show presets for Rainbow", "get_rgb_effect_presets"),
    ]

    print("\n" + "="*70)
    print("FUNCTION CALLING ROUTER TEST — 18 functions")
    print("="*70)

    total_time = 0
    correct = 0

    for prompt, expected in test_prompts:
        (func_name, args), elapsed = router.route_with_timing(prompt)
        total_time += elapsed
        match = "✓" if func_name == expected else "✗"
        if func_name == expected:
            correct += 1
        print(f"\n[{match}] {prompt}")
        print(f"    → {func_name}({args}) [{elapsed*1000:.0f}ms]")

    avg_time = total_time / len(test_prompts)
    print(f"\n{'='*70}")
    print(f"Accuracy: {correct}/{len(test_prompts)} ({100*correct/len(test_prompts):.0f}%)")
    print(f"Average routing time: {avg_time*1000:.0f}ms per prompt")
    print(f"Total time: {total_time:.2f}s for {len(test_prompts)} prompts")