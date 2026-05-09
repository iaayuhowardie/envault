"""Re-encryption of vault secrets under a new primary GPG key."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from envault.crypto import GPGError, decrypt_file, encrypt_file
from envault.vault import VaultError, load_meta, save_meta
from envault.audit import record as audit_record


class RekeyError(Exception):
    """Raised when a re-key operation fails."""


_REKEY_STATE_FILE = ".rekey_state.json"


def _rekey_state_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / _REKEY_STATE_FILE


def load_rekey_state(vault_dir: Path) -> dict:
    """Return persisted re-key state, or empty dict if none exists."""
    path = _rekey_state_path(vault_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def save_rekey_state(vault_dir: Path, state: dict) -> None:
    path = _rekey_state_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


def clear_rekey_state(vault_dir: Path) -> None:
    path = _rekey_state_path(vault_dir)
    if path.exists():
        path.unlink()


def rekey(
    vault_dir: Path,
    new_recipients: Optional[List[str]] = None,
    passphrase: Optional[str] = None,
) -> None:
    """Re-encrypt the vault's encrypted .env file for a new set of recipients.

    If *new_recipients* is None the existing recipients from vault meta are used,
    which effectively re-encrypts under the same keys (useful after key rotation).
    """
    meta = load_meta(vault_dir)
    current_recipients: List[str] = meta.get("recipients", [])

    if not current_recipients and not new_recipients:
        raise RekeyError("No recipients configured — cannot re-key.")

    recipients = new_recipients if new_recipients is not None else current_recipients

    enc_file = vault_dir / meta.get("encrypted_file", ".env.gpg")
    if not enc_file.exists():
        raise RekeyError(f"Encrypted file not found: {enc_file}")

    tmp_plain = vault_dir / ".env.rekey_tmp"
    try:
        decrypt_file(enc_file, tmp_plain, passphrase=passphrase)
        encrypt_file(tmp_plain, enc_file, recipients=recipients)
    except GPGError as exc:
        raise RekeyError(f"GPG operation failed during re-key: {exc}") from exc
    finally:
        if tmp_plain.exists():
            tmp_plain.unlink()

    if new_recipients is not None:
        meta["recipients"] = recipients
        save_meta(vault_dir, meta)

    audit_record(vault_dir, "rekey", {"recipients": recipients})
    clear_rekey_state(vault_dir)
