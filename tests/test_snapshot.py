"""Tests for envault.snapshot."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.snapshot import (
    SnapshotError,
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    d = tmp_path / "vault"
    d.mkdir()
    return d


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("KEY=value\nSECRET=hunter2\n")
    return f


def test_list_snapshots_empty(vault_dir: Path) -> None:
    assert list_snapshots(vault_dir) == []


def test_create_snapshot_stores_file(vault_dir: Path, env_file: Path) -> None:
    dest = create_snapshot(vault_dir, "v1", env_file)
    assert dest.exists()
    assert dest.read_text() == env_file.read_text()


def test_create_snapshot_creates_meta(vault_dir: Path, env_file: Path) -> None:
    create_snapshot(vault_dir, "v1", env_file)
    meta_file = vault_dir / ".envault_snapshots" / "v1" / "meta.json"
    assert meta_file.exists()


def test_list_snapshots_returns_names(vault_dir: Path, env_file: Path) -> None:
    create_snapshot(vault_dir, "beta", env_file)
    create_snapshot(vault_dir, "alpha", env_file)
    assert list_snapshots(vault_dir) == ["alpha", "beta"]


def test_create_snapshot_empty_name_raises(vault_dir: Path, env_file: Path) -> None:
    with pytest.raises(SnapshotError, match="empty"):
        create_snapshot(vault_dir, "  ", env_file)


def test_create_snapshot_missing_source_raises(vault_dir: Path, tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.env"
    with pytest.raises(SnapshotError, match="Source file not found"):
        create_snapshot(vault_dir, "v1", missing)


def test_create_snapshot_duplicate_raises(vault_dir: Path, env_file: Path) -> None:
    create_snapshot(vault_dir, "v1", env_file)
    with pytest.raises(SnapshotError, match="already exists"):
        create_snapshot(vault_dir, "v1", env_file)


def test_restore_snapshot_overwrites_target(
    vault_dir: Path, env_file: Path, tmp_path: Path
) -> None:
    create_snapshot(vault_dir, "v1", env_file)
    target = tmp_path / "restored.env"
    restore_snapshot(vault_dir, "v1", target)
    assert target.read_text() == env_file.read_text()


def test_restore_snapshot_missing_raises(vault_dir: Path, tmp_path: Path) -> None:
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot(vault_dir, "ghost", tmp_path / "out.env")


def test_delete_snapshot_removes_entry(vault_dir: Path, env_file: Path) -> None:
    create_snapshot(vault_dir, "v1", env_file)
    delete_snapshot(vault_dir, "v1")
    assert list_snapshots(vault_dir) == []


def test_delete_snapshot_missing_raises(vault_dir: Path) -> None:
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot(vault_dir, "nope")
