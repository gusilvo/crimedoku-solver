"""Reads a puzzle JSON file and returns the raw data dict."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict


def load_json(path: str | Path) -> Dict[str, Any]:
    """Read *path* and return the parsed JSON as a dict."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
