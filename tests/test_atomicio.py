"""pde.atomicio: rotating backup + atomic write."""

import json
from pathlib import Path

from pde.atomicio import atomic_write_json, read_json_file


def test_read_json_file_missing():
    assert read_json_file("/nonexistent/nope/nope.json") is None


def test_atomic_write_json_and_backups(tmp_path: Path) -> None:
    p = tmp_path / "data.json"
    atomic_write_json(str(p), {"a": 1}, keep_backups=0, indent=2)
    assert p.read_text(encoding="utf-8").strip() == json.dumps({"a": 1}, indent=2).strip()
    atomic_write_json(str(p), {"a": 2}, keep_backups=2, indent=2)
    assert (tmp_path / "data.json.bak").is_file()
    assert read_json_file(str(p)) == {"a": 2}
    assert read_json_file(str(tmp_path / "data.json.bak")) == {"a": 1}
