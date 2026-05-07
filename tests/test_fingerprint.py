"""Tests for envault.fingerprint."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.fingerprint import (
    FingerprintError,
    _registry_path,
    load_registry,
    save_registry,
    register,
    unregister,
    resolve,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    return tmp_path


def test_load_registry_missing_returns_empty(vault_dir: Path) -> None:
    assert load_registry(vault_dir) == {}


def test_save_and_load_registry_roundtrip(vault_dir: Path) -> None:
    data = {"alice": "AAAA1111", "bob": "BBBB2222"}
    save_registry(vault_dir, data)
    assert load_registry(vault_dir) == data


def test_load_registry_corrupt_raises(vault_dir: Path) -> None:
    _registry_path(vault_dir).write_text("not json{{{")
    with pytest.raises(FingerprintError, match="Corrupt"):
        load_registry(vault_dir)


def test_load_registry_wrong_type_raises(vault_dir: Path) -> None:
    _registry_path(vault_dir).write_text(json.dumps(["list", "not", "dict"]))
    with pytest.raises(FingerprintError, match="JSON object"):
        load_registry(vault_dir)


def test_register_stores_entry(vault_dir: Path) -> None:
    register(vault_dir, "carol", "CCCC3333")
    assert load_registry(vault_dir)["carol"] == "CCCC3333"


def test_register_overwrites_existing(vault_dir: Path) -> None:
    register(vault_dir, "alice", "OLD")
    register(vault_dir, "alice", "NEW")
    assert load_registry(vault_dir)["alice"] == "NEW"


def test_register_empty_alias_raises(vault_dir: Path) -> None:
    with pytest.raises(FingerprintError, match="Alias"):
        register(vault_dir, "  ", "CCCC3333")


def test_register_empty_fingerprint_raises(vault_dir: Path) -> None:
    with pytest.raises(FingerprintError, match="Fingerprint"):
        register(vault_dir, "dave", "")


def test_unregister_removes_entry(vault_dir: Path) -> None:
    register(vault_dir, "eve", "EEEE5555")
    unregister(vault_dir, "eve")
    assert "eve" not in load_registry(vault_dir)


def test_unregister_missing_raises(vault_dir: Path) -> None:
    with pytest.raises(FingerprintError, match="not found"):
        unregister(vault_dir, "ghost")


def test_resolve_known_alias(vault_dir: Path) -> None:
    register(vault_dir, "frank", "FFFF6666")
    assert resolve(vault_dir, "frank") == "FFFF6666"


def test_resolve_unknown_returns_value_unchanged(vault_dir: Path) -> None:
    assert resolve(vault_dir, "RAWFINGERPRINT") == "RAWFINGERPRINT"
