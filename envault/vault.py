"""Vault management: encrypt/decrypt .env files and track recipients."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from .crypto import encrypt_file, decrypt_file, GPGError

VAULT_META_FILE = ".envault.json"


class VaultError(Exception):
    """Raised for vault-level errors."""


def _meta_path(directory: str | os.PathLike = ".") -> Path:
    return Path(directory) / VAULT_META_FILE


def load_meta(directory: str | os.PathLike = ".") -> dict:
    """Load vault metadata from .envault.json, or return defaults."""
    path = _meta_path(directory)
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    return {"recipients": [], "env_file": ".env", "encrypted_file": ".env.gpg"}


def save_meta(meta: dict, directory: str | os.PathLike = ".") -> None:
    """Persist vault metadata to .envault.json."""
    path = _meta_path(directory)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
        fh.write("\n")


def add_recipient(fingerprint: str, directory: str | os.PathLike = ".") -> None:
    """Add a GPG fingerprint to the recipient list."""
    meta = load_meta(directory)
    if fingerprint in meta["recipients"]:
        raise VaultError(f"Recipient {fingerprint!r} is already in the vault.")
    meta["recipients"].append(fingerprint)
    save_meta(meta, directory)


def remove_recipient(fingerprint: str, directory: str | os.PathLike = ".") -> None:
    """Remove a GPG fingerprint from the recipient list."""
    meta = load_meta(directory)
    if fingerprint not in meta["recipients"]:
        raise VaultError(f"Recipient {fingerprint!r} not found in the vault.")
    meta["recipients"].remove(fingerprint)
    save_meta(meta, directory)


def lock(directory: str | os.PathLike = ".") -> Path:
    """Encrypt the .env file for all recipients and return the output path."""
    meta = load_meta(directory)
    env_path = Path(directory) / meta["env_file"]
    out_path = Path(directory) / meta["encrypted_file"]
    if not env_path.exists():
        raise VaultError(f"Source file {env_path} does not exist.")
    encrypt_file(str(env_path), meta["recipients"], str(out_path))
    return out_path


def unlock(directory: str | os.PathLike = ".") -> Path:
    """Decrypt the encrypted file and return the output .env path."""
    meta = load_meta(directory)
    enc_path = Path(directory) / meta["encrypted_file"]
    out_path = Path(directory) / meta["env_file"]
    if not enc_path.exists():
        raise VaultError(f"Encrypted file {enc_path} does not exist.")
    decrypt_file(str(enc_path), str(out_path))
    return out_path
