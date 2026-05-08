"""Tests for envault.lock."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.lock import (
    LockError,
    acquire_lock,
    is_locked,
    load_lock,
    release_lock,
    save_lock,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    return tmp_path


def test_load_lock_missing_returns_defaults(vault_dir: Path) -> None:
    state = load_lock(vault_dir)
    assert state["locked"] is True
    assert state["unlocked_at"] is None
    assert state["unlocked_by"] is None


def test_save_and_load_lock_roundtrip(vault_dir: Path) -> None:
    data = {"locked": False, "unlocked_at": "2024-01-01T00:00:00Z", "unlocked_by": "ABCD1234"}
    save_lock(vault_dir, data)
    assert load_lock(vault_dir) == data


def test_load_lock_corrupt_raises(vault_dir: Path) -> None:
    (vault_dir / ".envault" / "lock.json").write_text("not-json")
    with pytest.raises(LockError, match="corrupt"):
        load_lock(vault_dir)


def test_load_lock_wrong_type_raises(vault_dir: Path) -> None:
    (vault_dir / ".envault" / "lock.json").write_text(json.dumps([1, 2, 3]))
    with pytest.raises(LockError, match="malformed"):
        load_lock(vault_dir)


def test_release_lock_stores_state(vault_dir: Path) -> None:
    release_lock(vault_dir, "DEADBEEF")
    state = load_lock(vault_dir)
    assert state["locked"] is False
    assert state["unlocked_by"] == "DEADBEEF"
    assert state["unlocked_at"] is not None


def test_acquire_lock_marks_locked(vault_dir: Path) -> None:
    release_lock(vault_dir, "DEADBEEF")
    acquire_lock(vault_dir, "DEADBEEF")
    state = load_lock(vault_dir)
    assert state["locked"] is True
    assert state["unlocked_by"] is None


def test_is_locked_defaults_to_true(vault_dir: Path) -> None:
    assert is_locked(vault_dir) is True


def test_is_locked_false_after_release(vault_dir: Path) -> None:
    release_lock(vault_dir, "DEADBEEF")
    assert is_locked(vault_dir) is False


def test_release_lock_empty_fingerprint_raises(vault_dir: Path) -> None:
    with pytest.raises(LockError, match="fingerprint"):
        release_lock(vault_dir, "   ")


def test_save_lock_creates_parent_dirs(tmp_path: Path) -> None:
    """Parent .envault dir need not pre-exist."""
    save_lock(tmp_path, {"locked": True, "unlocked_at": None, "unlocked_by": None})
    assert (tmp_path / ".envault" / "lock.json").exists()
