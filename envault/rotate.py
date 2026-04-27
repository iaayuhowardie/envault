"""Key rotation: re-encrypt the vault for an updated recipient list."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from .audit import record
from .crypto import decrypt_file, encrypt_file
from .vault import VaultError, load_meta, save_meta


class RotateError(Exception):
    """Raised when key rotation fails."""


def rotate(
    vault_dir: str | Path,
    *,
    added: list[str] | None = None,
    removed: list[str] | None = None,
    actor: str = "unknown",
) -> None:
    """Re-encrypt the .env file for the current (updated) recipient list.

    Parameters
    ----------
    vault_dir:
        Directory that contains the ``.envault`` meta-file and the encrypted
        ``env.gpg`` artefact.
    added:
        Fingerprints that were *added* in this rotation (informational).
    removed:
        Fingerprints that were *removed* in this rotation (informational).
    actor:
        GPG fingerprint / identifier of the person triggering the rotation.
    """
    vault_dir = Path(vault_dir)
    meta = load_meta(vault_dir)

    recipients: list[str] = meta.get("recipients", [])
    if not recipients:
        raise RotateError("No recipients configured — cannot re-encrypt.")

    encrypted_path = vault_dir / "env.gpg"
    if not encrypted_path.exists():
        raise RotateError(
            f"Encrypted file not found: {encrypted_path}. "
            "Run 'envault lock' first."
        )

    # Decrypt to a temporary file, then re-encrypt for the current recipients.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_plain = Path(tmp) / ".env"
        decrypt_file(str(encrypted_path), str(tmp_plain))

        tmp_enc = Path(tmp) / "env.gpg"
        encrypt_file(str(tmp_plain), str(tmp_enc), recipients)

        # Atomically replace the existing encrypted file.
        shutil.move(str(tmp_enc), str(encrypted_path))

    # Persist any recipient-list changes that the caller already applied to
    # *meta* before calling rotate().
    save_meta(vault_dir, meta)

    record(
        vault_dir,
        action="rotate",
        actor=actor,
        details={
            "added": added or [],
            "removed": removed or [],
            "recipients": recipients,
        },
    )
