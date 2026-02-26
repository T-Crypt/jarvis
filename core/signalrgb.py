"""
SignalRGB Controller - Applies RGB lighting effects via the SignalRGB URL scheme.

Uses: start signalrgb://effect/apply/<EffectName>
Requires SignalRGB to be running. No API key or Pro subscription needed.

Available effects:
    Sakura, Hydrogen, Black Ice, Spiral Rainbow, Coral, Neon Fire,
    Emerald Dream, Rainbow Rise, Spin, Enigma, Corrosive, Pixel Fill,
    Cyber Rain, Fire And Ice
"""

import subprocess
from typing import Optional
from config import GREEN, YELLOW, RESET

# Canonical effect names → exact URL slug used by SignalRGB
# Spaces become % in the URL scheme (not %20)
EFFECT_MAP = {
    "sakura":          "Sakura",
    "hydrogen":        "Hydrogen",
    "black ice":       "Black%Ice",
    "spiral rainbow":  "Spiral%Rainbow",
    "coral":           "Coral",
    "neon fire":       "Neon%Fire",
    "emerald dream":   "Emerald%Dream",
    "rainbow rise":    "Rainbow%Rise",
    "spin":            "Spin",
    "enigma":          "Enigma",
    "corrosive":       "Corrosive",
    "pixel fill":      "Pixel%Fill",
    "cyber rain":      "Cyber%Rain",
    "fire and ice":    "Fire%And%Ice",
}


class SignalRGBController:
    """Controls RGB lighting by launching SignalRGB URL scheme commands via PowerShell."""

    def apply_effect(self, effect_name: str) -> bool:
        """
        Apply a lighting effect by name.

        Converts the human-readable name to the SignalRGB URL slug and launches
        it via PowerShell: start signalrgb://effect/apply/<slug>

        Args:
            effect_name: Human-readable effect name, e.g. "Cyber Rain" or "Spin"

        Returns:
            True if the command launched successfully, False otherwise
        """
        slug = self._resolve_slug(effect_name)
        if not slug:
            print(f"{YELLOW}[SignalRGB] ⚠ Unknown effect: '{effect_name}'. "
                  f"Available: {', '.join(self.list_effects())}{RESET}")
            return False

        url = f"signalrgb://effect/apply/{slug}"
        try:
            subprocess.run(
                ["powershell", "-Command", f"start '{url}'"],
                check=True,
                timeout=10,
                capture_output=True
            )
            print(f"{GREEN}[SignalRGB] ✓ Applied effect: {effect_name}{RESET}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"{YELLOW}[SignalRGB] ⚠ PowerShell error applying '{effect_name}': {e}{RESET}")
            return False
        except subprocess.TimeoutExpired:
            print(f"{YELLOW}[SignalRGB] ⚠ Timed out applying '{effect_name}'{RESET}")
            return False
        except FileNotFoundError:
            print(f"{YELLOW}[SignalRGB] ⚠ PowerShell not found. Are you on Windows?{RESET}")
            return False

    def _resolve_slug(self, effect_name: str) -> Optional[str]:
        """
        Resolve a human-readable effect name to its URL slug.

        Tries exact lowercase match first, then partial match so
        "cyber rain", "Cyber Rain", and "CyberRain" all work.

        Args:
            effect_name: Effect name from the router

        Returns:
            URL slug string, or None if not found
        """
        key = effect_name.lower().strip()

        # Exact match
        if key in EFFECT_MAP:
            return EFFECT_MAP[key]

        # Partial match — handles minor transcription variations
        for canonical_key, slug in EFFECT_MAP.items():
            if key in canonical_key or canonical_key in key:
                return slug

        # Last resort: encode it directly (for effects added later)
        # Replace spaces with % to match SignalRGB's URL scheme
        encoded = effect_name.strip().replace(" ", "%")
        if encoded:
            return encoded

        return None

    def list_effects(self):
        """Return list of known effect names."""
        return [k.title() for k in EFFECT_MAP.keys()]


# Global instance
signalrgb_client = SignalRGBController()