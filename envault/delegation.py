"""Delegation support: allow a fingerprint to act on behalf of another."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class DelegationError(Exception):
    """Raised when a delegation operation fails."""


def _delegation_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "delegations.json"


def load_delegations(vault_dir: Path) -> Dict[str, List[str]]:
    """Return mapping of grantor fingerprint -> list of delegate fingerprints."""
    path = _delegation_path(vault_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise DelegationError(f"Corrupt delegations file: {exc}") from exc
    if not isinstance(data, dict):
        raise DelegationError("Delegations file must contain a JSON object")
    return data


def save_delegations(vault_dir: Path, delegations: Dict[str, List[str]]) -> None:
    path = _delegation_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(delegations, indent=2))


def grant(vault_dir: Path, grantor: str, delegate: str) -> None:
    """Grant *delegate* the ability to act on behalf of *grantor*."""
    if not grantor:
        raise DelegationError("Grantor fingerprint must not be empty")
    if not delegate:
        raise DelegationError("Delegate fingerprint must not be empty")
    if grantor == delegate:
        raise DelegationError("A key cannot delegate to itself")
    delegations = load_delegations(vault_dir)
    delegates = delegations.setdefault(grantor, [])
    if delegate in delegates:
        raise DelegationError(f"{delegate!r} is already a delegate for {grantor!r}")
    delegates.append(delegate)
    save_delegations(vault_dir, delegations)


def revoke(vault_dir: Path, grantor: str, delegate: str) -> None:
    """Revoke *delegate*'s delegation from *grantor*."""
    delegations = load_delegations(vault_dir)
    delegates = delegations.get(grantor, [])
    if delegate not in delegates:
        raise DelegationError(f"{delegate!r} is not a delegate for {grantor!r}")
    delegates.remove(delegate)
    if not delegates:
        del delegations[grantor]
    save_delegations(vault_dir, delegations)


def is_delegate(vault_dir: Path, grantor: str, candidate: str) -> bool:
    """Return True if *candidate* is an active delegate for *grantor*."""
    delegations = load_delegations(vault_dir)
    return candidate in delegations.get(grantor, [])
