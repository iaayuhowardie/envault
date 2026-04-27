"""Audit log for envault operations (lock/unlock/add/remove)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

AUDIT_FILENAME = ".envault-audit.json"


class AuditError(Exception):
    """Raised when audit log operations fail."""


def _audit_path(vault_dir: str | Path) -> Path:
    return Path(vault_dir) / AUDIT_FILENAME


def load_log(vault_dir: str | Path) -> List[Dict[str, Any]]:
    """Load the audit log from *vault_dir*. Returns an empty list if none exists."""
    path = _audit_path(vault_dir)
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise AuditError(f"Corrupt audit log at {path}: expected a JSON array")
        return data
    except json.JSONDecodeError as exc:
        raise AuditError(f"Corrupt audit log at {path}: {exc}") from exc


def _save_log(vault_dir: str | Path, entries: List[Dict[str, Any]]) -> None:
    path = _audit_path(vault_dir)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2)


def record(
    vault_dir: str | Path,
    action: str,
    actor: str | None = None,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Append a new entry to the audit log and return it.

    Parameters
    ----------
    vault_dir:
        Directory that contains the vault (same as used by vault.py).
    action:
        Short verb describing the operation, e.g. ``"lock"``, ``"unlock"``,
        ``"add_recipient"``, ``"remove_recipient"``.
    actor:
        GPG key-id or username performing the action.  Defaults to the
        current OS user when *None*.
    details:
        Optional mapping of extra context to store alongside the entry.
    """
    entry: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor or os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
    }
    if details:
        entry["details"] = details

    entries = load_log(vault_dir)
    entries.append(entry)
    _save_log(vault_dir, entries)
    return entry


def clear_log(vault_dir: str | Path) -> None:
    """Remove all entries from the audit log (keeps the file)."""
    _save_log(vault_dir, [])
