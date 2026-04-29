"""Verify the integrity of encrypted vault files against stored checksums."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List

VERIFY_FILE = ".envault-checksums.json"


class VerifyError(Exception):
    """Raised when verification fails."""


def _checksums_path(vault_dir: Path) -> Path:
    return vault_dir / VERIFY_FILE


def _file_checksum(path: Path) -> str:
    """Return the SHA-256 hex digest of *path*."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_checksums(vault_dir: Path) -> Dict[str, str]:
    """Load stored checksums from *vault_dir*. Returns empty dict if missing."""
    p = _checksums_path(vault_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_checksums(vault_dir: Path, checksums: Dict[str, str]) -> None:
    """Persist *checksums* to *vault_dir*."""
    p = _checksums_path(vault_dir)
    p.write_text(json.dumps(checksums, indent=2), encoding="utf-8")


def record_checksum(vault_dir: Path, encrypted_file: Path) -> str:
    """Compute and store the checksum for *encrypted_file*. Returns the digest."""
    if not encrypted_file.exists():
        raise VerifyError(f"Encrypted file not found: {encrypted_file}")
    digest = _file_checksum(encrypted_file)
    checksums = load_checksums(vault_dir)
    checksums[encrypted_file.name] = digest
    save_checksums(vault_dir, checksums)
    return digest


def verify(vault_dir: Path, encrypted_file: Path) -> bool:
    """Return True if *encrypted_file* matches its stored checksum.

    Raises VerifyError if no checksum has been recorded yet.
    """
    if not encrypted_file.exists():
        raise VerifyError(f"Encrypted file not found: {encrypted_file}")
    checksums = load_checksums(vault_dir)
    name = encrypted_file.name
    if name not in checksums:
        raise VerifyError(
            f"No checksum recorded for '{name}'. Run 'envault lock' first."
        )
    current = _file_checksum(encrypted_file)
    return current == checksums[name]


def verify_all(vault_dir: Path) -> List[str]:
    """Verify every file listed in the checksum store.

    Returns a list of filenames whose checksums do NOT match (tampered/missing).
    """
    checksums = load_checksums(vault_dir)
    tampered: List[str] = []
    for name, stored_digest in checksums.items():
        candidate = vault_dir / name
        if not candidate.exists():
            tampered.append(name)
            continue
        if _file_checksum(candidate) != stored_digest:
            tampered.append(name)
    return tampered
