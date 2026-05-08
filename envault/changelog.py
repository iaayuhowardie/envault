"""Changelog tracking for vault .env file changes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any


class ChangelogError(Exception):
    """Raised when changelog operations fail."""


def _changelog_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "changelog.json"


def load_changelog(vault_dir: Path) -> List[Dict[str, Any]]:
    """Load changelog entries from disk. Returns empty list if missing."""
    path = _changelog_path(vault_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ChangelogError(f"Corrupt changelog: {exc}") from exc
    if not isinstance(data, list):
        raise ChangelogError("Changelog must be a JSON array")
    return data


def _save_changelog(vault_dir: Path, entries: List[Dict[str, Any]]) -> None:
    path = _changelog_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def record_change(
    vault_dir: Path,
    action: str,
    fingerprint: str,
    detail: str = "",
) -> Dict[str, Any]:
    """Append a change entry to the changelog.

    Args:
        vault_dir: Root directory containing the vault.
        action: Short action label, e.g. "lock", "unlock", "rotate".
        fingerprint: GPG fingerprint of the actor.
        detail: Optional human-readable detail string.

    Returns:
        The newly created entry dict.
    """
    if not action:
        raise ChangelogError("action must not be empty")
    if not fingerprint:
        raise ChangelogError("fingerprint must not be empty")

    entries = load_changelog(vault_dir)
    entry: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "fingerprint": fingerprint,
        "detail": detail,
    }
    entries.append(entry)
    _save_changelog(vault_dir, entries)
    return entry


def format_changelog(entries: List[Dict[str, Any]]) -> str:
    """Return a human-readable changelog summary."""
    if not entries:
        return "(no changelog entries)"
    lines = []
    for e in entries:
        ts = e.get("timestamp", "?")
        action = e.get("action", "?")
        fp = e.get("fingerprint", "?")
        detail = e.get("detail", "")
        line = f"[{ts}] {action} by {fp}"
        if detail:
            line += f" — {detail}"
        lines.append(line)
    return "\n".join(lines)
