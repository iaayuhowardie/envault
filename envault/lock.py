"""Lock/unlock state tracking for the vault."""
from __future__ import annotations

import json
import time
from pathlib import Path


class LockError(Exception):
    """Raised on lock state errors."""


def _lock_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "lock.json"


def load_lock(vault_dir: Path) -> dict:
    """Return current lock state; defaults to locked."""
    path = _lock_path(vault_dir)
    if not path.exists():
        return {"locked": True, "unlocked_at": None, "unlocked_by": None}
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            raise LockError("lock.json is malformed")
        return data
    except json.JSONDecodeError as exc:
        raise LockError(f"lock.json is corrupt: {exc}") from exc


def save_lock(vault_dir: Path, state: dict) -> None:
    path = _lock_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


def acquire_lock(vault_dir: Path, fingerprint: str) -> None:
    """Mark the vault as locked."""
    state = load_lock(vault_dir)
    state["locked"] = True
    state["unlocked_at"] = None
    state["unlocked_by"] = None
    save_lock(vault_dir, state)


def release_lock(vault_dir: Path, fingerprint: str) -> None:
    """Mark the vault as unlocked, recording who and when."""
    if not fingerprint or not fingerprint.strip():
        raise LockError("fingerprint is required to unlock")
    state = {
        "locked": False,
        "unlocked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "unlocked_by": fingerprint.strip(),
    }
    save_lock(vault_dir, state)


def is_locked(vault_dir: Path) -> bool:
    """Return True if the vault is currently locked."""
    return bool(load_lock(vault_dir).get("locked", True))
