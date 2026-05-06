"""Tests for envault.retention."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest

from envault.retention import (
    DEFAULT_MAX_DAYS,
    DEFAULT_MAX_SNAPSHOTS,
    RetentionError,
    apply_retention,
    load_retention,
    save_retention,
    set_retention,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_retention_missing_returns_defaults(vault_dir: Path) -> None:
    policy = load_retention(vault_dir)
    assert policy["max_snapshots"] == DEFAULT_MAX_SNAPSHOTS
    assert policy["max_days"] == DEFAULT_MAX_DAYS


def test_save_and_load_retention_roundtrip(vault_dir: Path) -> None:
    save_retention(vault_dir, {"max_snapshots": 5, "max_days": 30})
    policy = load_retention(vault_dir)
    assert policy["max_snapshots"] == 5
    assert policy["max_days"] == 30


def test_load_retention_corrupt_raises(vault_dir: Path) -> None:
    (vault_dir / ".envault_retention.json").write_text("not json")
    with pytest.raises(RetentionError, match="Corrupt"):
        load_retention(vault_dir)


def test_set_retention_updates_max_snapshots(vault_dir: Path) -> None:
    policy = set_retention(vault_dir, max_snapshots=3)
    assert policy["max_snapshots"] == 3
    assert policy["max_days"] == DEFAULT_MAX_DAYS


def test_set_retention_updates_max_days(vault_dir: Path) -> None:
    policy = set_retention(vault_dir, max_days=14)
    assert policy["max_days"] == 14


def test_set_retention_invalid_max_snapshots_raises(vault_dir: Path) -> None:
    with pytest.raises(RetentionError, match="max_snapshots"):
        set_retention(vault_dir, max_snapshots=0)


def test_set_retention_invalid_max_days_raises(vault_dir: Path) -> None:
    with pytest.raises(RetentionError, match="max_days"):
        set_retention(vault_dir, max_days=-1)


def _make_snapshot(name: str, days_ago: int) -> dict:
    created = datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)
    return {"name": name, "created_at": created.isoformat()}


def test_apply_retention_prunes_old_snapshots(vault_dir: Path) -> None:
    set_retention(vault_dir, max_days=30)
    snapshots = [
        _make_snapshot("snap_new.enc", 5),
        _make_snapshot("snap_old.enc", 60),
    ]
    prunable = apply_retention(vault_dir, snapshots)
    names = [s["name"] for s in prunable]
    assert "snap_old.enc" in names
    assert "snap_new.enc" not in names


def test_apply_retention_prunes_excess_count(vault_dir: Path) -> None:
    set_retention(vault_dir, max_snapshots=2, max_days=9999)
    snapshots = [_make_snapshot(f"snap_{i}.enc", i) for i in range(5)]
    prunable = apply_retention(vault_dir, snapshots)
    assert len(prunable) == 3


def test_apply_retention_nothing_to_prune(vault_dir: Path) -> None:
    set_retention(vault_dir, max_snapshots=10, max_days=365)
    snapshots = [_make_snapshot(f"snap_{i}.enc", i) for i in range(3)]
    prunable = apply_retention(vault_dir, snapshots)
    assert prunable == []
