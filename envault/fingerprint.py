"""Fingerprint registry — map human-readable aliases to GPG fingerprints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


class FingerprintError(Exception):
    """Raised when a fingerprint operation fails."""


def _registry_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "fingerprints.json"


def load_registry(vault_dir: Path) -> Dict[str, str]:
    """Return alias -> fingerprint mapping, or {} if not yet created."""
    path = _registry_path(vault_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise FingerprintError(f"Corrupt fingerprint registry: {exc}") from exc
    if not isinstance(data, dict):
        raise FingerprintError("Fingerprint registry must be a JSON object.")
    return data


def save_registry(vault_dir: Path, registry: Dict[str, str]) -> None:
    """Persist *registry* to disk."""
    path = _registry_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2))


def register(vault_dir: Path, alias: str, fingerprint: str) -> None:
    """Associate *alias* with *fingerprint*, overwriting any previous mapping."""
    if not alias.strip():
        raise FingerprintError("Alias must not be empty.")
    if not fingerprint.strip():
        raise FingerprintError("Fingerprint must not be empty.")
    registry = load_registry(vault_dir)
    registry[alias.strip()] = fingerprint.strip()
    save_registry(vault_dir, registry)


def unregister(vault_dir: Path, alias: str) -> None:
    """Remove *alias* from the registry; raise if it does not exist."""
    registry = load_registry(vault_dir)
    if alias not in registry:
        raise FingerprintError(f"Alias '{alias}' not found in registry.")
    del registry[alias]
    save_registry(vault_dir, registry)


def resolve(vault_dir: Path, alias_or_fp: str) -> str:
    """Return the fingerprint for *alias_or_fp*.

    If the value is already a fingerprint (not found as an alias) it is
    returned unchanged, allowing callers to pass either form.
    """
    registry = load_registry(vault_dir)
    return registry.get(alias_or_fp, alias_or_fp)
