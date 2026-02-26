"""
Train FunctionGemma for function calling — 10 tools.

Core (9):  control_light, set_timer, set_alarm, create_calendar_event,
           add_task, web_search, get_system_info, thinking, nonthinking
RGB  (1):  control_rgb_lighting  (effect name only, PowerShell URL scheme)
"""

import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers.utils import get_json_schema
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig, PeftModel
from collections import Counter

MODEL_ID   = "google/functiongemma-270m-it"
OUTPUT_DIR = "functiongemma-270m-ft"
MERGED_DIR = "merged_model"
DATA_FILE  = "training_dataset_functions.jsonl"
MAX_LENGTH = 768
EPOCHS     = 8


# ---------------------------------------------------------------------------
# Tool stubs — docstrings drive get_json_schema(). Keep in sync with
# generate_training_data.py and router.py or training will be misaligned.
# ---------------------------------------------------------------------------

def control_light(action: str, device_name: str = None,
                  brightness: int = None, color: str = None) -> str:
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


def create_calendar_event(title: str, date: str = None,
                          time: str = None, duration: int = None) -> str:
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
    Search the web for information.

    Args:
        query: Search query
    """
    return "result"


def get_system_info() -> str:
    """
    Get current system state including timers, calendar, tasks, devices,
    and weather.
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


def control_rgb_lighting(effect_name: str) -> str:
    """
    Change the PC RGB lighting effect via SignalRGB.
    Available effects: Sakura, Hydrogen, Black Ice, Spiral Rainbow, Coral,
    Neon Fire, Emerald Dream, Rainbow Rise, Spin, Enigma, Corrosive,
    Pixel Fill, Cyber Rain, Fire And Ice

    Args:
        effect_name: Name of the RGB effect to apply
    """
    return "result"


# ---------------------------------------------------------------------------
# Build tool schema list — order must match generate_training_data.py TOOLS
# ---------------------------------------------------------------------------
TOOLS = [
    get_json_schema(control_light),
    get_json_schema(set_timer),
    get_json_schema(set_alarm),
    get_json_schema(create_calendar_event),
    get_json_schema(add_task),
    get_json_schema(web_search),
    get_json_schema(get_system_info),
    get_json_schema(thinking),
    get_json_schema(nonthinking),
    get_json_schema(control_rgb_lighting),
]

VALID_FUNCTIONS = {schema["function"]["name"] for schema in TOOLS}
SYSTEM_MSG = "You are a model that can do function calling with the following functions"


# ---------------------------------------------------------------------------
# Dataset preprocessing
# ---------------------------------------------------------------------------

def rebuild_sample(sample):
    """
    Replace the stored tools list with the authoritative TOOLS schemas so every
    training example sees the exact same tool context as at inference time.
    """
    messages = sample.get("messages", [])
    user_content = tool_name = tool_args = None

    for msg in messages:
        if msg["role"] == "user":
            user_content = msg["content"]
        elif msg["role"] == "assistant" and msg.get("tool_calls"):
            fn = msg["tool_calls"][0]["function"]
            tool_name = fn["name"]
            tool_args = fn.get("arguments", {})

    if not user_content or not tool_name:
        return sample

    if tool_name not in VALID_FUNCTIONS:
        print(f"  ⚠  Skipping unknown function: '{tool_name}'")
        return sample

    return {
        "messages": [
            {"role": "developer", "content": SYSTEM_MSG},
            {"role": "user",      "content": user_content},
            {"role": "assistant", "tool_calls": [
                {"type": "function", "function": {
                    "name": tool_name, "arguments": tool_args
                }}
            ]},
        ],
        "tools": TOOLS,
    }


# ---------------------------------------------------------------------------
# Main training routine
# ---------------------------------------------------------------------------

def train():
    print("=" * 60)
    print(f"Model  : {MODEL_ID}")
    print(f"Data   : {DATA_FILE}")
    print(f"Tools  : {len(TOOLS)}")
    print("=" * 60)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    # Load & inspect
    print(f"\nLoading dataset from {DATA_FILE}...")
    raw = load_dataset("json", data_files=DATA_FILE, split="train")
    print(f"Raw examples: {len(raw)}")

    counts = Counter(
        s["messages"][2]["tool_calls"][0]["function"]["name"]
        for s in raw
        if len(s.get("messages", [])) > 2 and s["messages"][2].get("tool_calls")
    )
    print("\nFunction distribution:")
    unknown = []
    for fn, n in sorted(counts.items()):
        mark = "✓" if fn in VALID_FUNCTIONS else "❌"
        print(f"  {mark}  {fn:<40} {n:>4}")
        if fn not in VALID_FUNCTIONS:
            unknown.append(fn)
    if unknown:
        print(f"\n  ⚠  Unknown functions will be skipped: {unknown}")
        print("     Regenerate dataset with: python generate_training_data.py")

    # Rebuild with authoritative schemas
    print("\nRebuilding with current tool schemas...")
    dataset = raw.map(rebuild_sample, remove_columns=raw.column_names)
    print(f"Final examples: {len(dataset)}")

    # Token length check
    sample_text = tokenizer.apply_chat_template(
        dataset[0]["messages"],
        tools=dataset[0]["tools"],
        add_generation_prompt=False,
        tokenize=False
    )
    n_tok = len(tokenizer.encode(sample_text))
    print(f"Sample[0] token length: {n_tok}  (max_length={MAX_LENGTH})")
    if n_tok > MAX_LENGTH:
        print("  ⚠  Sample exceeds max_length — some examples will be truncated")

    # Load model
    print("\nLoading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="eager",
    )
    print(f"Device: {model.device}  |  DType: {model.dtype}")

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        task_type="CAUSAL_LM",
    )

    sft_args = SFTConfig(
        output_dir=OUTPUT_DIR,
        max_length=MAX_LENGTH,
        packing=False,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        gradient_checkpointing=True,
        optim="adamw_torch_fused",
        logging_steps=10,
        save_strategy="epoch",
        learning_rate=2e-5,
        bf16=True,
        lr_scheduler_type="constant",
        overwrite_output_dir=True,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_args,
        train_dataset=dataset,
        peft_config=peft_config,
        processing_class=tokenizer,
    )

    print(f"\nTraining {len(dataset)} examples × {EPOCHS} epochs...")
    print("=" * 60)
    trainer.train()

    print("\nSaving LoRA adapter...")
    trainer.save_model(OUTPUT_DIR)

    del model, trainer
    torch.cuda.empty_cache()

    print("\nMerging adapter into base model...")
    base = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto",
    )
    merged = PeftModel.from_pretrained(base, OUTPUT_DIR).merge_and_unload()

    print(f"Saving merged model → {MERGED_DIR}/")
    merged.save_pretrained(MERGED_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_DIR)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print(f"  Merged model: {MERGED_DIR}/")
    print("\nQuick route test:")
    print('  python -c "from core.router import FunctionGemmaRouter; r=FunctionGemmaRouter(); print(r.route(\'set my rgb to cyber rain\'))"')
    print("=" * 60)


if __name__ == "__main__":
    train()