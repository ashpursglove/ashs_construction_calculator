"""
modules/project_io.py

Project save/load helpers for GDT Construction Planner.

- Saves ALL user inputs across tabs into a single JSON file
- Loads and restores those values back into the UI

This is intentionally plain JSON:
- easy to diff in git
- easy to email around
- no weird binary formats
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

PROJECT_FILE_EXT = ".ashproj.json"
PROJECT_SCHEMA_VERSION = 1


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_project(path: str, data: Dict[str, Any]) -> None:
    """
    Save project data to JSON.

    Args:
        path: Output file path.
        data: Arbitrary project dictionary (must be JSON-serializable).
    """
    payload = {
        "schema_version": PROJECT_SCHEMA_VERSION,
        "saved_utc": _utc_now_iso(),
        "data": data,
    }

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_project(path: str) -> Dict[str, Any]:
    """
    Load project data from JSON.

    Returns:
        The 'data' dict from the project file.
    """
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Invalid project file: root is not an object.")

    version = payload.get("schema_version", None)
    if version != PROJECT_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported project file version: {version} (expected {PROJECT_SCHEMA_VERSION})"
        )

    data = payload.get("data", None)
    if not isinstance(data, dict):
        raise ValueError("Invalid project file: missing/invalid 'data' object.")

    return data
