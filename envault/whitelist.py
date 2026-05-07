"""Whitelist management for envault — restrict operations to approved GPG fingerprints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List


class WhitelistError(Exception):
    """Raised when a whitelist operation fails."""


def _whitelist_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "whitelist.json"


def load_whitelist(vault_dir: Path) -> List[str]:
    """Return the list of approved fingerprints, or [] if none saved."""
    path = _whitelist_path(vault_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise WhitelistError(f"Corrupt whitelist file: {exc}") from exc
    if not isinstance(data, list):
        raise WhitelistError("Whitelist file must contain a JSON array.")
    return data


def save_whitelist(vault_dir: Path, fingerprints: List[str]) -> None:
    """Persist the whitelist to disk."""
    path = _whitelist_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fingerprints, indent=2))


def allow(vault_dir: Path, fingerprint: str) -> List[str]:
    """Add *fingerprint* to the whitelist. Raises if already present."""
    fingerprint = fingerprint.strip().upper()
    if not fingerprint:
        raise WhitelistError("Fingerprint must not be empty.")
    entries = load_whitelist(vault_dir)
    if fingerprint in entries:
        raise WhitelistError(f"Fingerprint already whitelisted: {fingerprint}")
    entries.append(fingerprint)
    save_whitelist(vault_dir, entries)
    return entries


def deny(vault_dir: Path, fingerprint: str) -> List[str]:
    """Remove *fingerprint* from the whitelist. Raises if not present."""
    fingerprint = fingerprint.strip().upper()
    entries = load_whitelist(vault_dir)
    if fingerprint not in entries:
        raise WhitelistError(f"Fingerprint not in whitelist: {fingerprint}")
    entries.remove(fingerprint)
    save_whitelist(vault_dir, entries)
    return entries


def is_allowed(vault_dir: Path, fingerprint: str) -> bool:
    """Return True if *fingerprint* appears in the whitelist.

    An empty whitelist is treated as *allow-all* (feature disabled).
    """
    entries = load_whitelist(vault_dir)
    if not entries:
        return True
    return fingerprint.strip().upper() in entries
