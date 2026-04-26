"""Redact API material for support logs (no secrets, no network)."""

from __future__ import annotations

import json
import platform
import sys
from typing import Any


def _mask_secret(s: str, *, show_last: int = 4) -> str:
    t = (s or "").strip()
    if not t:
        return "(empty)"
    if len(t) <= show_last + 1:
        return "****"
    return "(…)" + t[-show_last:]


def redact_credential_map(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with secrets masked; usernames/URLs and model name kept as-is."""
    secret_keys = (
        "consumer_key",
        "consumer_secret",
        "access_token",
        "access_token_secret",
        "bearer_token",
        "ai_token",
    )
    out: dict[str, Any] = {}
    for k, v in data.items():
        if k in secret_keys:
            out[k] = _mask_secret(str(v))
        else:
            out[k] = v
    return out


def support_bundle_text() -> str:
    """OS + Python + tweepy versions for 'About' / support (no hostname)."""
    line = f"Python: {sys.version.split()[0]}  platform: {sys.platform!r}  {platform.machine()!r} {platform.system()!r}\n"
    try:
        import tweepy

        line += f"tweepy: {getattr(tweepy, '__version__', '?')!r}\n"
    except ImportError as e:
        line += f"tweepy: not importable ({e})\n"
    try:
        import keyring

        k = keyring.get_keyring()
        line += f"keyring: backend={k.__class__.__name__!r}\n"
    except ImportError:
        line += "keyring: not installed\n"
    except Exception as e:
        line += f"keyring: {e!r}\n"
    return line


def redact_credentials_json_pretty(data: dict[str, Any]) -> str:
    return json.dumps(redact_credential_map(data), indent=2, ensure_ascii=False) + "\n"
