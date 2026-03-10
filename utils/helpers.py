"""
Utility helpers shared across the application.
"""

import json
import re


def parse_entity_path_from_conn_str(connection_string: str) -> str:
    """
    Extract the EntityPath value from a Fabric / Azure Event Hubs
    connection string, e.g.:
      Endpoint=sb://...;SharedAccessKeyName=...;SharedAccessKey=...;EntityPath=myeventhub
    Returns an empty string if not found.
    """
    match = re.search(r"EntityPath=([^;]+)", connection_string, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def format_bytes(num_bytes: int) -> str:
    """Human-readable byte size string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def truncate_json(data: dict, max_chars: int = 500) -> str:
    """Return a JSON string truncated for display."""
    raw = json.dumps(data, default=str)
    if len(raw) > max_chars:
        return raw[:max_chars] + "…"
    return raw
