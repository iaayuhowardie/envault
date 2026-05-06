"""Vault storage quota tracking and enforcement."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

QUOTA_FILE = ".quota.json"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


class QuotaError(Exception):
    """Raised when a quota operation fails."""


def _quota_path(vault_dir: str) -> Path:
    return Path(vault_dir) / QUOTA_FILE


def load_quota(vault_dir: str) -> Dict:
    """Load quota config from vault directory."""
    path = _quota_path(vault_dir)
    if not path.exists():
        return {"max_bytes": DEFAULT_MAX_BYTES, "warn_threshold": 0.8}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise QuotaError(f"Corrupt quota file: {exc}") from exc


def save_quota(vault_dir: str, config: Dict) -> None:
    """Persist quota config to vault directory."""
    _quota_path(vault_dir).write_text(json.dumps(config, indent=2))


def set_quota(vault_dir: str, max_bytes: int, warn_threshold: float = 0.8) -> None:
    """Set the maximum allowed vault size in bytes."""
    if max_bytes <= 0:
        raise QuotaError("max_bytes must be a positive integer")
    if not (0.0 < warn_threshold < 1.0):
        raise QuotaError("warn_threshold must be between 0 and 1 (exclusive)")
    config = load_quota(vault_dir)
    config["max_bytes"] = max_bytes
    config["warn_threshold"] = warn_threshold
    save_quota(vault_dir, config)


def vault_size(vault_dir: str) -> int:
    """Return total byte size of all files in the vault directory."""
    total = 0
    for root, _dirs, files in os.walk(vault_dir):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def check_quota(vault_dir: str) -> Dict:
    """Check current usage against quota. Returns status dict.

    Raises QuotaError if the vault exceeds max_bytes.
    """
    config = load_quota(vault_dir)
    max_bytes: int = config["max_bytes"]
    warn_threshold: float = config["warn_threshold"]
    used = vault_size(vault_dir)
    ratio = used / max_bytes if max_bytes else 0.0
    status = {
        "used_bytes": used,
        "max_bytes": max_bytes,
        "ratio": ratio,
        "warning": ratio >= warn_threshold,
        "exceeded": used > max_bytes,
    }
    if status["exceeded"]:
        raise QuotaError(
            f"Vault size {used} bytes exceeds quota of {max_bytes} bytes"
        )
    return status
