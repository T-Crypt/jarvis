"""
Train FunctionGemma for function calling with 18 tools
Auto HuggingFace authentication + safe overwrite behavior
"""

import os
import shutil
import getpass
import json
from pathlib import Path
from collections import Counter

import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers.utils import get_json_schema
from huggingface_hub import login, get_token
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig, PeftModel

os.environ["TENSORBOARD_LOGGING_DIR"] = "runs"

# ============================================================
# CONFIG
# ============================================================

MODEL_ID = "google/functiongemma-270m-it"
OUTPUT_DIR = "functiongemma-270m-ft"
MERGED_OUTPUT_DIR = "merged_model"
DATA_FILE = "training_dataset_functions.jsonl"

SYSTEM_MSG = "You are a model that can do function calling."

# ============================================================
# HUGGINGFACE AUTHENTICATION
# ============================================================


def ensure_hf_login():
    """
    Ensure the environment has a Hugging Face token; if not, prompt the user.

    Uses:
        get_token - returns token if already saved in the environment.

    Raises:
        RuntimeError: If no token is provided interactively.
    """
    token = get_token()
    if token:
        print("✓ Hugging Face token already present")
        return

    print("\nHugging Face login required.")
    token = getpass.getpass("Enter Hugging Face token: ").strip()

    if not token:
        raise RuntimeError("No token provided")

    login(token=token, add_to_git_credential=True)
    print("✓ Login successful")


# ============================================================
# SAFE DIRECTORY RESET
# ============================================================


def reset_dir(path):
    """
    Remove and recreate the directory at `path` to ensure it's empty.

    Args:
        path: Path to remove and recreate.

    Returns:
        None
    """
    if os.path.exists(path):
        print(f"Removing existing directory: {path}")
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


# ============================================================
# GPU VRAM AUTO TUNER
# ============================================================


def auto_training_profile():
    """
    Guess a reasonable per-device batch and accumulation profile from GPU VRAM.

    Returns:
        dict: {batch: int, grad_accum: int, bf16: bool}
    """
    if not torch.cuda.is_available():
        return dict(batch=1, grad_accum=4, bf16=False)

    try:
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    except Exception:
        # fallback if device properties not available
        vram = 12.0
    print(f"Detected VRAM: {vram:.1f} GB")

    if vram >= 20:
        return dict(batch=4, grad_accum=1, bf16=True)
    if vram >= 12:
        return dict(batch=2, grad_accum=2, bf16=True)
    if vram >= 8:
        return dict(batch=1, grad_accum=4, bf16=True)
    return dict(batch=1, grad_accum=8, bf16=False)


# ============================================================
# DATASET SCHEMA VALIDATION
# ============================================================


def validate_sample(sample):
    """
    Validate JSONL sample structure:
      - must contain "messages" list
      - must contain at least one user and one assistant message
      - assistant message must include tool_calls with a function name that is valid

    Args:
        sample: single dataset example (a dict)

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        msgs = sample["messages"]
        assert isinstance(msgs, list)
        user_found = False
        assistant_found = False
        for m in msgs:
            if m["role"] == "user":
                user_found = True
            if m["role"] == "assistant":
                assistant_found = True
                if "tool_calls" not in m:
                    return False
                tc = m["tool_calls"]
                if not isinstance(tc, list) or len(tc) == 0:
                    return False
                fn = tc[0]["function"]["name"]
                if fn not in VALID_FUNCTIONS:
                    print(f"Invalid function skipped: {fn}")
                    return False
        return user_found and assistant_found
    except Exception as e:
        # If anything goes wrong while validating, mark sample invalid
        # Print minimal message for debugging
        # (Don't raise to allow dataset.filter to continue)
        print("Dataset validation error:", e)
        return False


# ============================================================
# TOOL STUBS (with docstrings)
# Each function must have full `Args:` and `Returns:` sections so
# transformers.utils.get_json_schema can parse them.
# ============================================================

def control_light(action: str, device_name: str = None, brightness: int = None, color: str = None) -> str:
    """
    Control a smart light device.

    Args:
        action: Action to perform (on, off, toggle, dim).
        device_name: Name of the device or room.
        brightness: Brightness level (0-100).
        color: Color name or hex code.

    Returns:
        Status string describing the result.
    """
    return "result"


def set_timer(duration: str, label: str = None) -> str:
    """
    Set a countdown timer.

    Args:
        duration: Duration string, e.g., '5 minutes'.
        label: Optional label for the timer.

    Returns:
        Status string confirming the timer creation.
    """
    return "result"


def set_alarm(time: str, label: str = None) -> str:
    """
    Set an alarm.

    Args:
        time: Time string, e.g., '07:00' or '7am'.
        label: Optional label for the alarm.

    Returns:
        Status string confirming the alarm creation.
    """
    return "result"


def create_calendar_event(title: str, date: str = None, time: str = None, duration: int = None) -> str:
    """
    Create a calendar event.

    Args:
        title: Event title.
        date: Event date string, e.g., '2026-05-01'.
        time: Event time string, e.g., '14:00'.
        duration: Duration in minutes.

    Returns:
        Status string confirming the event creation.
    """
    return "result"


def add_task(text: str, priority: str = None) -> str:
    """
    Add a task to the to-do list.

    Args:
        text: Task description.
        priority: Optional priority label (low, medium, high).

    Returns:
        Status string confirming the task addition.
    """
    return "result"


def web_search(query: str) -> str:
    """
    Perform a web search.

    Args:
        query: Search query text.

    Returns:
        Search results string or summary.
    """
    return "result"


def get_system_info() -> str:
    """
    Return system info: timers, calendar events, tasks, devices.

    Returns:
        JSON-like status string describing current system state.
    """
    return "result"


def thinking(prompt: str) -> str:
    """
    Multi-step reasoning function.

    Args:
        prompt: User prompt for multi-step reasoning.

    Returns:
        Computed result string (long-form reasoning).
    """
    return "result"


def nonthinking(prompt: str) -> str:
    """
    Simple, single-step responses.

    Args:
        prompt: User prompt.

    Returns:
        Short result string.
    """
    return "result"


# ── RGB HIGH-LEVEL CONTROL ──

def control_rgb_lighting(action: str, brightness: int = None, effect_name: str = None) -> str:
    """
    Control PC RGB lighting via SignalRGB.

    Args:
        action: One of 'set_brightness', 'enable_canvas', 'disable_canvas', 'apply_effect'.
        brightness: Brightness level (0-100), used when action is 'set_brightness'.
        effect_name: Name of effect to apply when action is 'apply_effect'.

    Returns:
        Status string confirming the action.
    """
    return "result"


# ── RGB LOW-LEVEL API ──

def check_signalrgb_connection() -> str:
    """
    Check if SignalRGB API is available.

    Returns:
        Status string indicating connectivity (e.g., 'connected' or 'unavailable').
    """
    return "result"


def get_current_rgb_effect() -> str:
    """
    Return currently active RGB effect.

    Returns:
        The ID or name of the currently active RGB effect.
    """
    return "result"


def set_rgb_brightness(brightness: int) -> str:
    """
    Set global RGB brightness 0-100.

    Args:
        brightness: Brightness level (0-100).

    Returns:
        Status string confirming the brightness change.
    """
    return "result"


def enable_rgb_canvas(enabled: bool) -> str:
    """
    Enable or disable the RGB canvas.

    Args:
        enabled: True to enable the canvas, False to disable it.

    Returns:
        Status string indicating new canvas state.
    """
    return "result"


def get_installed_rgb_effects() -> str:
    """
    Get all installed RGB effects.

    Returns:
        A list (stringified) of installed RGB effect names/IDs.
    """
    return "result"


def get_rgb_effect_info(effect_id: str) -> str:
    """
    Get details for a specific RGB effect.

    Args:
        effect_id: ID or name of the RGB effect.

    Returns:
        Detailed info about the effect (string or JSON).
    """
    return "result"


def apply_rgb_effect(effect_id: str) -> str:
    """
    Apply a specific RGB effect by ID.

    Args:
        effect_id: ID or name of the RGB effect.

    Returns:
        Status string confirming the effect application.
    """
    return "result"


def get_rgb_effect_presets(effect_id: str) -> str:
    """
    Get presets for a specific RGB effect.

    Args:
        effect_id: ID or name of the RGB effect.

    Returns:
        List (string) of presets available for that effect.
    """
    return "result"


# ============================================================
# GENERATE SCHEMAS
# ============================================================

# Build TOOLS list by generating JSON schema entries for each function.
TOOLS = []
_function_list = [
    control_light, set_timer, set_alarm, create_calendar_event, add_task, web_search,
    get_system_info, thinking, nonthinking, control_rgb_lighting,
    check_signalrgb_connection, get_current_rgb_effect, set_rgb_brightness,
    enable_rgb_canvas, get_installed_rgb_effects, get_rgb_effect_info,
    apply_rgb_effect, get_rgb_effect_presets
]

# Wrap schema generation with a helpful error message if any function's docstring is malformed.
for fn in _function_list:
    try:
        schema = get_json_schema(fn)
        TOOLS.append(schema)
    except Exception as e:
        # Re-raise with more context to help debugging docstring problems
        raise RuntimeError(f"Error generating JSON schema for function '{fn.__name__}': {e}") from e

# Set of valid function names for dataset validation and rebuild step
VALID_FUNCTIONS = {s["function"]["name"] for s in TOOLS}


# ============================================================
# DATASET REBUILD
# ============================================================


def rebuild(sample):
    """
    Convert original conversation sample into canonical training structure.
    Keeps developer/system, user, assistant(function_call) roles and attaches tool schemas.

    Args:
        sample: original dict with "messages" list.

    Returns:
        dict: {"messages": [...], "tools": TOOLS}
    """
    user = None
    tool = None
    args = {}
    for m in sample["messages"]:
        if m["role"] == "user":
            user = m.get("content", "")
        if m["role"] == "assistant" and "tool_calls" in m:
            tc = m["tool_calls"][0]["function"]
            tool = tc["name"]
            args = tc.get("arguments", {})
    if not user or tool not in VALID_FUNCTIONS:
        # return original sample unchanged if can't rebuild
        return sample
    return {
        "messages": [
            {"role": "developer", "content": SYSTEM_MSG},
            {"role": "user", "content": user},
            {"role": "assistant", "tool_calls": [
                {"type": "function", "function": {"name": tool, "arguments": args}}
            ]}
        ],
        "tools": TOOLS
    }


# ============================================================
# PROMPT / TOKENIZATION HELPERS
# ============================================================


def render_messages_to_text(messages):
    """
    Convert a list of role/content dicts into a single training text string.

    Args:
        messages: list of {"role": str, "content": str} or assistant function call dict.

    Returns:
        str: Combined prompt/response text for causal LM training.
    """
    out = []
    for m in messages:
        role = m.get("role", "")
        if role == "assistant" and "tool_calls" in m:
            tc = m["tool_calls"][0]["function"]
            fn_name = tc.get("name")
            fn_args = tc.get("arguments", {})
            # function call serialized as JSON so model sees function name + args
            out.append(f"<assistant_function_call name={fn_name} args={json.dumps(fn_args, ensure_ascii=False)} />")
        else:
            content = m.get("content", "")
            out.append(f"<{role}>{content}</{role}>")
    # join segments with newlines - keep small, consistent separators
    return "\n".join(out)


def tokenize_and_build_labels(example, tokenizer, max_length=1024):
    """
    Convert a rebuilt example into tokenized input_ids and labels.

    Args:
        example: dict as returned from rebuild()
        tokenizer: AutoTokenizer instance
        max_length: max token length

    Returns:
        dict with input_ids, attention_mask, labels
    """
    text = render_messages_to_text(example["messages"])
    # Tokenize; return PyTorch-style input ids
    tok = tokenizer(text, truncation=True, max_length=max_length, padding=False)
    input_ids = tok["input_ids"]
    # For causal LM fine-tuning we set labels = input_ids
    return {"input_ids": input_ids, "attention_mask": tok.get("attention_mask", [1] * len(input_ids)), "labels": input_ids}


# ============================================================
# TRAINING FUNCTION
# ============================================================


def train():
    # HuggingFace login
    ensure_hf_login()

    # Auto VRAM profile
    profile = auto_training_profile()
    print(f"Auto training profile: {profile}")

    # Overwrite directories
    reset_dir(OUTPUT_DIR)
    reset_dir(MERGED_OUTPUT_DIR)

    # Load tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)

    # Load dataset
    print("Loading dataset...")
    raw = load_dataset("json", data_files=DATA_FILE, split="train")
    dataset = raw.filter(validate_sample)
    dataset = dataset.map(rebuild, remove_columns=raw.column_names)
    print(f"Rebuilt dataset size: {len(dataset)}")

    # ==============================
    # Tokenize dataset
    # ==============================
    def tokenize_sample(sample):
        # Encode user + assistant messages
        content = ""
        for msg in sample["messages"]:
            role = msg["role"]
            if role == "developer":  # SYSTEM_MSG
                continue
            if role == "user":
                content += f"<|user|> {msg['content']}\n"
            elif role == "assistant" and "tool_calls" in msg:
                fn = msg["tool_calls"][0]["function"]["name"]
                args = msg["tool_calls"][0]["function"].get("arguments", {})
                content += f"<|assistant|> Call {fn} with {args}\n"
            else:
                content += f"<|assistant|> {msg.get('content','')}\n"
        return tokenizer(content, truncation=True, max_length=1024)

    print("Tokenizing dataset...")
    tokenized = dataset.map(tokenize_sample)
    print(f"Tokenized dataset size: {len(tokenized)}")

    # Convert to arrow with input_ids, attention_mask, labels
    print("Final dataset size:", len(tokenized))

    # Safe dtype selection for bf16
    if profile["bf16"] and torch.cuda.is_available():
        try:
            torch_dtype = torch.bfloat16
        except Exception:
            torch_dtype = torch.float32
    else:
        torch_dtype = torch.float32

    # Load model
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        dtype=torch.bfloat16 if profile["bf16"] else torch.float32,
        device_map="auto"
    )

    # LoRA config
    peft = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM"
    )

    args = SFTConfig(
        output_dir=OUTPUT_DIR,
        max_length=1024,
        num_train_epochs=8,
        per_device_train_batch_size=profile["batch"],
        gradient_accumulation_steps=profile["grad_accum"],
        gradient_checkpointing=True,
        bf16=profile["bf16"],
        learning_rate=2e-5,
        save_strategy="epoch",
        report_to="tensorboard",
        packing=False
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=tokenized,
        peft_config=peft,
    )

    print("\n=== TRAINING START ===")
    trainer.train()
    trainer.save_model(OUTPUT_DIR)

    del trainer
    del model
    torch.cuda.empty_cache()

    # ====================================================
    # MERGE
    # ====================================================
    print("\nMerging LoRA adapter...")

    base = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch_dtype,
        device_map="auto"
    )
    merged = PeftModel.from_pretrained(base, OUTPUT_DIR)
    merged = merged.merge_and_unload()
    merged.save_pretrained(MERGED_OUTPUT_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_OUTPUT_DIR)

    print("\n✓ TRAINING COMPLETE")
    print(f"Merged model overwritten at: {MERGED_OUTPUT_DIR}")


if __name__ == "__main__":
    train()