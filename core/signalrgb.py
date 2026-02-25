"""
SignalRGB API Client - Controls PC RGB lighting via SignalRGB API.

Official API docs: https://docs.signalrgb.com/signalrgb-api/lighting
Base URL: http://localhost:16038/api/v1/
"""

import requests
from urllib.parse import quote   # FIX: URL-encode effect IDs (they contain spaces, dots)
from typing import List, Dict, Optional, Any
from config import GRAY, RESET, CYAN, GREEN, YELLOW


class SignalRGBClient:
    """Client for SignalRGB API to control PC RGB lighting."""

    def __init__(self, base_url: str = "http://localhost:16038"):
        self.base_url = base_url
        self.session = requests.Session()
        self.available = False

        # Cache of name (lowercase) → effect dict from the last get_installed_effects call.
        # Used by resolve_effect_id() so we don't hammer the effects list endpoint.
        self._effects_cache: Dict[str, Dict] = {}

    # ── Connection ────────────────────────────────────────────────────────────

    def check_connection(self) -> bool:
        """Check if SignalRGB API is available.

        Returns:
            True if API is reachable, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/api/v1/lighting", timeout=5)
            if response.status_code == 200:
                self.available = True
                print(f"{GREEN}[SignalRGB] ✓ Connection established{RESET}")
                return True
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ SignalRGB API returned status {response.status_code}{RESET}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Could not connect to SignalRGB API: {e}{RESET}")
            self.available = False
            return False

    # ── Current state ─────────────────────────────────────────────────────────

    def get_current_effect(self) -> Optional[Dict[str, Any]]:
        """Get the current lighting effect.

        Official response shape:
          data.attributes = {name, enabled, global_brightness}
          data.id         = effect filename e.g. "Neon Shift.html"

        Returns:
            dict with effect attributes, or None if unavailable
        """
        if not self.available:
            return None
        try:
            response = self.session.get(f"{self.base_url}/api/v1/lighting", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("attributes", {})
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to get current effect (status {response.status_code}){RESET}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error getting current effect: {e}{RESET}")
            return None

    # ── Canvas controls ───────────────────────────────────────────────────────

    def set_global_brightness(self, brightness: int) -> bool:
        """Set the global brightness level.

        Official endpoint: PATCH /api/v1/lighting/global_brightness
        Payload: {"global_brightness": <int 0-100>}

        Args:
            brightness: Brightness level 0-100

        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            return False

        brightness = max(0, min(100, brightness))

        try:
            payload = {"global_brightness": brightness}
            response = self.session.patch(
                f"{self.base_url}/api/v1/lighting/global_brightness",
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                print(f"{GREEN}[SignalRGB] ✓ Brightness set to {brightness}%{RESET}")
                return True
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to set brightness (status {response.status_code}){RESET}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error setting brightness: {e}{RESET}")
            return False

    def enable_canvas(self, enabled: bool) -> bool:
        """Enable or disable the lighting canvas.

        Official endpoint: PATCH /api/v1/lighting/enabled
        Payload: {"enabled": <bool>}
        When disabled, all devices receive black (#000000).

        Args:
            enabled: True to enable, False to disable

        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            return False

        try:
            payload = {"enabled": enabled}
            response = self.session.patch(
                f"{self.base_url}/api/v1/lighting/enabled",
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                status = "enabled" if enabled else "disabled"
                print(f"{GREEN}[SignalRGB] ✓ Canvas {status}{RESET}")
                return True
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to {'enable' if enabled else 'disable'} canvas (status {response.status_code}){RESET}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error {'enabling' if enabled else 'disabling'} canvas: {e}{RESET}")
            return False

    # ── Effects list ──────────────────────────────────────────────────────────

    def get_installed_effects(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of all installed effects.

        Official endpoint: GET /api/v1/lighting/effects
        Returns data.items — each item has:
          id         : hash string e.g. "-MQtFeX-o2hMR6sv8aFr"  ← use this as effect_id
          attributes : {name: str}
          links      : {apply: str, self: str}

        NOTE: The API docs warn this can be a large payload — cache where possible.

        Returns:
            List of effect dicts, or None if unavailable
        """
        if not self.available:
            return None

        try:
            response = self.session.get(f"{self.base_url}/api/v1/lighting/effects", timeout=10)
            if response.status_code == 200:
                data = response.json()
                effects = data.get("data", {}).get("items", [])
                # Populate name cache for resolve_effect_id()
                self._effects_cache = {
                    e.get("attributes", {}).get("name", "").lower(): e
                    for e in effects
                    if e.get("attributes", {}).get("name")
                }
                return effects
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to get installed effects (status {response.status_code}){RESET}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error getting installed effects: {e}{RESET}")
            return None

    def resolve_effect_id(self, name_or_id: str) -> Optional[str]:
        """
        Resolve a human-readable effect name to its API hash ID.

        CRITICAL: The SignalRGB API uses hash IDs like "-MQtFeX-o2hMR6sv8aFr",
        NOT human-readable names. Passing a name directly to apply/info/preset
        endpoints will result in a 404.

        This method:
          1. Checks if name_or_id already looks like a hash (starts with - or is long)
          2. Otherwise searches installed effects by name (case-insensitive)
          3. Refreshes the effects list if the name isn't found in cache

        Args:
            name_or_id: Either a hash ID or a human-readable effect name

        Returns:
            The hash ID string, or None if not found
        """
        # Already looks like a hash ID (starts with - and is not a plain name)
        if name_or_id.startswith("-") and len(name_or_id) > 10:
            return name_or_id

        # Check cache first
        key = name_or_id.lower()
        if key in self._effects_cache:
            return self._effects_cache[key].get("id")

        # Cache miss — refresh from API
        effects = self.get_installed_effects()
        if not effects:
            return None

        if key in self._effects_cache:
            return self._effects_cache[key].get("id")

        print(f"{YELLOW}[SignalRGB] ⚠ Effect '{name_or_id}' not found in installed effects{RESET}")
        return None

    # ── Effect details ────────────────────────────────────────────────────────

    def get_effect_info(self, effect_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific effect.

        Official endpoint: GET /api/v1/lighting/effects/:id
        The :id must be the HASH ID (e.g. "-Mg1qujV9F4rabJxlSOS"),
        not the human-readable name.

        Args:
            effect_id: Hash ID or human-readable name (will be resolved automatically)

        Returns:
            Effect data dict, or None if unavailable/not found
        """
        if not self.available:
            return None

        resolved = self.resolve_effect_id(effect_id)
        if not resolved:
            print(f"{YELLOW}[SignalRGB] ⚠ Could not resolve effect ID for '{effect_id}'{RESET}")
            return None

        try:
            # URL-encode the ID — some IDs contain spaces or special characters
            encoded_id = quote(resolved, safe="")
            response = self.session.get(
                f"{self.base_url}/api/v1/lighting/effects/{encoded_id}",
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("data", {})
            elif response.status_code == 404:
                print(f"{YELLOW}[SignalRGB] ⚠ Effect '{effect_id}' not found{RESET}")
                return None
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to get effect info (status {response.status_code}){RESET}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error getting effect info: {e}{RESET}")
            return None

    def apply_effect(self, effect_id: str) -> bool:
        """Apply a specific effect.

        Official endpoint: POST /api/v1/lighting/effects/:id/apply
        The :id must be the HASH ID, not the human-readable name.

        Args:
            effect_id: Hash ID or human-readable name (will be resolved automatically)

        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            return False

        resolved = self.resolve_effect_id(effect_id)
        if not resolved:
            print(f"{YELLOW}[SignalRGB] ⚠ Could not resolve effect ID for '{effect_id}'{RESET}")
            return False

        try:
            encoded_id = quote(resolved, safe="")
            response = self.session.post(
                f"{self.base_url}/api/v1/lighting/effects/{encoded_id}/apply",
                timeout=10
            )
            if response.status_code == 200:
                print(f"{GREEN}[SignalRGB] ✓ Applied effect '{effect_id}'{RESET}")
                return True
            elif response.status_code == 404:
                print(f"{YELLOW}[SignalRGB] ⚠ Effect '{effect_id}' not found{RESET}")
                return False
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to apply effect (status {response.status_code}){RESET}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error applying effect: {e}{RESET}")
            return False

    # ── Effect presets ────────────────────────────────────────────────────────

    def get_effect_presets(self, effect_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get available presets for a specific effect.

        Official endpoint: GET /api/v1/lighting/effects/:id/presets
        Returns list of preset dicts: [{id: "My Fancy Preset 1", type: "preset"}, ...]

        Args:
            effect_id: Hash ID or human-readable name (will be resolved automatically)

        Returns:
            List of preset dicts, or None if unavailable/not found
        """
        if not self.available:
            return None

        resolved = self.resolve_effect_id(effect_id)
        if not resolved:
            print(f"{YELLOW}[SignalRGB] ⚠ Could not resolve effect ID for '{effect_id}'{RESET}")
            return None

        try:
            encoded_id = quote(resolved, safe="")
            response = self.session.get(
                f"{self.base_url}/api/v1/lighting/effects/{encoded_id}/presets",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("items", [])
            elif response.status_code == 404:
                print(f"{YELLOW}[SignalRGB] ⚠ Effect '{effect_id}' not found{RESET}")
                return None
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to get effect presets (status {response.status_code}){RESET}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error getting effect presets: {e}{RESET}")
            return None

    def apply_effect_preset(self, effect_id: str, preset_name: str) -> bool:
        """Apply a specific preset for an effect.

        Official endpoint: PATCH /api/v1/lighting/effects/:id/presets
        Payload: {"preset": "<preset_name>"}

        NOTE: This method was MISSING from the original implementation.
        The preset_name must match exactly (e.g. "My Fancy Preset 1").

        Args:
            effect_id: Hash ID or human-readable name (will be resolved automatically)
            preset_name: Exact preset name string

        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            return False

        resolved = self.resolve_effect_id(effect_id)
        if not resolved:
            print(f"{YELLOW}[SignalRGB] ⚠ Could not resolve effect ID for '{effect_id}'{RESET}")
            return False

        try:
            encoded_id = quote(resolved, safe="")
            payload = {"preset": preset_name}
            response = self.session.patch(
                f"{self.base_url}/api/v1/lighting/effects/{encoded_id}/presets",
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                print(f"{GREEN}[SignalRGB] ✓ Applied preset '{preset_name}' for effect '{effect_id}'{RESET}")
                return True
            elif response.status_code == 404:
                print(f"{YELLOW}[SignalRGB] ⚠ Effect '{effect_id}' or preset '{preset_name}' not found{RESET}")
                return False
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to apply preset (status {response.status_code}){RESET}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error applying preset: {e}{RESET}")
            return False


# Global SignalRGB client instance
signalrgb_client = SignalRGBClient()