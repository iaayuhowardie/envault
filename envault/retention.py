"""Retention policy management for encrypted vault snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RETENTION_FILE = ".envault_retention.json"
DEFAULT_MAX_SNAPSHOTS = 10
DEFAULT_MAX_DAYS = 90


class RetentionError(Exception):
    """Raised when a retention policy operation fails."""


def _retention_path(vault_dir: Path) -> Path:
    return vault_dir / RETENTION_FILE


def load_retention(vault_dir: Path) -> dict[str, Any]:
    """Load retention policy from vault directory, returning defaults if absent."""
    path = _retention_path(vault_dir)
    if not path.exists():
        return {"max_snapshots": DEFAULT_MAX_SNAPSHOTS, "max_days": DEFAULT_MAX_DAYS}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise RetentionError(f"Corrupt retention file: {exc}") from exc
    return data


def save_retention(vault_dir: Path, policy: dict[str, Any]) -> None:
    """Persist retention policy to disk."""
    _retention_path(vault_dir).write_text(json.dumps(policy, indent=2))


def set_retention(vault_dir: Path, max_snapshots: int | None = None, max_days: int | None = None) -> dict[str, Any]:
    """Update retention policy fields and persist."""
    if max_snapshots is not None and max_snapshots < 1:
        raise RetentionError("max_snapshots must be at least 1")
    if max_days is not None and max_days < 1:
        raise RetentionError("max_days must be at least 1")
    policy = load_retention(vault_dir)
    if max_snapshots is not None:
        policy["max_snapshots"] = max_snapshots
    if max_days is not None:
        policy["max_days"] = max_days
    save_retention(vault_dir, policy)
    return policy


def apply_retention(vault_dir: Path, snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return snapshots that should be pruned according to the current policy.

    Snapshots are expected to be dicts with at least a ``created_at`` ISO timestamp
    and a ``name`` key, sorted newest-first.
    """
    import datetime

    policy = load_retention(vault_dir)
    max_snapshots: int = policy.get("max_snapshots", DEFAULT_MAX_SNAPSHOTS)
    max_days: int = policy.get("max_days", DEFAULT_MAX_DAYS)
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=max_days)

    prunable: list[dict[str, Any]] = []
    for idx, snap in enumerate(snapshots):
        too_old = False
        created_raw = snap.get("created_at", "")
        if created_raw:
            try:
                created = datetime.datetime.fromisoformat(created_raw)
                too_old = created < cutoff
            except ValueError:
                pass
        exceeds_count = idx >= max_snapshots
        if too_old or exceeds_count:
            prunable.append(snap)
    return prunable
