"""Access control list (ACL) management for envault vaults."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

ACL_FILENAME = ".envault-acl.json"

VALID_ROLES = ("reader", "writer", "admin")


class ACLError(Exception):
    """Raised when an ACL operation fails."""


def _acl_path(vault_dir: Path) -> Path:
    return vault_dir / ACL_FILENAME


def load_acl(vault_dir: Path) -> Dict[str, str]:
    """Load the ACL mapping fingerprint -> role.  Returns {} if missing."""
    path = _acl_path(vault_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ACLError(f"Corrupt ACL file: {exc}") from exc


def save_acl(vault_dir: Path, acl: Dict[str, str]) -> None:
    """Persist the ACL to disk."""
    _acl_path(vault_dir).write_text(json.dumps(acl, indent=2))


def set_role(vault_dir: Path, fingerprint: str, role: str) -> None:
    """Assign *role* to *fingerprint*, creating or updating the entry."""
    if not fingerprint:
        raise ACLError("Fingerprint must not be empty.")
    if role not in VALID_ROLES:
        raise ACLError(f"Invalid role '{role}'. Choose from: {', '.join(VALID_ROLES)}.")
    acl = load_acl(vault_dir)
    acl[fingerprint] = role
    save_acl(vault_dir, acl)


def remove_role(vault_dir: Path, fingerprint: str) -> None:
    """Remove *fingerprint* from the ACL."""
    acl = load_acl(vault_dir)
    if fingerprint not in acl:
        raise ACLError(f"Fingerprint '{fingerprint}' not found in ACL.")
    del acl[fingerprint]
    save_acl(vault_dir, acl)


def get_role(vault_dir: Path, fingerprint: str) -> str | None:
    """Return the role for *fingerprint*, or None if not present."""
    return load_acl(vault_dir).get(fingerprint)


def list_acl(vault_dir: Path) -> List[Dict[str, str]]:
    """Return ACL entries as a list of dicts with 'fingerprint' and 'role' keys."""
    return [
        {"fingerprint": fp, "role": role}
        for fp, role in load_acl(vault_dir).items()
    ]
