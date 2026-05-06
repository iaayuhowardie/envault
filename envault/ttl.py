"""TTL (time-to-live) management for encrypted vault files."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

TTL_FILE = ".envault_ttl.json"


class TTLError(Exception):
    """Raised when a TTL operation fails."""


def _ttl_path(vault_dir: Path) -> Path:
    return vault_dir / TTL_FILE


def load_ttl(vault_dir: Path) -> dict:
    """Load TTL config from vault_dir; return empty dict if missing."""
    path = _ttl_path(vault_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise TTLError(f"Corrupt TTL file: {exc}") from exc


def save_ttl(vault_dir: Path, data: dict) -> None:
    """Persist TTL config to vault_dir."""
    _ttl_path(vault_dir).write_text(json.dumps(data, indent=2))


def set_ttl(vault_dir: Path, seconds: int) -> None:
    """Set a TTL (in seconds) for the vault. Must be a positive integer."""
    if seconds <= 0:
        raise TTLError("TTL must be a positive number of seconds.")
    data = load_ttl(vault_dir)
    data["ttl_seconds"] = seconds
    data["set_at"] = datetime.now(timezone.utc).isoformat()
    save_ttl(vault_dir, data)


def get_expiry(vault_dir: Path) -> Optional[datetime]:
    """Return the expiry datetime for the vault, or None if no TTL is set."""
    data = load_ttl(vault_dir)
    if "ttl_seconds" not in data or "set_at" not in data:
        return None
    set_at = datetime.fromisoformat(data["set_at"])
    return set_at + timedelta(seconds=data["ttl_seconds"])


def is_expired(vault_dir: Path) -> bool:
    """Return True if the vault TTL has elapsed."""
    expiry = get_expiry(vault_dir)
    if expiry is None:
        return False
    return datetime.now(timezone.utc) >= expiry


def clear_ttl(vault_dir: Path) -> None:
    """Remove TTL configuration from the vault."""
    data = load_ttl(vault_dir)
    data.pop("ttl_seconds", None)
    data.pop("set_at", None)
    save_ttl(vault_dir, data)
