"""Timeout management for encrypted vault access sessions."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

TIMEOUT_FILENAME = ".envault_timeout.json"
DEFAULT_TIMEOUT_SECONDS = 900  # 15 minutes


class TimeoutError(Exception):  # noqa: A001
    """Raised when a timeout operation fails."""


def _timeout_path(vault_dir: Path) -> Path:
    return vault_dir / TIMEOUT_FILENAME


def load_timeout(vault_dir: Path) -> dict:
    """Load timeout config, returning defaults if missing or corrupt."""
    path = _timeout_path(vault_dir)
    if not path.exists():
        return {"seconds": DEFAULT_TIMEOUT_SECONDS, "session_start": None}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise TimeoutError(f"Corrupt timeout file: {exc}") from exc


def save_timeout(vault_dir: Path, data: dict) -> None:
    """Persist timeout config to disk."""
    _timeout_path(vault_dir).write_text(json.dumps(data, indent=2))


def set_timeout(vault_dir: Path, seconds: int) -> None:
    """Configure the inactivity timeout duration."""
    if seconds <= 0:
        raise TimeoutError("Timeout must be a positive number of seconds.")
    data = load_timeout(vault_dir)
    data["seconds"] = seconds
    save_timeout(vault_dir, data)


def start_session(vault_dir: Path) -> float:
    """Record the current time as the session start."""
    data = load_timeout(vault_dir)
    now = time.time()
    data["session_start"] = now
    save_timeout(vault_dir, data)
    return now


def clear_session(vault_dir: Path) -> None:
    """Clear the active session timestamp."""
    data = load_timeout(vault_dir)
    data["session_start"] = None
    save_timeout(vault_dir, data)


def is_expired(vault_dir: Path, *, now: Optional[float] = None) -> bool:
    """Return True if the current session has exceeded the configured timeout."""
    data = load_timeout(vault_dir)
    session_start = data.get("session_start")
    if session_start is None:
        return True
    elapsed = (now if now is not None else time.time()) - session_start
    return elapsed >= data.get("seconds", DEFAULT_TIMEOUT_SECONDS)


def remaining(vault_dir: Path, *, now: Optional[float] = None) -> float:
    """Return seconds remaining in the session, or 0.0 if expired."""
    data = load_timeout(vault_dir)
    session_start = data.get("session_start")
    if session_start is None:
        return 0.0
    elapsed = (now if now is not None else time.time()) - session_start
    secs = data.get("seconds", DEFAULT_TIMEOUT_SECONDS)
    return max(0.0, secs - elapsed)
