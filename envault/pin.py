"""Pin management: lock a vault to a specific encrypted-file checksum."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

PIN_FILENAME = ".envault-pin"


class PinError(Exception):
    """Raised when a pin operation fails."""


def _pin_path(vault_dir: Path) -> Path:
    return vault_dir / PIN_FILENAME


def load_pin(vault_dir: Path) -> Dict[str, str]:
    """Return the current pin record, or an empty dict if none exists."""
    path = _pin_path(vault_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise PinError(f"Corrupt pin file: {exc}") from exc


def save_pin(vault_dir: Path, record: Dict[str, str]) -> None:
    """Persist *record* to the pin file."""
    _pin_path(vault_dir).write_text(json.dumps(record, indent=2))


def set_pin(vault_dir: Path, encrypted_file: Path) -> str:
    """Record the current checksum of *encrypted_file* as the active pin.

    Returns the hex checksum that was stored.
    """
    if not encrypted_file.exists():
        raise PinError(f"Encrypted file not found: {encrypted_file}")

    import hashlib

    digest = hashlib.sha256(encrypted_file.read_bytes()).hexdigest()
    record = load_pin(vault_dir)
    record[str(encrypted_file.resolve())] = digest
    save_pin(vault_dir, record)
    return digest


def check_pin(vault_dir: Path, encrypted_file: Path) -> bool:
    """Return True if *encrypted_file* matches its pinned checksum.

    Returns True also when no pin has been recorded for the file.
    """
    record = load_pin(vault_dir)
    key = str(encrypted_file.resolve())
    if key not in record:
        return True

    import hashlib

    if not encrypted_file.exists():
        raise PinError(f"Encrypted file not found: {encrypted_file}")

    digest = hashlib.sha256(encrypted_file.read_bytes()).hexdigest()
    return digest == record[key]


def remove_pin(vault_dir: Path, encrypted_file: Optional[Path] = None) -> None:
    """Remove the pin for *encrypted_file*, or clear all pins if None."""
    if encrypted_file is None:
        save_pin(vault_dir, {})
        return
    record = load_pin(vault_dir)
    key = str(encrypted_file.resolve())
    if key not in record:
        raise PinError(f"No pin found for: {encrypted_file}")
    del record[key]
    save_pin(vault_dir, record)
