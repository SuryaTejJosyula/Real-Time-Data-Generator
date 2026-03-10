"""
Microsoft Fabric REST API helpers.

Provides workspace/eventstream discovery and Custom Endpoint connection-string
extraction.  All functions are synchronous and thread-safe (stateless).

Key public surface:
    list_workspaces(token)           → [{id, displayName, capacityId?, ...}]
    list_eventstreams(token, ws_id)  → [{id, displayName}]
    get_custom_endpoint(token, ws_id, es_id) → (conn_str, entity_name)
"""

import base64
import json
import re
import time

import requests

_BASE = "https://api.fabric.microsoft.com/v1"


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── Custom exception ──────────────────────────────────────────────────────────

class NoCustomEndpointError(Exception):
    """Raised when an eventstream has no usable Custom Endpoint source."""


# ── Workspace listing ─────────────────────────────────────────────────────────

def list_workspaces(token: str) -> list[dict]:
    """
    Returns all workspaces the user can access as [{id, displayName, ...}].
    Fabric-capacity workspaces (those with a capacityId) are sorted first.
    """
    resp = requests.get(f"{_BASE}/workspaces", headers=_headers(token), timeout=30)
    resp.raise_for_status()
    workspaces = resp.json().get("value", [])
    # Sort: Fabric-capacity first, then alphabetical
    return sorted(
        workspaces,
        key=lambda w: (not bool(w.get("capacityId")), w.get("displayName", "").lower()),
    )


# ── Eventstream listing ───────────────────────────────────────────────────────

def list_eventstreams(token: str, workspace_id: str) -> list[dict]:
    """
    Returns eventstreams in a workspace as [{id, displayName}].
    Returns [] silently when the workspace has no Fabric capacity or access is denied.
    """
    resp = requests.get(
        f"{_BASE}/workspaces/{workspace_id}/eventstreams",
        headers=_headers(token),
        timeout=30,
    )
    if resp.status_code in (403, 404):
        return []
    resp.raise_for_status()
    return resp.json().get("value", [])


# ── Custom Endpoint connection string ─────────────────────────────────────────

def get_custom_endpoint(
    token: str, workspace_id: str, eventstream_id: str
) -> tuple[str, str]:
    """
    Fetch the first Custom Endpoint source connection string from an eventstream.

    Returns ``(connection_string, entity_name)``.
    The entity_name is parsed from ``EntityPath=`` in the connection string when present.

    Raises ``NoCustomEndpointError`` if:
    - The eventstream has no Custom Endpoint source, OR
    - The source exists but its connection details are not returned by the API.
    """
    es_json = _fetch_definition_json(token, workspace_id, eventstream_id)

    sources = es_json.get("sources", [])
    custom = [s for s in sources if s.get("type") in ("CustomEndpoint", "CustomApp")]

    if not custom:
        raise NoCustomEndpointError(
            "This Eventstream has no Custom Endpoint source.  "
            "Open it in Fabric, add a 'Custom endpoint' source, publish it, "
            "then try again."
        )

    for source in custom:
        props = source.get("properties") or {}
        conn_str = _find_connection_string(props)
        if conn_str:
            entity = _parse_entity_path(conn_str) or source.get("name", "")
            return conn_str, entity

    # Sources were found but the API did not return connection details in properties.
    # This can happen when the Fabric API restricts secret exposure.
    names = ", ".join(s.get("name", "?") for s in custom)
    raise NoCustomEndpointError(
        f"Found Custom Endpoint source(s) [{names}] but the connection string is "
        "not returned by the Fabric API for this eventstream.  "
        "Open the Eventstream in Fabric, select the Custom Endpoint source, go to "
        "the Details pane → SAS Key Authentication, and copy the connection string "
        "here manually."
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _fetch_definition_json(
    token: str, workspace_id: str, eventstream_id: str
) -> dict:
    """
    Call POST getDefinition, handle LRO (202 Accepted) if needed,
    and return the decoded eventstream.json as a Python dict.
    """
    url = (
        f"{_BASE}/workspaces/{workspace_id}"
        f"/eventstreams/{eventstream_id}/getDefinition"
    )
    h = _headers(token)
    resp = requests.post(url, headers=h, timeout=30)

    # Long-running operation — poll Location header
    if resp.status_code == 202:
        location = (
            resp.headers.get("Location")
            or resp.headers.get("location", "")
        )
        if not location:
            raise RuntimeError("getDefinition returned 202 but no Location header.")
        for _ in range(15):
            time.sleep(2)
            poll = requests.get(location, headers=h, timeout=30)
            if not poll.ok:
                continue
            op = poll.json()
            status = op.get("status", "")
            if status == "Succeeded":
                # Result may be at a separate URL or inlined
                result_url = op.get("href") or op.get("resultUrl") or ""
                if result_url.startswith("http"):
                    resp = requests.get(result_url, headers=h, timeout=30)
                else:
                    resp = poll
                break
            if status in ("Failed", "Cancelled"):
                raise RuntimeError(
                    f"getDefinition operation {status}: "
                    + op.get("error", {}).get("message", "Unknown error")
                )
        else:
            raise TimeoutError("getDefinition timed out waiting for the operation.")

    if not resp.ok:
        resp.raise_for_status()

    data = resp.json()
    for part in data.get("definition", {}).get("parts", []):
        if part.get("path") == "eventstream.json":
            payload = part["payload"]
            # Add base64 padding if needed
            payload += "=" * (-len(payload) % 4)
            decoded = base64.b64decode(payload).decode("utf-8")
            return json.loads(decoded)

    # Eventstream.json part not found — return empty so caller gets a clean error
    return {}


# Property key names that might hold a SAS connection string
_CONNSTR_KEYS = (
    "connectionString",
    "connection_string",
    "ConnectionString",
    "primaryConnectionString",
    "secondaryConnectionString",
    "connectionInfo",
    "endpoint",
    "Endpoint",
    "eventHubConnectionString",
    "amqpConnectionString",
    "sasConnectionString",
    "keyInfo",
    "primaryKey",
    "secondaryKey",
)


def _find_connection_string(obj) -> str | None:
    """
    Recursively search an arbitrary JSON value for a Fabric / Azure SAS
    connection string (contains 'Endpoint=sb://').
    """
    if isinstance(obj, str):
        if "Endpoint=sb://" in obj:
            return obj
        return None
    if isinstance(obj, list):
        for item in obj:
            found = _find_connection_string(item)
            if found:
                return found
    if isinstance(obj, dict):
        # Check well-known keys first for speed
        for key in _CONNSTR_KEYS:
            if key in obj:
                found = _find_connection_string(obj[key])
                if found:
                    return found
        # Exhaustive scan for anything else
        for val in obj.values():
            found = _find_connection_string(val)
            if found:
                return found
    return None


def _parse_entity_path(conn_str: str) -> str:
    """Return the EntityPath value from a connection string, or empty string."""
    m = re.search(r"[Ee]ntity[Pp]ath=([^;]+)", conn_str)
    return m.group(1).strip() if m else ""
