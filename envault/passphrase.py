"""Passphrase policy enforcement for envault vaults."""
from __future__ import annotations

import json
from pathlib import Path

POLICY_FILE = ".envault_passphrase_policy.json"

DEFAULT_POLICY: dict = {
    "min_length": 12,
    "require_uppercase": True,
    "require_digit": True,
    "require_special": True,
}

SPECIAL_CHARS = set("!@#$%^&*()-_=+[]{}|;:',.<>?/`~")


class PassphraseError(Exception):
    """Raised for passphrase policy violations or configuration errors."""


def _policy_path(vault_dir: str | Path) -> Path:
    return Path(vault_dir) / POLICY_FILE


def load_policy(vault_dir: str | Path) -> dict:
    """Load passphrase policy from vault_dir; return defaults if missing."""
    path = _policy_path(vault_dir)
    if not path.exists():
        return dict(DEFAULT_POLICY)
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise PassphraseError(f"Corrupt policy file: {exc}") from exc
    if not isinstance(data, dict):
        raise PassphraseError("Policy file must contain a JSON object.")
    return {**DEFAULT_POLICY, **data}


def save_policy(vault_dir: str | Path, policy: dict) -> None:
    """Persist passphrase policy to vault_dir."""
    path = _policy_path(vault_dir)
    path.write_text(json.dumps(policy, indent=2))


def set_policy(
    vault_dir: str | Path,
    *,
    min_length: int | None = None,
    require_uppercase: bool | None = None,
    require_digit: bool | None = None,
    require_special: bool | None = None,
) -> dict:
    """Update one or more policy fields and persist."""
    policy = load_policy(vault_dir)
    if min_length is not None:
        if min_length < 1:
            raise PassphraseError("min_length must be at least 1.")
        policy["min_length"] = min_length
    if require_uppercase is not None:
        policy["require_uppercase"] = require_uppercase
    if require_digit is not None:
        policy["require_digit"] = require_digit
    if require_special is not None:
        policy["require_special"] = require_special
    save_policy(vault_dir, policy)
    return policy


def validate_passphrase(passphrase: str, policy: dict) -> None:
    """Raise PassphraseError if passphrase violates the given policy."""
    if len(passphrase) < policy.get("min_length", 1):
        raise PassphraseError(
            f"Passphrase must be at least {policy['min_length']} characters long."
        )
    if policy.get("require_uppercase") and not any(c.isupper() for c in passphrase):
        raise PassphraseError("Passphrase must contain at least one uppercase letter.")
    if policy.get("require_digit") and not any(c.isdigit() for c in passphrase):
        raise PassphraseError("Passphrase must contain at least one digit.")
    if policy.get("require_special") and not any(c in SPECIAL_CHARS for c in passphrase):
        raise PassphraseError("Passphrase must contain at least one special character.")
