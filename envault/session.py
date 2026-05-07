"""Session management: track active unlock sessions with expiry."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional


class SessionError(Exception):
    """Raised on session-related failures."""


def _session_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "session.json"


def load_session(vault_dir: Path) -> dict:
    """Load the current session, returning empty dict if missing or corrupt."""
    path = _session_path(vault_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_session(vault_dir: Path, data: dict) -> None:
    """Persist session data to disk."""
    path = _session_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def open_session(vault_dir: Path, fingerprint: str, ttl_seconds: int = 3600) -> dict:
    """Start a new session for *fingerprint* expiring after *ttl_seconds*."""
    if not fingerprint:
        raise SessionError("fingerprint must not be empty")
    if ttl_seconds <= 0:
        raise SessionError("ttl_seconds must be positive")
    now = time.time()
    session = {
        "fingerprint": fingerprint,
        "created_at": now,
        "expires_at": now + ttl_seconds,
    }
    save_session(vault_dir, session)
    return session


def close_session(vault_dir: Path) -> None:
    """Invalidate the current session by removing the session file."""
    path = _session_path(vault_dir)
    if path.exists():
        path.unlink()


def is_session_active(vault_dir: Path) -> bool:
    """Return True if a valid, non-expired session exists."""
    session = load_session(vault_dir)
    if not session:
        return False
    return time.time() < session.get("expires_at", 0)


def get_active_fingerprint(vault_dir: Path) -> Optional[str]:
    """Return the fingerprint of the active session, or None."""
    if not is_session_active(vault_dir):
        return None
    return load_session(vault_dir).get("fingerprint")
