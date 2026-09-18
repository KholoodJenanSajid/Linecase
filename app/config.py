from __future__ import annotations

import os

PLACEHOLDER_KEYS = {"", "your_gemini_api_key", "YOUR_KEY", "changeme"}


def api_key() -> str | None:
    """Return the Gemini key, treating .env.example placeholders as unset."""
    key = (os.environ.get("GOOGLE_API_KEY") or "").strip()
    return None if key in PLACEHOLDER_KEYS else key


def offline() -> bool:
    """Serve canned fixtures when forced, or whenever no usable key exists."""
    forced = (os.environ.get("LINECASE_OFFLINE") or "").strip().lower()
    if forced in {"1", "true", "yes"}:
        return True
    return api_key() is None
