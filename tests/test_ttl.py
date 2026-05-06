"""Tests for envault.ttl module."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.ttl import (
    TTLError,
    clear_ttl,
    get_expiry,
    is_expired,
    load_ttl,
    save_ttl,
    set_ttl,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_ttl_missing_returns_empty(vault_dir: Path) -> None:
    assert load_ttl(vault_dir) == {}


def test_load_ttl_corrupt_raises(vault_dir: Path) -> None:
    (vault_dir / ".envault_ttl.json").write_text("not json")
    with pytest.raises(TTLError, match="Corrupt"):
        load_ttl(vault_dir)


def test_save_and_load_roundtrip(vault_dir: Path) -> None:
    save_ttl(vault_dir, {"ttl_seconds": 300})
    data = load_ttl(vault_dir)
    assert data["ttl_seconds"] == 300


def test_set_ttl_stores_values(vault_dir: Path) -> None:
    set_ttl(vault_dir, 600)
    data = load_ttl(vault_dir)
    assert data["ttl_seconds"] == 600
    assert "set_at" in data


def test_set_ttl_zero_raises(vault_dir: Path) -> None:
    with pytest.raises(TTLError, match="positive"):
        set_ttl(vault_dir, 0)


def test_set_ttl_negative_raises(vault_dir: Path) -> None:
    with pytest.raises(TTLError, match="positive"):
        set_ttl(vault_dir, -10)


def test_get_expiry_no_ttl_returns_none(vault_dir: Path) -> None:
    assert get_expiry(vault_dir) is None


def test_get_expiry_returns_datetime(vault_dir: Path) -> None:
    set_ttl(vault_dir, 3600)
    expiry = get_expiry(vault_dir)
    assert isinstance(expiry, datetime)
    assert expiry > datetime.now(timezone.utc)


def test_is_expired_false_for_future(vault_dir: Path) -> None:
    set_ttl(vault_dir, 9999)
    assert is_expired(vault_dir) is False


def test_is_expired_true_for_past(vault_dir: Path) -> None:
    set_ttl(vault_dir, 1)
    data = load_ttl(vault_dir)
    past = datetime.now(timezone.utc) - timedelta(seconds=100)
    data["set_at"] = past.isoformat()
    save_ttl(vault_dir, data)
    assert is_expired(vault_dir) is True


def test_is_expired_no_ttl_returns_false(vault_dir: Path) -> None:
    assert is_expired(vault_dir) is False


def test_clear_ttl_removes_fields(vault_dir: Path) -> None:
    set_ttl(vault_dir, 120)
    clear_ttl(vault_dir)
    data = load_ttl(vault_dir)
    assert "ttl_seconds" not in data
    assert "set_at" not in data


def test_clear_ttl_on_empty_vault(vault_dir: Path) -> None:
    clear_ttl(vault_dir)  # should not raise
    assert load_ttl(vault_dir) == {}
