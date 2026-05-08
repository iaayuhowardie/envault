"""Trust level management for GPG fingerprints in the vault."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

TRUST_LEVELS = ("unknown", "untrusted", "marginal", "full", "ultimate")


class TrustError(Exception):
    """Raised when a trust operation fails."""


def _trust_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "trust.json"


def load_trust(vault_dir: Path) -> Dict[str, str]:
    """Load the trust registry from disk. Returns empty dict if missing."""
    path = _trust_path(vault_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise TrustError(f"Corrupt trust file: {exc}") from exc
    if not isinstance(data, dict):
        raise TrustError("Trust file must be a JSON object")
    return data


def save_trust(vault_dir: Path, trust: Dict[str, str]) -> None:
    """Persist the trust registry to disk."""
    path = _trust_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trust, indent=2))


def set_trust(vault_dir: Path, fingerprint: str, level: str) -> None:
    """Assign a trust level to a fingerprint."""
    if not fingerprint:
        raise TrustError("Fingerprint must not be empty")
    if level not in TRUST_LEVELS:
        raise TrustError(
            f"Invalid trust level '{level}'. Choose from: {', '.join(TRUST_LEVELS)}"
        )
    trust = load_trust(vault_dir)
    trust[fingerprint] = level
    save_trust(vault_dir, trust)


def get_trust(vault_dir: Path, fingerprint: str) -> Optional[str]:
    """Return the trust level for a fingerprint, or None if not set."""
    trust = load_trust(vault_dir)
    return trust.get(fingerprint)


def remove_trust(vault_dir: Path, fingerprint: str) -> None:
    """Remove a fingerprint from the trust registry."""
    trust = load_trust(vault_dir)
    if fingerprint not in trust:
        raise TrustError(f"Fingerprint '{fingerprint}' not found in trust registry")
    del trust[fingerprint]
    save_trust(vault_dir, trust)
