"""OS keychain (keyring) + optional plain JSON for API credentials (Tab 2)."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Literal, cast

KEYRING_SERVICE = "PleaseDaddyElonNotTheBelt"
KEYRING_USER = "x_credentials_v1"
_log = logging.getLogger("PleaseDaddyElonNotTheBelt.creds")

Source = Literal["keyring", "file"]


def is_keyring_available() -> bool:
    try:
        import keyring

        k = keyring.get_keyring()
        return k is not None
    except ImportError:
        return False
    except Exception:
        return False


def _keyring_get_json() -> dict[str, Any] | None:
    try:
        import keyring
    except ImportError:
        return None
    try:
        raw = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
        if not raw:
            return None
        out = json.loads(raw)
        if not isinstance(out, dict):
            return None
        return out
    except Exception as e:
        _log.debug("keyring read: %s", e)
    return None


def load_credential_map(
    credentials_path: str,
) -> tuple[dict[str, Any] | None, Source | None]:
    d = _keyring_get_json()
    if d:
        return d, "keyring"
    if os.path.exists(credentials_path):
        try:
            with open(credentials_path, encoding="utf-8") as f:
                return cast(dict, json.load(f)), "file"
        except (json.JSONDecodeError, OSError) as e:
            _log.debug("credentials file read: %s", e)
    return None, None


def save_credential_map(
    credentials_path: str, data: dict[str, Any], *, use_keyring: bool
) -> Source:
    if use_keyring and is_keyring_available():
        keyring_mod: Any
        try:
            import keyring

            keyring_mod = keyring
        except ImportError:
            keyring_mod = None
        if keyring_mod is not None:
            try:
                keyring_mod.set_password(
                    KEYRING_SERVICE,
                    KEYRING_USER,
                    json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                )
                try:
                    if os.path.exists(credentials_path):
                        os.remove(credentials_path)
                except OSError as e:
                    _log.warning("could not remove plain credentials file: %s", e)
                return "keyring"
            except Exception as e:
                _log.warning("keyring write failed, using file: %s", e)
    with open(credentials_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return "file"


def update_stored_x_username(credentials_path: str, username: str, *, use_keyring: bool) -> None:
    cur, _ = load_credential_map(credentials_path)
    if not cur:
        return
    cur = dict(cur)
    cur["x_username"] = username
    save_credential_map(credentials_path, cur, use_keyring=use_keyring)
