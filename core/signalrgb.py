"""
SignalRGB API Client - Controls PC RGB lighting via SignalRGB API.
"""

import requests
import json
from typing import List, Dict, Optional, Any
from config import GRAY, RESET, CYAN, GREEN, YELLOW


class SignalRGBClient:
    """Client for SignalRGB API to control PC RGB lighting."""

    def __init__(self, base_url: str = "http://localhost:16038"):
        """Initialize SignalRGB client.

        Args:
            base_url: Base URL for SignalRGB API (default: http://localhost:16038)
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.available = False

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

    def get_current_effect(self) -> Optional[Dict[str, Any]]:
        """Get the current lighting effect.

        Returns:
            Dictionary with effect information, or None if unavailable
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

    def set_global_brightness(self, brightness: int) -> bool:
        """Set the global brightness level.

        Args:
            brightness: Brightness level (0-100)

        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            return False

        # Clamp brightness to valid range
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

    def get_installed_effects(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of all installed effects.

        Returns:
            List of effect dictionaries, or None if unavailable
        """
        if not self.available:
            return None

        try:
            response = self.session.get(f"{self.base_url}/api/v1/lighting/effects", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("items", [])
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to get installed effects (status {response.status_code}){RESET}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error getting installed effects: {e}{RESET}")
            return None

    def get_effect_info(self, effect_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific effect.

        Args:
            effect_id: The ID of the effect

        Returns:
            Dictionary with effect information, or None if unavailable
        """
        if not self.available:
            return None

        try:
            response = self.session.get(f"{self.base_url}/api/v1/lighting/effects/{effect_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {})
            elif response.status_code == 404:
                print(f"{YELLOW}[SignalRGB] ⚠ Effect {effect_id} not found{RESET}")
                return None
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to get effect info (status {response.status_code}){RESET}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error getting effect info: {e}{RESET}")
            return None

    def apply_effect(self, effect_id: str) -> bool:
        """Apply a specific effect.

        Args:
            effect_id: The ID of the effect to apply

        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            return False

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/lighting/effects/{effect_id}/apply",
                timeout=10
            )

            if response.status_code == 200:
                print(f"{GREEN}[SignalRGB] ✓ Applied effect {effect_id}{RESET}")
                return True
            elif response.status_code == 404:
                print(f"{YELLOW}[SignalRGB] ⚠ Effect {effect_id} not found{RESET}")
                return False
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to apply effect (status {response.status_code}){RESET}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error applying effect: {e}{RESET}")
            return False

    def get_effect_presets(self, effect_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get available presets for a specific effect.

        Args:
            effect_id: The ID of the effect

        Returns:
            List of preset dictionaries, or None if unavailable
        """
        if not self.available:
            return None

        try:
            response = self.session.get(f"{self.base_url}/api/v1/lighting/effects/{effect_id}/presets", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("items", [])
            elif response.status_code == 404:
                print(f"{YELLOW}[SignalRGB] ⚠ Effect {effect_id} not found{RESET}")
                return None
            else:
                print(f"{YELLOW}[SignalRGB] ⚠ Failed to get effect presets (status {response.status_code}){RESET}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"{YELLOW}[SignalRGB] ⚠ Error getting effect presets: {e}{RESET}")
            return None


# Global SignalRGB client instance
signalrgb_client = SignalRGBClient()
