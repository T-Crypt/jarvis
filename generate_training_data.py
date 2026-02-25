"""
Generate training dataset for function calling model.
Creates ~50 examples per function across all functions.

Functions covered:
  Core:         control_light, set_timer, set_alarm, create_calendar_event,
                add_task, web_search, get_system_info
  Routing:      thinking, nonthinking
  RGB (high):   control_rgb_lighting
  RGB (low):    check_signalrgb_connection, get_current_rgb_effect,
                set_rgb_brightness, enable_rgb_canvas,
                get_installed_rgb_effects, get_rgb_effect_info,
                apply_rgb_effect, get_rgb_effect_presets
"""
import json
import random

# ---------------------------------------------------------------------------
# Tool definitions
# NOTE: every dict in this list needs THREE closing braces at the end:
#   }  → closes "parameters"
#   }  → closes the inner "function" value
#   }  → closes the outer tool dict
# ---------------------------------------------------------------------------
TOOLS = [
    # ── Core tools ──────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "control_light", "description": "Control smart lights - turn on, off, dim, or change color", "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "device_name": {"type": "string"}, "brightness": {"type": "integer"}, "color": {"type": "string"}}, "required": ["action"]}}},
    {"type": "function", "function": {"name": "set_timer", "description": "Set a countdown timer", "parameters": {"type": "object", "properties": {"duration": {"type": "string"}, "label": {"type": "string"}}, "required": ["duration"]}}},
    {"type": "function", "function": {"name": "set_alarm", "description": "Set an alarm for a specific time", "parameters": {"type": "object", "properties": {"time": {"type": "string"}, "label": {"type": "string"}}, "required": ["time"]}}},
    {"type": "function", "function": {"name": "create_calendar_event", "description": "Create a calendar event", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "date": {"type": "string"}, "time": {"type": "string"}, "duration": {"type": "integer"}}, "required": ["title"]}}},
    {"type": "function", "function": {"name": "add_task", "description": "Add a task to the to-do list", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "priority": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "web_search", "description": "Search the web for information", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "get_system_info", "description": "Get current system state including timers, calendar, tasks, devices, and weather", "parameters": {"type": "object", "properties": {}}}},

    # ── Thinking / routing tools ─────────────────────────────────────────────
    {"type": "function", "function": {"name": "thinking", "description": "Use for complex queries requiring multi-step reasoning, math, coding, debugging, detailed analysis, or long-form writing", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}}, "required": ["prompt"]}}},
    {"type": "function", "function": {"name": "nonthinking", "description": "Use for simple queries: greetings, single-fact questions, short acknowledgements, or any request not requiring deep reasoning", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}}, "required": ["prompt"]}}},

    # ── RGB high-level control ────────────────────────────────────────────────
    {"type": "function", "function": {"name": "control_rgb_lighting", "description": "Control PC RGB lighting via SignalRGB - set brightness, enable/disable canvas, or apply effects", "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "brightness": {"type": "integer"}, "effect_name": {"type": "string"}}, "required": ["action"]}}},

    # ── RGB low-level API tools ───────────────────────────────────────────────
    {"type": "function", "function": {"name": "check_signalrgb_connection", "description": "Check if SignalRGB API is available for RGB lighting control", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_current_rgb_effect", "description": "Get the currently active RGB lighting effect", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "set_rgb_brightness", "description": "Set the global RGB lighting brightness level (0-100)", "parameters": {"type": "object", "properties": {"brightness": {"type": "integer"}}, "required": ["brightness"]}}},
    {"type": "function", "function": {"name": "enable_rgb_canvas", "description": "Enable or disable the RGB lighting canvas", "parameters": {"type": "object", "properties": {"enabled": {"type": "boolean"}}, "required": ["enabled"]}}},
    {"type": "function", "function": {"name": "get_installed_rgb_effects", "description": "Get list of all installed RGB lighting effects", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_rgb_effect_info", "description": "Get detailed information about a specific RGB effect", "parameters": {"type": "object", "properties": {"effect_id": {"type": "string"}}, "required": ["effect_id"]}}},
    {"type": "function", "function": {"name": "apply_rgb_effect", "description": "Apply a specific RGB lighting effect by ID", "parameters": {"type": "object", "properties": {"effect_id": {"type": "string"}}, "required": ["effect_id"]}}},
    {"type": "function", "function": {"name": "get_rgb_effect_presets", "description": "Get available presets for a specific RGB effect", "parameters": {"type": "object", "properties": {"effect_id": {"type": "string"}}, "required": ["effect_id"]}}},
]

SYSTEM_MSG = "You are a model that can do function calling with the following functions"


def make_example(user_content, func_name, args):
    return {
        "messages": [
            {"role": "developer", "content": SYSTEM_MSG},
            {"role": "user", "content": user_content},
            {"role": "assistant", "tool_calls": [{"type": "function", "function": {"name": func_name, "arguments": args}}]},
        ],
        "tools": TOOLS,
    }


# ============ CONTROL_LIGHT (50 examples) ============
control_light_examples = [
    ("Turn on the living room lights", {"action": "on", "device_name": "living room"}),
    ("Turn off the bedroom light", {"action": "off", "device_name": "bedroom"}),
    ("Dim the kitchen lights to 50%", {"action": "dim", "device_name": "kitchen", "brightness": 50}),
    ("Switch on all the lights", {"action": "on", "device_name": "all"}),
    ("Make the office light blue", {"action": "on", "device_name": "office", "color": "blue"}),
    ("Set the bathroom light to 25%", {"action": "dim", "device_name": "bathroom", "brightness": 25}),
    ("Toggle the hallway lights", {"action": "toggle", "device_name": "hallway"}),
    ("Lights off everywhere", {"action": "off", "device_name": "all"}),
    ("Change the living room to warm white", {"action": "on", "device_name": "living room", "color": "warm white"}),
    ("Set brightness to full in the garage", {"action": "dim", "device_name": "garage", "brightness": 100}),
    ("Turn the porch light on", {"action": "on", "device_name": "porch"}),
    ("Kill the lights in the den", {"action": "off", "device_name": "den"}),
    ("Brighten the dining room", {"action": "dim", "device_name": "dining room", "brightness": 100}),
    ("Set bedroom to red", {"action": "on", "device_name": "bedroom", "color": "red"}),
    ("Lower the office lights to 30", {"action": "dim", "device_name": "office", "brightness": 30}),
    ("Lights on in basement", {"action": "on", "device_name": "basement"}),
    ("Switch off kitchen light", {"action": "off", "device_name": "kitchen"}),
    ("Make it brighter in here", {"action": "dim", "device_name": "current room", "brightness": 80}),
    ("Dim all lights to 40%", {"action": "dim", "device_name": "all", "brightness": 40}),
    ("Set the nursery to soft pink", {"action": "on", "device_name": "nursery", "color": "pink"}),
    ("Turn on lamp", {"action": "on", "device_name": "lamp"}),
    ("Shut off the desk light", {"action": "off", "device_name": "desk"}),
    ("Bedroom lights at half", {"action": "dim", "device_name": "bedroom", "brightness": 50}),
    ("Change color to green in kids room", {"action": "on", "device_name": "kids room", "color": "green"}),
    ("Maximize brightness in study", {"action": "dim", "device_name": "study", "brightness": 100}),
    ("Turn off outside lights", {"action": "off", "device_name": "outside"}),
    ("Switch the attic light on", {"action": "on", "device_name": "attic"}),
    ("Dim patio lights", {"action": "dim", "device_name": "patio", "brightness": 40}),
    ("Set all lights to cool white", {"action": "on", "device_name": "all", "color": "cool white"}),
    ("Make the closet light brighter", {"action": "dim", "device_name": "closet", "brightness": 75}),
    ("Lights to 10% in master bedroom", {"action": "dim", "device_name": "master bedroom", "brightness": 10}),
    ("Turn on reading lamp", {"action": "on", "device_name": "reading lamp"}),
    ("Office to daylight mode", {"action": "on", "device_name": "office", "color": "daylight"}),
    ("Kill all the lights", {"action": "off", "device_name": "all"}),
    ("Set movie mode lighting", {"action": "dim", "device_name": "living room", "brightness": 20}),
    ("Bathroom at full brightness", {"action": "dim", "device_name": "bathroom", "brightness": 100}),
    ("Purple light in gaming room", {"action": "on", "device_name": "gaming room", "color": "purple"}),
    ("Lower all lights", {"action": "dim", "device_name": "all", "brightness": 30}),
    ("Switch on the ceiling fan light", {"action": "on", "device_name": "ceiling fan"}),
    ("Turn off stairway lights", {"action": "off", "device_name": "stairway"}),
    ("Entryway light on", {"action": "on", "device_name": "entryway"}),
    ("Dim the table lamp to 60", {"action": "dim", "device_name": "table lamp", "brightness": 60}),
    ("Set accent lights to orange", {"action": "on", "device_name": "accent", "color": "orange"}),
    ("Guest room lights off", {"action": "off", "device_name": "guest room"}),
    ("Brighten up the workspace", {"action": "dim", "device_name": "workspace", "brightness": 90}),
    ("Night light on", {"action": "on", "device_name": "night light"}),
    ("Set laundry room to 50%", {"action": "dim", "device_name": "laundry room", "brightness": 50}),
    ("Yellow lights in sunroom", {"action": "on", "device_name": "sunroom", "color": "yellow"}),
    ("Mudroom light off", {"action": "off", "device_name": "mudroom"}),
    ("Front porch to warm", {"action": "on", "device_name": "front porch", "color": "warm"}),
    ("Turn on the chandelier", {"action": "on", "device_name": "chandelier"}),
    ("Kill the basement lights", {"action": "off", "device_name": "basement"}),
    ("Set reading light to 40%", {"action": "dim", "device_name": "reading light", "brightness": 40}),
    ("Change bedroom to cool white", {"action": "on", "device_name": "bedroom", "color": "cool white"}),
    ("Lights up in the hallway", {"action": "dim", "device_name": "hallway", "brightness": 100}),
    ("Turn off the aquarium light", {"action": "off", "device_name": "aquarium"}),
    ("Set deck lights to amber", {"action": "on", "device_name": "deck", "color": "amber"}),
    ("Dim living room to 10%", {"action": "dim", "device_name": "living room", "brightness": 10}),
    ("Switch on the garage light", {"action": "on", "device_name": "garage"}),
    ("Make the kitchen light blue", {"action": "on", "device_name": "kitchen", "color": "blue"}),
    ("Turn off all upstairs lights", {"action": "off", "device_name": "upstairs"}),
    ("Set master bath to daylight", {"action": "on", "device_name": "master bath", "color": "daylight"}),
    ("Brighten the vanity mirror", {"action": "dim", "device_name": "vanity mirror", "brightness": 85}),
    ("Turn on the floodlights", {"action": "on", "device_name": "floodlights"}),
    ("Lower the dining light to 25", {"action": "dim", "device_name": "dining room", "brightness": 25}),
    ("Set strip lights to purple", {"action": "on", "device_name": "strip lights", "color": "purple"}),
    ("Lights out in the guest room", {"action": "off", "device_name": "guest room"}),
    ("Turn on the pantry light", {"action": "on", "device_name": "pantry"}),
    ("Set bedside lamp to warm", {"action": "on", "device_name": "bedside lamp", "color": "warm"}),
    ("Dim the foyer lights", {"action": "dim", "device_name": "foyer", "brightness": 50}),
    ("Switch off the attic", {"action": "off", "device_name": "attic"}),
    ("Make the gym light red", {"action": "on", "device_name": "gym", "color": "red"}),
    ("Set nursery light to 5%", {"action": "dim", "device_name": "nursery", "brightness": 5}),
    ("Turn on the closet light", {"action": "on", "device_name": "closet"}),
    ("Lights off in the study", {"action": "off", "device_name": "study"}),
    ("Set patio to soft white", {"action": "on", "device_name": "patio", "color": "soft white"}),
    ("Increase brightness in kitchen", {"action": "dim", "device_name": "kitchen", "brightness": 90}),
    ("Turn off the nightstand light", {"action": "off", "device_name": "nightstand"}),
    ("Set under cabinet lights to green", {"action": "on", "device_name": "under cabinet", "color": "green"}),
    ("Turn on the shed light", {"action": "on", "device_name": "shed"}),
    ("Dim the movie room to zero", {"action": "off", "device_name": "movie room"}),
    ("Set hallway to 20 percent", {"action": "dim", "device_name": "hallway", "brightness": 20}),
    ("Change living room to candle light", {"action": "on", "device_name": "living room", "color": "candle light"}),
    ("Switch on the desk lamp", {"action": "on", "device_name": "desk lamp"}),
    ("Turn off the laundry light", {"action": "off", "device_name": "laundry"}),
    ("Set balcony lights to yellow", {"action": "on", "device_name": "balcony", "color": "yellow"}),
    ("Brighten the garage", {"action": "dim", "device_name": "garage", "brightness": 100}),
    ("Turn on the floor lamp", {"action": "on", "device_name": "floor lamp"}),
    ("Set toilet light to blue", {"action": "on", "device_name": "toilet", "color": "blue"}),
    ("Dim the art light", {"action": "dim", "device_name": "art light", "brightness": 60}),
    ("Lights out in the library", {"action": "off", "device_name": "library"}),
    ("Turn on the monitor backlights", {"action": "on", "device_name": "monitor backlights"}),
    ("Set garden lights to white", {"action": "on", "device_name": "garden", "color": "white"}),
    ("Lower the bedroom lights", {"action": "dim", "device_name": "bedroom", "brightness": 40}),
    ("Switch off the workbench", {"action": "off", "device_name": "workbench"}),
    ("Make the entryway bright", {"action": "dim", "device_name": "entryway", "brightness": 100}),
    ("Turn on the lava lamp", {"action": "on", "device_name": "lava lamp"}),
    ("Set ceiling lights to 75%", {"action": "dim", "device_name": "ceiling", "brightness": 75}),
    ("Change bathroom to magenta", {"action": "on", "device_name": "bathroom", "color": "magenta"}),
    ("Turn off the showcase light", {"action": "off", "device_name": "showcase"}),
]

# ============ SET_TIMER (50 examples) ============
set_timer_examples = [
    ("Set a timer for 10 minutes", {"duration": "10 minutes"}),
    ("Timer for 5 mins", {"duration": "5 minutes"}),
    ("Set a 30 second timer", {"duration": "30 seconds"}),
    ("Start a one hour timer", {"duration": "1 hour"}),
    ("Timer 15 minutes for eggs", {"duration": "15 minutes", "label": "eggs"}),
    ("Set pasta timer 8 minutes", {"duration": "8 minutes", "label": "pasta"}),
    ("Create a timer for 45 minutes", {"duration": "45 minutes"}),
    ("Set a 2 minute timer", {"duration": "2 minutes"}),
    ("Timer for laundry 1 hour", {"duration": "1 hour", "label": "laundry"}),
    ("Start 20 minute workout timer", {"duration": "20 minutes", "label": "workout"}),
    ("Set timer 3 minutes", {"duration": "3 minutes"}),
    ("Pizza timer 12 minutes", {"duration": "12 minutes", "label": "pizza"}),
    ("Timer for 25 minutes pomodoro", {"duration": "25 minutes", "label": "pomodoro"}),
    ("Set a quick 1 minute timer", {"duration": "1 minute"}),
    ("90 second timer please", {"duration": "90 seconds"}),
    ("Start timer for tea steeping 4 minutes", {"duration": "4 minutes", "label": "tea"}),
    ("Timer 7 minutes for rice", {"duration": "7 minutes", "label": "rice"}),
    ("Set 35 minute timer", {"duration": "35 minutes"}),
    ("Nap timer for 20 minutes", {"duration": "20 minutes", "label": "nap"}),
    ("Create meditation timer 10 minutes", {"duration": "10 minutes", "label": "meditation"}),
    ("Timer for cookies 11 minutes", {"duration": "11 minutes", "label": "cookies"}),
    ("Set a half hour timer", {"duration": "30 minutes"}),
    ("Timer 2 hours for roast", {"duration": "2 hours", "label": "roast"}),
    ("Quick timer 45 seconds", {"duration": "45 seconds"}),
    ("Set break timer 15 minutes", {"duration": "15 minutes", "label": "break"}),
    ("Timer for 6 minutes", {"duration": "6 minutes"}),
    ("Bread timer 40 minutes", {"duration": "40 minutes", "label": "bread"}),
    ("Set study timer 50 minutes", {"duration": "50 minutes", "label": "study"}),
    ("Timer 90 minutes for movie", {"duration": "90 minutes", "label": "movie"}),
    ("Start countdown 5 minutes", {"duration": "5 minutes"}),
    ("Set 18 minute timer", {"duration": "18 minutes"}),
    ("Chicken timer for 25 minutes", {"duration": "25 minutes", "label": "chicken"}),
    ("Create timer 1 hour 30 minutes", {"duration": "1 hour 30 minutes"}),
    ("Timer for stretching 8 minutes", {"duration": "8 minutes", "label": "stretching"}),
    ("Set reminder timer 10 minutes", {"duration": "10 minutes", "label": "reminder"}),
    ("Coffee timer 4 minutes", {"duration": "4 minutes", "label": "coffee"}),
    ("Timer 55 minutes", {"duration": "55 minutes"}),
    ("Set game timer 2 hours", {"duration": "2 hours", "label": "game"}),
    ("Quick 30 second countdown", {"duration": "30 seconds"}),
    ("Timer for veggies 9 minutes", {"duration": "9 minutes", "label": "veggies"}),
    ("Set focus timer 45 minutes", {"duration": "45 minutes", "label": "focus"}),
    ("Sauce timer 20 minutes", {"duration": "20 minutes", "label": "sauce"}),
    ("Timer 3 hours", {"duration": "3 hours"}),
    ("Set parking meter reminder 2 hours", {"duration": "2 hours", "label": "parking"}),
    ("Timer for face mask 15 minutes", {"duration": "15 minutes", "label": "face mask"}),
    ("Create 22 minute timer", {"duration": "22 minutes"}),
    ("Timer steaks 6 minutes", {"duration": "6 minutes", "label": "steaks"}),
    ("Set charging timer 1 hour", {"duration": "1 hour", "label": "charging"}),
    ("Baby bottle timer 3 minutes", {"duration": "3 minutes", "label": "bottle"}),
    ("Start 14 minute timer", {"duration": "14 minutes"}),
]

# ============ SET_ALARM (50 examples) ============
set_alarm_examples = [
    ("Set an alarm for 7am", {"time": "7am"}),
    ("Wake me up at 6:30", {"time": "6:30am"}),
    ("Alarm for 8 o'clock", {"time": "8am"}),
    ("Set alarm 5:45am", {"time": "5:45am"}),
    ("Wake up alarm 7:15", {"time": "7:15am"}),
    ("Set morning alarm 6am", {"time": "6am", "label": "morning"}),
    ("Alarm at 9am for meeting", {"time": "9am", "label": "meeting"}),
    ("Set an alarm for noon", {"time": "12pm"}),
    ("Wake me at 5am", {"time": "5am"}),
    ("Alarm 10:30pm", {"time": "10:30pm"}),
    ("Set alarm for 4:30 in the morning", {"time": "4:30am"}),
    ("Create alarm 7:45am", {"time": "7:45am"}),
    ("Wake up call at 6:15", {"time": "6:15am"}),
    ("Set an 8:30 alarm", {"time": "8:30am"}),
    ("Alarm for tomorrow 7am", {"time": "7am"}),
    ("Set my workout alarm 5:30am", {"time": "5:30am", "label": "workout"}),
    ("Alarm at 11pm for bed", {"time": "11pm", "label": "bedtime"}),
    ("Wake me 6:45", {"time": "6:45am"}),
    ("Set alarm 3pm for pickup", {"time": "3pm", "label": "pickup"}),
    ("Morning alarm 7:30", {"time": "7:30am", "label": "morning"}),
    ("Set an alarm for 2pm", {"time": "2pm"}),
    ("Alarm 6:20am", {"time": "6:20am"}),
    ("Set school alarm 6:30am", {"time": "6:30am", "label": "school"}),
    ("Wake me up at 7:05", {"time": "7:05am"}),
    ("Alarm for 5:15am", {"time": "5:15am"}),
    ("Set lunch reminder alarm noon", {"time": "12pm", "label": "lunch"}),
    ("Alarm at 10am", {"time": "10am"}),
    ("Set early alarm 4am", {"time": "4am"}),
    ("Wake up at quarter to seven", {"time": "6:45am"}),
    ("Alarm for 8am sharp", {"time": "8am"}),
    ("Set nap alarm 3:30pm", {"time": "3:30pm", "label": "nap"}),
    ("Alarm 9:15am", {"time": "9:15am"}),
    ("Set gym alarm 5am", {"time": "5am", "label": "gym"}),
    ("Wake me at 7:20", {"time": "7:20am"}),
    ("Alarm for 6:40am", {"time": "6:40am"}),
    ("Set medication alarm 8pm", {"time": "8pm", "label": "medication"}),
    ("Alarm at 11:30am", {"time": "11:30am"}),
    ("Set 7:55 alarm", {"time": "7:55am"}),
    ("Wake up call 6am", {"time": "6am"}),
    ("Alarm for 4pm meeting", {"time": "4pm", "label": "meeting"}),
    ("Set alarm 5:50am", {"time": "5:50am"}),
    ("Alarm at seven thirty", {"time": "7:30am"}),
    ("Set call alarm 2:30pm", {"time": "2:30pm", "label": "call"}),
    ("Wake me 6:35am", {"time": "6:35am"}),
    ("Alarm for 9:45am", {"time": "9:45am"}),
    ("Set flight alarm 4:15am", {"time": "4:15am", "label": "flight"}),
    ("Alarm at 1pm", {"time": "1pm"}),
    ("Set 6:55 alarm", {"time": "6:55am"}),
    ("Wake me up at eight", {"time": "8am"}),
    ("Alarm 7:10am", {"time": "7:10am"}),
]

# ============ CREATE_CALENDAR_EVENT (50 examples) ============
calendar_examples = [
    ("Schedule a meeting tomorrow at 3pm", {"title": "meeting", "date": "tomorrow", "time": "3pm"}),
    ("Add dentist appointment Friday 2pm", {"title": "dentist appointment", "date": "Friday", "time": "2pm"}),
    ("Create event lunch with John Monday noon", {"title": "lunch with John", "date": "Monday", "time": "12pm"}),
    ("Schedule team standup daily 9am", {"title": "team standup", "time": "9am"}),
    ("Add call with mom Saturday 11am", {"title": "call with mom", "date": "Saturday", "time": "11am"}),
    ("Schedule doctor visit next Tuesday 10am", {"title": "doctor visit", "date": "next Tuesday", "time": "10am"}),
    ("Create meeting with boss at 4pm", {"title": "meeting with boss", "time": "4pm"}),
    ("Add gym session tomorrow 6am", {"title": "gym session", "date": "tomorrow", "time": "6am"}),
    ("Schedule haircut Wednesday 3:30pm", {"title": "haircut", "date": "Wednesday", "time": "3:30pm"}),
    ("Add birthday party Saturday 5pm", {"title": "birthday party", "date": "Saturday", "time": "5pm"}),
    ("Create dinner reservation Friday 7pm", {"title": "dinner reservation", "date": "Friday", "time": "7pm"}),
    ("Schedule oil change Monday morning", {"title": "oil change", "date": "Monday", "time": "morning"}),
    ("Add parent teacher conference Thursday 4pm", {"title": "parent teacher conference", "date": "Thursday", "time": "4pm"}),
    ("Create interview tomorrow 2:30pm", {"title": "interview", "date": "tomorrow", "time": "2:30pm"}),
    ("Schedule vet visit next week", {"title": "vet visit", "date": "next week"}),
    ("Add yoga class Tuesday 7am", {"title": "yoga class", "date": "Tuesday", "time": "7am"}),
    ("Create lunch meeting Wednesday noon", {"title": "lunch meeting", "date": "Wednesday", "time": "12pm"}),
    ("Schedule car service Friday 8am", {"title": "car service", "date": "Friday", "time": "8am"}),
    ("Add movie night Saturday 8pm", {"title": "movie night", "date": "Saturday", "time": "8pm"}),
    ("Create client call Monday 11am", {"title": "client call", "date": "Monday", "time": "11am"}),
    ("Schedule grocery shopping Sunday 10am", {"title": "grocery shopping", "date": "Sunday", "time": "10am"}),
    ("Add concert tickets event Friday 7pm", {"title": "concert", "date": "Friday", "time": "7pm"}),
    ("Create brunch Sunday 11am", {"title": "brunch", "date": "Sunday", "time": "11am"}),
    ("Schedule code review Thursday 2pm", {"title": "code review", "date": "Thursday", "time": "2pm"}),
    ("Add anniversary dinner next Saturday", {"title": "anniversary dinner", "date": "next Saturday"}),
    ("Create project deadline Friday", {"title": "project deadline", "date": "Friday"}),
    ("Schedule flight Tuesday 6am", {"title": "flight", "date": "Tuesday", "time": "6am"}),
    ("Add therapy session Wednesday 3pm", {"title": "therapy session", "date": "Wednesday", "time": "3pm"}),
    ("Create book club meeting Thursday 6pm", {"title": "book club", "date": "Thursday", "time": "6pm"}),
    ("Schedule presentation Monday 10am", {"title": "presentation", "date": "Monday", "time": "10am"}),
    ("Add coffee with Sarah tomorrow 9am", {"title": "coffee with Sarah", "date": "tomorrow", "time": "9am"}),
    ("Create piano lesson Saturday 2pm", {"title": "piano lesson", "date": "Saturday", "time": "2pm"}),
    ("Schedule date night Friday 6:30pm", {"title": "date night", "date": "Friday", "time": "6:30pm"}),
    ("Add soccer practice Tuesday 4pm", {"title": "soccer practice", "date": "Tuesday", "time": "4pm"}),
    ("Create team lunch Wednesday 12:30", {"title": "team lunch", "date": "Wednesday", "time": "12:30pm"}),
    ("Schedule eye exam next month", {"title": "eye exam", "date": "next month"}),
    ("Add game night Saturday 7pm", {"title": "game night", "date": "Saturday", "time": "7pm"}),
    ("Create conference call Friday 9am", {"title": "conference call", "date": "Friday", "time": "9am"}),
    ("Schedule massage Thursday 5pm", {"title": "massage", "date": "Thursday", "time": "5pm"}),
    ("Add study group Sunday 3pm", {"title": "study group", "date": "Sunday", "time": "3pm"}),
    ("Create board meeting Monday 8am", {"title": "board meeting", "date": "Monday", "time": "8am"}),
    ("Schedule wine tasting Saturday", {"title": "wine tasting", "date": "Saturday"}),
    ("Add swimming lessons Wednesday 4:30pm", {"title": "swimming lessons", "date": "Wednesday", "time": "4:30pm"}),
    ("Create networking event Thursday 6pm", {"title": "networking event", "date": "Thursday", "time": "6pm"}),
    ("Schedule pickup from airport Sunday 3pm", {"title": "airport pickup", "date": "Sunday", "time": "3pm"}),
    ("Add dance class Tuesday 7pm", {"title": "dance class", "date": "Tuesday", "time": "7pm"}),
    ("Create all hands meeting Friday 2pm", {"title": "all hands meeting", "date": "Friday", "time": "2pm"}),
    ("Schedule tutoring session Monday 4pm", {"title": "tutoring session", "date": "Monday", "time": "4pm"}),
    ("Add potluck dinner Saturday noon", {"title": "potluck dinner", "date": "Saturday", "time": "12pm"}),
    ("Create sprint planning Monday 9:30am", {"title": "sprint planning", "date": "Monday", "time": "9:30am"}),
]

# ============ ADD_TASK (50 examples) ============
task_examples = [
    ("Add buy groceries to my task list", {"text": "buy groceries"}),
    ("Add to todo list: call mom", {"text": "call mom"}),
    ("Put pay bills on the task list", {"text": "pay bills"}),
    ("Add new task: send email", {"text": "send email"}),
    ("Add to task list: water plants", {"text": "water plants"}),
    ("Create task pick up dry cleaning", {"text": "pick up dry cleaning"}),
    ("Add to list: take out trash", {"text": "take out trash"}),
    ("Add book flight tickets to my to-do list", {"text": "book flight tickets"}),
    ("Add task: schedule dentist", {"text": "schedule dentist"}),
    ("Put finish report on my task list", {"text": "finish report"}),
    ("Add buy birthday gift to my tasks", {"text": "buy birthday gift"}),
    ("Add to todo list: clean the house", {"text": "clean the house"}),
    ("Add entry to tasks: meal prep", {"text": "meal prep"}),
    ("Add task do laundry", {"text": "do laundry"}),
    ("Put return library books on the list", {"text": "return library books"}),
    ("Add renew subscription to task list", {"text": "renew subscription"}),
    ("Add new task: fix leaky faucet", {"text": "fix leaky faucet"}),
    ("Add to list: order supplies", {"text": "order supplies"}),
    ("Create task submit expense report", {"text": "submit expense report"}),
    ("Add schedule car maintenance to my to-do list", {"text": "schedule car maintenance"}),
    ("Add task: prescription refill", {"text": "prescription refill"}),
    ("Put backup computer files on my task list", {"text": "backup computer files"}),
    ("Add cancel subscription to my tasks", {"text": "cancel subscription"}),
    ("Add to todo list: review contract", {"text": "review contract"}),
    ("Add task update resume", {"text": "update resume"}),
    ("Put organize closet on the list", {"text": "organize closet"}),
    ("Add reply to John to task list", {"text": "reply to John"}),
    ("Add new task: prepare presentation", {"text": "prepare presentation"}),
    ("Add to list: buy new shoes", {"text": "buy new shoes"}),
    ("Create task call insurance", {"text": "call insurance"}),
    ("Add fix broken chair to my to-do list", {"text": "fix broken chair"}),
    ("Add task: research vacation", {"text": "research vacation"}),
    ("Put sign permission slip on my task list", {"text": "sign permission slip"}),
    ("Add change air filters to my tasks", {"text": "change air filters"}),
    ("Add to todo list: change oil", {"text": "change oil"}),
    ("Add entry to tasks: buy dog food", {"text": "buy dog food"}),
    ("Add task clean garage", {"text": "clean garage"}),
    ("Put follow up with client on the list", {"text": "follow up with client"}),
    ("Add return Amazon package to task list", {"text": "return Amazon package"}),
    ("Add new task: charge batteries", {"text": "charge batteries"}),
    ("Add to list: paint bedroom", {"text": "paint bedroom"}),
    ("Create task schedule haircut", {"text": "schedule haircut"}),
    ("Add write thank you notes to my to-do list", {"text": "write thank you notes"}),
    ("Add task: buy new headphones", {"text": "buy new headphones"}),
    ("Put water lawn on my task list", {"text": "water lawn"}),
    ("Add vacuum the car to my tasks", {"text": "vacuum the car"}),
    ("Add to todo list: file taxes", {"text": "file taxes"}),
    ("Add entry to tasks: update software", {"text": "update software"}),
    ("Add task defrost freezer", {"text": "defrost freezer"}),
    ("Put RSVP to party on the list", {"text": "RSVP to party"}),
]

# ============ WEB_SEARCH (50 examples) ============
search_examples = [
    ("Search for Italian recipes", {"query": "Italian recipes"}),
    ("Look up weather in Tokyo", {"query": "weather in Tokyo"}),
    ("Search how to tie a tie", {"query": "how to tie a tie"}),
    ("Find best restaurants nearby", {"query": "best restaurants nearby"}),
    ("Look up stock price of Apple", {"query": "Apple stock price"}),
    ("Search for flight deals to Paris", {"query": "flight deals to Paris"}),
    ("Find news about tech", {"query": "latest tech news"}),
    ("Search Python tutorials", {"query": "Python tutorials"}),
    ("Look up movie showtimes", {"query": "movie showtimes near me"}),
    ("Find recipe for banana bread", {"query": "banana bread recipe"}),
    ("Search for yoga exercises", {"query": "yoga exercises for beginners"}),
    ("Look up Lakers score", {"query": "Lakers game score"}),
    ("Find hotels in Miami", {"query": "hotels in Miami"}),
    ("Search home workout routines", {"query": "home workout routines"}),
    ("Look up traffic conditions", {"query": "current traffic conditions"}),
    ("Search for gift ideas", {"query": "gift ideas for birthday"}),
    ("Find used cars for sale", {"query": "used cars for sale"}),
    ("Search best laptops 2024", {"query": "best laptops 2024"}),
    ("Look up flu symptoms", {"query": "flu symptoms"}),
    ("Find coffee shops near me", {"query": "coffee shops near me"}),
    ("Search how to make sourdough", {"query": "how to make sourdough bread"}),
    ("Look up currency exchange rates", {"query": "USD to EUR exchange rate"}),
    ("Search for hiking trails", {"query": "hiking trails near me"}),
    ("Find plumbers in my area", {"query": "plumbers near me"}),
    ("Search for DIY furniture projects", {"query": "DIY furniture projects"}),
    ("Look up concert tickets", {"query": "concert tickets near me"}),
    ("Find best pizza in town", {"query": "best pizza in town"}),
    ("Search for online courses", {"query": "online courses programming"}),
    ("Look up book recommendations", {"query": "best books 2024"}),
    ("Search for car insurance quotes", {"query": "car insurance quotes"}),
    ("Find gym memberships", {"query": "gym memberships near me"}),
    ("Search how to fix a flat tire", {"query": "how to fix a flat tire"}),
    ("Look up gardening tips", {"query": "gardening tips for beginners"}),
    ("Find dentists accepting patients", {"query": "dentists accepting new patients"}),
    ("Search for streaming services", {"query": "best streaming services"}),
    ("Look up train schedule", {"query": "train schedule"}),
    ("Search for moving companies", {"query": "moving companies near me"}),
    ("Find pet stores nearby", {"query": "pet stores near me"}),
    ("Search for wedding venues", {"query": "wedding venues near me"}),
    ("Look up tax deductions", {"query": "tax deductions 2024"}),
    ("Find tutors for math", {"query": "math tutors near me"}),
    ("Search for camping gear", {"query": "best camping gear"}),
    ("Look up pharmacy hours", {"query": "CVS pharmacy hours"}),
    ("Find electricians", {"query": "electricians near me"}),
    ("Search for baby names", {"query": "popular baby names 2024"}),
    ("Look up interview tips", {"query": "job interview tips"}),
    ("Search for language learning apps", {"query": "best language learning apps"}),
    ("Find dry cleaners nearby", {"query": "dry cleaners near me"}),
    ("Search for home improvement ideas", {"query": "home improvement ideas"}),
    ("Look up visa requirements", {"query": "visa requirements for Japan"}),
]

# ============ GET_SYSTEM_INFO (50 examples) ============
system_info_examples = [
    ("How much time is left on my timer?", {}),
    ("What's on my calendar today?", {}),
    ("Do I have any tasks?", {}),
    ("Are any lights on?", {}),
    ("What time is my alarm set for?", {}),
    ("What's the weather?", {}),
    ("Give me a summary of my day", {}),
    ("How many tasks do I have?", {}),
    ("Is the living room light on?", {}),
    ("What's left on my timer?", {}),
    ("Check my calendar for today", {}),
    ("What do I have scheduled?", {}),
    ("Any alarms set?", {}),
    ("What's the temperature?", {}),
    ("Show me my to-do list", {}),
    ("Which lights are on?", {}),
    ("How's the timer doing?", {}),
    ("What events are coming up?", {}),
    ("Tell me about today", {}),
    ("Any tasks pending?", {}),
    ("What's my schedule look like?", {}),
    ("Status of my timer", {}),
    ("Is it going to rain?", {}),
    ("What's the forecast?", {}),
    ("Do I have meetings today?", {}),
    ("How many minutes left on timer?", {}),
    ("What alarms do I have?", {}),
    ("Show my tasks", {}),
    ("Are there any lights off?", {}),
    ("What's happening today?", {}),
    ("Check the timer status", {}),
    ("Any calendar events?", {}),
    ("What's on my list?", {}),
    ("Status of bedroom light", {}),
    ("When is my next alarm?", {}),
    ("What's the weather forecast?", {}),
    ("How's my day looking?", {}),
    ("Pending tasks?", {}),
    ("Timer check", {}),
    ("What's the current temperature?", {}),
    ("My schedule for today", {}),
    ("Any reminders?", {}),
    ("Light status", {}),
    ("When does the timer go off?", {}),
    ("What's my agenda?", {}),
    ("Do I have anything tomorrow?", {}),
    ("Status of the house", {}),
    ("How's the weather outside?", {}),
    ("What tasks are pending?", {}),
    ("System status", {}),
]

# ============ THINKING (50 examples) ============
# Use thinking for: coding/debugging, math, multi-step reasoning, deep analysis,
# detailed technical explanations, long-form writing that requires planning.
thinking_examples = [
    "Explain how neural networks learn",
    "Write a Python function to sort a list",
    "Solve this equation: 3x + 7 = 22",
    "Debug this code that has a memory leak",
    "Explain the theory of relativity",
    "Write a SQL query to find duplicates",
    "Calculate the compound interest on $10000",
    "Explain how blockchain works",
    "Write a recursive function for Fibonacci",
    "Analyze the pros and cons of remote work",
    "Explain quantum computing basics",
    "Write a regex to validate emails",
    "Calculate the probability of rolling doubles",
    "Explain the difference between TCP and UDP",
    "Write an algorithm for binary search",
    "Analyze this stock's performance",
    "Explain machine learning algorithms",
    "Write a function to detect palindromes",
    "Calculate the area of an irregular shape",
    "Explain how encryption works",
    "Write a class for a linked list",
    "Analyze this business problem",
    "Explain the immune system in detail",
    "Write unit tests for this function",
    "Calculate the optimal route",
    "Explain cryptocurrency mining",
    "Write a parser for JSON",
    "Analyze this dataset for trends",
    "Write an API endpoint in Python",
    "Calculate mortgage payments for a $400k loan",
    "Explain how vaccines produce immunity",
    "Write a sorting algorithm from scratch",
    "Analyze this legal contract for risks",
    "Explain climate change science",
    "Write a web scraper in Python",
    "Calculate return on investment",
    "Explain supply chain logistics",
    "Write a state machine implementation",
    "Analyze this chemical reaction",
    "Write a compression algorithm",
    "Calculate statistical significance of this data",
    "Write a database schema for an e-commerce app",
    "Solve the traveling salesman problem",
    "Write a biography of Albert Einstein",
    "Explain how MRI machines work",
    "Write a marketing plan for a new product",
    "Calculate the energy of a photon at 500nm",
    "Write a bash script to automate backups",
    "Analyze the themes in To Kill a Mockingbird",
    "Explain how GPS determines location",
]

# ============ NONTHINKING (50 examples) ============
# Use nonthinking for: greetings, single-fact recall, brief acknowledgements,
# simple definitions, and questions with a direct one-line answer.
nonthinking_examples = [
    "Hello",
    "Hi there",
    "Good morning",
    "How are you?",
    "What's the capital of France?",
    "Who wrote Harry Potter?",
    "What year did WWII end?",
    "What color is the sky?",
    "How many states in the USA?",
    "Who is the CEO of Tesla?",
    "What's 2 + 2?",
    "Thanks",
    "Thank you so much",
    "Goodbye",
    "See you later",
    "What day is it?",
    "Who invented the telephone?",
    "What's the largest ocean?",
    "How many continents are there?",
    "What language is spoken in Brazil?",
    "Hey",
    "What's up?",
    "Good evening",
    "Nice to meet you",
    "What's your name?",
    "Who painted the Mona Lisa?",
    "What's the speed of light?",
    "When is Christmas?",
    "What's the tallest mountain?",
    "Who discovered penicillin?",
    "You're welcome",
    "No problem",
    "Good night",
    "Have a nice day",
    "What's the currency of Japan?",
    "How many days in a week?",
    "What's the chemical symbol for gold?",
    "Who wrote 1984?",
    "Greetings",
    "Tell me a joke",
    "What's the opposite of hot?",
    "What's the boiling point of water?",
    "How do you say hello in Spanish?",
    "What is 10 plus 5?",
    "What is the largest country by area?",
    "How many legs does a spider have?",
    "What's the fastest land animal?",
    "What is the moon made of?",
    "How many hours are in a day?",
    "Who wrote Romeo and Juliet?",
]

# ============ CONTROL_RGB_LIGHTING (50 examples) ============
# High-level dispatcher: routes to brightness, canvas, or effect actions.
control_rgb_examples = [
    # Effect application (20 examples)
    ("Apply Rainbow effect to RGB lighting", {"action": "apply_effect", "effect_name": "Rainbow"}),
    ("Set RGB to Breathing effect", {"action": "apply_effect", "effect_name": "Breathing"}),
    ("Use Wave effect for RGB lights", {"action": "apply_effect", "effect_name": "Wave"}),
    ("Apply Gradient effect", {"action": "apply_effect", "effect_name": "Gradient"}),
    ("Set RGB lighting to Color Shift", {"action": "apply_effect", "effect_name": "Color Shift"}),
    ("Use Marquee effect", {"action": "apply_effect", "effect_name": "Marquee"}),
    ("Apply Alternating effect", {"action": "apply_effect", "effect_name": "Alternating"}),
    ("Set RGB to Cross effect", {"action": "apply_effect", "effect_name": "Cross"}),
    ("Use Round Robin effect", {"action": "apply_effect", "effect_name": "Round Robin"}),
    ("Apply Random effect", {"action": "apply_effect", "effect_name": "Random"}),
    ("Set RGB lighting to Static effect", {"action": "apply_effect", "effect_name": "Static"}),
    ("Use Fading effect", {"action": "apply_effect", "effect_name": "Fading"}),
    ("Apply Chase effect", {"action": "apply_effect", "effect_name": "Chase"}),
    ("Set RGB to Flash effect", {"action": "apply_effect", "effect_name": "Flash"}),
    ("Use Pulse effect on my RGB", {"action": "apply_effect", "effect_name": "Pulse"}),
    ("Apply Smooth effect", {"action": "apply_effect", "effect_name": "Smooth"}),
    ("Set RGB to Aurora effect", {"action": "apply_effect", "effect_name": "Aurora"}),
    ("Use Comet effect for RGB lighting", {"action": "apply_effect", "effect_name": "Comet"}),
    ("Apply Fire effect to my setup", {"action": "apply_effect", "effect_name": "Fire"}),
    ("Set RGB lighting to Matrix effect", {"action": "apply_effect", "effect_name": "Matrix"}),
]

# ============ CHECK_SIGNALRGB_CONNECTION (25 examples) ============
check_rgb_connection_examples = [
    ("Is SignalRGB connected?", {}),
    ("Check if the RGB API is available", {}),
    ("Is the SignalRGB service running?", {}),
    ("Can you reach the RGB lighting API?", {}),
    ("Verify SignalRGB connection", {}),
    ("Is RGB lighting control available?", {}),
    ("Check SignalRGB status", {}),
    ("Is the lighting software connected?", {}),
    ("Test the RGB API connection", {}),
    ("Ping the SignalRGB service", {}),
    ("Make sure SignalRGB is online", {}),
    ("Is the RGB controller reachable?", {}),
    ("Check if RGB software is active", {}),
    ("Are the RGB controls accessible?", {}),
    ("Confirm SignalRGB is running", {}),
    ("Is the lighting API up?", {}),
    ("Validate the SignalRGB connection", {}),
    ("Check RGB service availability", {}),
    ("Is SignalRGB responding?", {}),
    ("Can the app talk to SignalRGB?", {}),
    ("Detect if SignalRGB is installed and running", {}),
    ("Probe the RGB API", {}),
    ("Is the SignalRGB backend reachable?", {}),
    ("Check if RGB automation is possible", {}),
    ("Is RGB lighting management available right now?", {}),
]

# ============ GET_CURRENT_RGB_EFFECT (25 examples) ============
get_current_rgb_examples = [
    ("What RGB effect is currently active?", {}),
    ("What's the current lighting effect?", {}),
    ("Which effect is running on my RGB?", {}),
    ("Show me the active RGB effect", {}),
    ("What effect do I have on right now?", {}),
    ("What's playing on my RGB lights?", {}),
    ("Get the current RGB mode", {}),
    ("Tell me the active lighting effect", {}),
    ("Which RGB animation is active?", {}),
    ("What's my current SignalRGB effect?", {}),
    ("Show the current effect name", {}),
    ("What effect is on my setup?", {}),
    ("Fetch the active RGB effect", {}),
    ("What lighting mode is running?", {}),
    ("Current RGB effect please", {}),
    ("Get current lighting animation", {}),
    ("Which effect is loaded right now?", {}),
    ("What is the RGB set to?", {}),
    ("Show active effect name", {}),
    ("What is the RGB currently doing?", {}),
    ("Read the current RGB effect", {}),
    ("Retrieve the running lighting effect", {}),
    ("Which preset is active on my RGB?", {}),
    ("What effect is SignalRGB using?", {}),
    ("Get the name of the current RGB effect", {}),
]

# ============ SET_RGB_BRIGHTNESS (25 examples) ============
# Low-level direct API call (complements the high-level control_rgb_lighting)
set_rgb_brightness_examples = [
    ("Directly set RGB brightness to 80", {"brightness": 80}),
    ("Call set brightness 50 on RGB API", {"brightness": 50}),
    ("Set the RGB brightness value to 30", {"brightness": 30}),
    ("RGB brightness API call: 100", {"brightness": 100}),
    ("Push brightness level 70 to SignalRGB", {"brightness": 70}),
    ("Set brightness parameter to 40 in SignalRGB", {"brightness": 40}),
    ("Update RGB brightness to 90 via API", {"brightness": 90}),
    ("Send brightness 20 to the RGB controller", {"brightness": 20}),
    ("Set global RGB brightness to 60", {"brightness": 60}),
    ("Change the RGB brightness value to 75", {"brightness": 75}),
    ("Apply brightness level 10 to all RGB", {"brightness": 10}),
    ("Set RGB API brightness parameter to 55", {"brightness": 55}),
    ("Update global brightness to 85 in SignalRGB", {"brightness": 85}),
    ("Set RGB light level to 45", {"brightness": 45}),
    ("Apply brightness 65 to RGB lighting", {"brightness": 65}),
    ("Send brightness value 35 to SignalRGB", {"brightness": 35}),
    ("Set RGB intensity to 95", {"brightness": 95}),
    ("Update the SignalRGB brightness to 25", {"brightness": 25}),
    ("Set global brightness parameter to 15", {"brightness": 15}),
    ("Push brightness 5 to RGB system", {"brightness": 5}),
    ("Set SignalRGB brightness level to 100", {"brightness": 100}),
    ("Update RGB brightness via API to 0", {"brightness": 0}),
    ("Set RGB brightness to 48", {"brightness": 48}),
    ("Apply brightness 72 to SignalRGB", {"brightness": 72}),
    ("Set the lighting brightness to 33 on RGB", {"brightness": 33}),
]

# ============ ENABLE_RGB_CANVAS (25 examples) ============
enable_rgb_canvas_examples = [
    ("Enable the RGB canvas now", {"enabled": True}),
    ("Turn on the SignalRGB canvas", {"enabled": True}),
    ("Switch the RGB canvas on", {"enabled": True}),
    ("Activate the RGB canvas", {"enabled": True}),
    ("Set RGB canvas enabled to true", {"enabled": True}),
    ("Start the lighting canvas", {"enabled": True}),
    ("Enable canvas in SignalRGB", {"enabled": True}),
    ("Power on the RGB canvas layer", {"enabled": True}),
    ("Resume the RGB canvas", {"enabled": True}),
    ("Restore the lighting canvas", {"enabled": True}),
    ("Disable the RGB canvas now", {"enabled": False}),
    ("Turn off the SignalRGB canvas", {"enabled": False}),
    ("Switch the RGB canvas off", {"enabled": False}),
    ("Deactivate the RGB canvas", {"enabled": False}),
    ("Set RGB canvas enabled to false", {"enabled": False}),
    ("Stop the lighting canvas", {"enabled": False}),
    ("Disable canvas in SignalRGB", {"enabled": False}),
    ("Power off the RGB canvas layer", {"enabled": False}),
    ("Pause the RGB canvas", {"enabled": False}),
    ("Suspend the lighting canvas", {"enabled": False}),
    ("RGB canvas on", {"enabled": True}),
    ("RGB canvas off", {"enabled": False}),
    ("Set canvas state to enabled", {"enabled": True}),
    ("Set canvas state to disabled", {"enabled": False}),
    ("Toggle canvas to active state", {"enabled": True}),
]

# ============ GET_INSTALLED_RGB_EFFECTS (25 examples) ============
get_installed_effects_examples = [
    ("What RGB effects are installed?", {}),
    ("List all available lighting effects", {}),
    ("Show me the installed RGB effects", {}),
    ("What effects can I use in SignalRGB?", {}),
    ("Get all installed RGB animations", {}),
    ("Which lighting effects are available?", {}),
    ("Fetch the list of RGB effects", {}),
    ("What effects does SignalRGB have?", {}),
    ("Show available effects for RGB", {}),
    ("List installed SignalRGB effects", {}),
    ("Get all RGB effect names", {}),
    ("What animations are available?", {}),
    ("Show all lighting modes available", {}),
    ("Retrieve installed effects list", {}),
    ("What effects can I apply to my RGB?", {}),
    ("List the lighting effects I have", {}),
    ("Get available SignalRGB effects", {}),
    ("Show RGB effect library", {}),
    ("What are my RGB options?", {}),
    ("Enumerate all RGB effects", {}),
    ("Fetch installed lighting effects from SignalRGB", {}),
    ("What effects are on my system?", {}),
    ("Display the list of RGB effects", {}),
    ("Get all available animation effects", {}),
    ("What lighting options does SignalRGB offer?", {}),
]

# ============ GET_RGB_EFFECT_INFO (25 examples) ============
get_rgb_effect_info_examples = [
    ("Get details on the Rainbow effect", {"effect_id": "Rainbow"}),
    ("Tell me about the Breathing effect", {"effect_id": "Breathing"}),
    ("What parameters does the Wave effect have?", {"effect_id": "Wave"}),
    ("Get info for the Gradient effect", {"effect_id": "Gradient"}),
    ("Show details for Color Shift effect", {"effect_id": "Color Shift"}),
    ("Describe the Marquee effect", {"effect_id": "Marquee"}),
    ("Get effect info for Alternating", {"effect_id": "Alternating"}),
    ("What does the Cross effect do?", {"effect_id": "Cross"}),
    ("Tell me about Round Robin effect", {"effect_id": "Round Robin"}),
    ("Get details on Random effect", {"effect_id": "Random"}),
    ("Show info for Static effect", {"effect_id": "Static"}),
    ("Describe the Fading effect", {"effect_id": "Fading"}),
    ("What options does Chase have?", {"effect_id": "Chase"}),
    ("Get info on Flash effect", {"effect_id": "Flash"}),
    ("Tell me about the Pulse effect", {"effect_id": "Pulse"}),
    ("Describe the Smooth effect", {"effect_id": "Smooth"}),
    ("Get info for Aurora effect", {"effect_id": "Aurora"}),
    ("Tell me about Comet effect options", {"effect_id": "Comet"}),
    ("What parameters does Fire have?", {"effect_id": "Fire"}),
    ("Get effect info for Matrix", {"effect_id": "Matrix"}),
    ("Show details for Storm effect", {"effect_id": "Storm"}),
    ("What does the Glitch effect do?", {"effect_id": "Glitch"}),
    ("Get info for the Starlight effect", {"effect_id": "Starlight"}),
    ("Describe the Vortex effect", {"effect_id": "Vortex"}),
    ("Tell me about the Spectrum effect", {"effect_id": "Spectrum"}),
]

# ============ APPLY_RGB_EFFECT (25 examples) ============
apply_rgb_effect_examples = [
    ("Apply the Rainbow effect", {"effect_id": "Rainbow"}),
    ("Load the Breathing effect", {"effect_id": "Breathing"}),
    ("Run the Wave effect", {"effect_id": "Wave"}),
    ("Apply Gradient to RGB lighting", {"effect_id": "Gradient"}),
    ("Load Color Shift effect", {"effect_id": "Color Shift"}),
    ("Apply Marquee effect now", {"effect_id": "Marquee"}),
    ("Run the Alternating effect", {"effect_id": "Alternating"}),
    ("Apply Cross effect via API", {"effect_id": "Cross"}),
    ("Load Round Robin effect", {"effect_id": "Round Robin"}),
    ("Apply Random to the RGB system", {"effect_id": "Random"}),
    ("Run Static effect on RGB", {"effect_id": "Static"}),
    ("Apply the Fading effect", {"effect_id": "Fading"}),
    ("Load Chase effect", {"effect_id": "Chase"}),
    ("Apply Flash effect to lighting", {"effect_id": "Flash"}),
    ("Run Pulse effect", {"effect_id": "Pulse"}),
    ("Apply Smooth effect via SignalRGB", {"effect_id": "Smooth"}),
    ("Load Aurora effect", {"effect_id": "Aurora"}),
    ("Apply Comet effect to my RGB", {"effect_id": "Comet"}),
    ("Run Fire effect on the RGB", {"effect_id": "Fire"}),
    ("Load Matrix effect", {"effect_id": "Matrix"}),
    ("Apply Storm effect", {"effect_id": "Storm"}),
    ("Run Glitch effect", {"effect_id": "Glitch"}),
    ("Apply Starlight effect to RGB", {"effect_id": "Starlight"}),
    ("Load Vortex effect now", {"effect_id": "Vortex"}),
    ("Apply the Spectrum effect", {"effect_id": "Spectrum"}),
]

# ============ GET_RGB_EFFECT_PRESETS (25 examples) ============
get_rgb_effect_presets_examples = [
    ("Get presets for Rainbow effect", {"effect_id": "Rainbow"}),
    ("Show presets for Breathing", {"effect_id": "Breathing"}),
    ("List Wave effect presets", {"effect_id": "Wave"}),
    ("What presets does Gradient have?", {"effect_id": "Gradient"}),
    ("Fetch presets for Color Shift", {"effect_id": "Color Shift"}),
    ("Get available presets for Marquee", {"effect_id": "Marquee"}),
    ("Show Alternating effect presets", {"effect_id": "Alternating"}),
    ("List presets for Cross effect", {"effect_id": "Cross"}),
    ("Get Round Robin presets", {"effect_id": "Round Robin"}),
    ("What presets are available for Random?", {"effect_id": "Random"}),
    ("Fetch Static effect presets", {"effect_id": "Static"}),
    ("Show Fading presets", {"effect_id": "Fading"}),
    ("Get presets for Chase effect", {"effect_id": "Chase"}),
    ("List available Flash presets", {"effect_id": "Flash"}),
    ("What presets does Pulse have?", {"effect_id": "Pulse"}),
    ("Get presets for Smooth", {"effect_id": "Smooth"}),
    ("Show Aurora effect presets", {"effect_id": "Aurora"}),
    ("Fetch Comet presets", {"effect_id": "Comet"}),
    ("Get presets for Fire effect", {"effect_id": "Fire"}),
    ("List Matrix effect presets", {"effect_id": "Matrix"}),
    ("Show Storm presets", {"effect_id": "Storm"}),
    ("Get available Glitch presets", {"effect_id": "Glitch"}),
    ("List presets for Starlight effect", {"effect_id": "Starlight"}),
    ("Get Vortex effect presets", {"effect_id": "Vortex"}),
    ("Show presets for Spectrum effect", {"effect_id": "Spectrum"}),
]

# ---------------------------------------------------------------------------
# Assemble all examples
# ---------------------------------------------------------------------------
all_examples = []

for prompt, args in control_light_examples:
    all_examples.append(make_example(prompt, "control_light", args))

for prompt, args in set_timer_examples:
    all_examples.append(make_example(prompt, "set_timer", args))

for prompt, args in set_alarm_examples:
    all_examples.append(make_example(prompt, "set_alarm", args))

for prompt, args in calendar_examples:
    all_examples.append(make_example(prompt, "create_calendar_event", args))

for prompt, args in task_examples:
    all_examples.append(make_example(prompt, "add_task", args))

for prompt, args in search_examples:
    all_examples.append(make_example(prompt, "web_search", args))

for prompt, args in system_info_examples:
    all_examples.append(make_example(prompt, "get_system_info", args))

for prompt in thinking_examples:
    all_examples.append(make_example(prompt, "thinking", {"prompt": prompt}))

for prompt in nonthinking_examples:
    all_examples.append(make_example(prompt, "nonthinking", {"prompt": prompt}))

# RGB examples
for prompt, args in control_rgb_examples:
    all_examples.append(make_example(prompt, "control_rgb_lighting", args))

for prompt, args in check_rgb_connection_examples:
    all_examples.append(make_example(prompt, "check_signalrgb_connection", args))

for prompt, args in get_current_rgb_examples:
    all_examples.append(make_example(prompt, "get_current_rgb_effect", args))

for prompt, args in set_rgb_brightness_examples:
    all_examples.append(make_example(prompt, "set_rgb_brightness", args))

for prompt, args in enable_rgb_canvas_examples:
    all_examples.append(make_example(prompt, "enable_rgb_canvas", args))

for prompt, args in get_installed_effects_examples:
    all_examples.append(make_example(prompt, "get_installed_rgb_effects", args))

for prompt, args in get_rgb_effect_info_examples:
    all_examples.append(make_example(prompt, "get_rgb_effect_info", args))

for prompt, args in apply_rgb_effect_examples:
    all_examples.append(make_example(prompt, "apply_rgb_effect", args))

for prompt, args in get_rgb_effect_presets_examples:
    all_examples.append(make_example(prompt, "get_rgb_effect_presets", args))

# ---------------------------------------------------------------------------
# Shuffle and write
# ---------------------------------------------------------------------------
random.seed(42)
random.shuffle(all_examples)

output_path = "training_dataset_functions.jsonl"
with open(output_path, "w") as f:
    for ex in all_examples:
        f.write(json.dumps(ex) + "\n")

print(f"Generated {len(all_examples)} training examples")
print(f"Saved to {output_path}")

# Per-function breakdown
from collections import Counter
fn_counts = Counter(
    ex["messages"][2]["tool_calls"][0]["function"]["name"]
    for ex in all_examples
)
print("\nExamples per function:")
for fn, count in sorted(fn_counts.items()):
    print(f"  {fn:<35} {count}")