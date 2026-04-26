"""Rotating backups and atomic JSON writes to avoid truncated files on crash."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from typing import Any


def _remove_if_exists(p: str) -> None:
    try:
        if os.path.exists(p):
            os.remove(p)
    except OSError:
        pass


def _move_file(src: str, dst: str) -> None:
    if not os.path.isfile(src):
        return
    _remove_if_exists(dst)
    os.replace(src, dst)


def rotate_backups(path: str, keep: int = 3) -> None:
    """
    Move ``path`` into ``path.bak``, older backups to ``.bak.1``, ``.bak.2``, dropping
    the oldest. ``keep=1`` only copies to ``.bak`` (one generation). For ``keep>3`` the
    chain depth is still three files (``main``, ``.bak``, ``.bak.1``, ``.bak.2``).
    """
    if not os.path.isfile(path) or keep < 1:
        return
    if keep == 1:
        try:
            shutil.copy2(path, path + ".bak")
        except OSError:
            pass
        return
    if keep == 2:
        if os.path.isfile(f"{path}.bak"):
            _remove_if_exists(f"{path}.bak.1")
            _move_file(f"{path}.bak", f"{path}.bak.1")
        _move_file(path, f"{path}.bak")
        return
    _remove_if_exists(f"{path}.bak.2")
    if os.path.isfile(f"{path}.bak.1"):
        _move_file(f"{path}.bak.1", f"{path}.bak.2")
    if os.path.isfile(f"{path}.bak"):
        _move_file(f"{path}.bak", f"{path}.bak.1")
    if os.path.isfile(path):
        _move_file(path, f"{path}.bak")


def atomic_write_json(
    path: str,
    obj: Any,
    *,
    keep_backups: int = 3,
    indent: int = 2,
) -> None:
    d = os.path.dirname(os.path.abspath(path)) or "."
    if keep_backups and os.path.isfile(path):
        rotate_backups(path, keep=min(keep_backups, 3))
    fd, tmp = tempfile.mkstemp(prefix="._tmp_", suffix=".json", dir=d, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, indent=indent, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        raise


def read_json_file(path: str) -> Any | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, TypeError):
        return None
