"""Centralized helpers for (de)serializing JSON-ish data into Text columns.

SQLite doesn't need a dedicated JSON column type for this project, so list/dict
fields are stored as JSON-encoded strings in Text columns. All (de)serialization
goes through these helpers so it's consistent and not duplicated across models,
schemas and routers.
"""
import json
from typing import Any


def dumps(value: Any) -> str:
    """Serialize a Python value (list/dict/None) to a JSON string for storage."""
    if value is None:
        return json.dumps([])
    return json.dumps(value)


def loads(value: str | None, default: Any = None) -> Any:
    """Deserialize a stored JSON string back into a Python value."""
    if value is None or value == "":
        return default if default is not None else []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []
