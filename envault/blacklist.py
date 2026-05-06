"""Blacklist management for envault — block specific GPG fingerprints from accessing vaults."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

BLACKLIST_FILE = ".blacklist.json"


class BlacklistError(Exception):
    """Raised when a blacklist operation fails."""


def _blacklist_path(vault_dir: Path) -> Path:
    return vault_dir / BLACKLIST_FILE


def load_blacklist(vault_dir: Path) -> Dict[str, str]:
    """Load the blacklist from *vault_dir*.

    Returns a dict mapping fingerprint -> reason string.
    Returns an empty dict when the file does not exist.
    """
    path = _blacklist_path(vault_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise BlacklistError(f"Corrupt blacklist file: {exc}") from exc
    if not isinstance(data, dict):
        raise BlacklistError("Blacklist file must contain a JSON object.")
    return data


def save_blacklist(vault_dir: Path, blacklist: Dict[str, str]) -> None:
    """Persist *blacklist* to *vault_dir*."""
    _blacklist_path(vault_dir).write_text(json.dumps(blacklist, indent=2))


def block(vault_dir: Path, fingerprint: str, reason: str = "") -> None:
    """Add *fingerprint* to the blacklist.

    Raises :class:`BlacklistError` if the fingerprint is already blocked.
    """
    if not fingerprint:
        raise BlacklistError("Fingerprint must not be empty.")
    bl = load_blacklist(vault_dir)
    if fingerprint in bl:
        raise BlacklistError(f"Fingerprint {fingerprint!r} is already blacklisted.")
    bl[fingerprint] = reason
    save_blacklist(vault_dir, bl)


def unblock(vault_dir: Path, fingerprint: str) -> None:
    """Remove *fingerprint* from the blacklist.

    Raises :class:`BlacklistError` if the fingerprint is not found.
    """
    bl = load_blacklist(vault_dir)
    if fingerprint not in bl:
        raise BlacklistError(f"Fingerprint {fingerprint!r} is not blacklisted.")
    del bl[fingerprint]
    save_blacklist(vault_dir, bl)


def is_blocked(vault_dir: Path, fingerprint: str) -> bool:
    """Return *True* if *fingerprint* is on the blacklist."""
    return fingerprint in load_blacklist(vault_dir)


def list_blocked(vault_dir: Path) -> List[Dict[str, str]]:
    """Return a list of dicts with 'fingerprint' and 'reason' keys."""
    bl = load_blacklist(vault_dir)
    return [{"fingerprint": fp, "reason": reason} for fp, reason in bl.items()]
