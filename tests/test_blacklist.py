"""Tests for envault.blacklist."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.blacklist import (
    BlacklistError,
    block,
    is_blocked,
    list_blocked,
    load_blacklist,
    save_blacklist,
    unblock,
)

FP1 = "AABBCCDD11223344"
FP2 = "EEFF99887766"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_blacklist_missing_returns_empty(vault_dir: Path) -> None:
    assert load_blacklist(vault_dir) == {}


def test_save_and_load_blacklist_roundtrip(vault_dir: Path) -> None:
    data = {FP1: "compromised", FP2: ""}
    save_blacklist(vault_dir, data)
    assert load_blacklist(vault_dir) == data


def test_load_blacklist_corrupt_raises(vault_dir: Path) -> None:
    (vault_dir / ".blacklist.json").write_text("not json{{{")
    with pytest.raises(BlacklistError, match="Corrupt"):
        load_blacklist(vault_dir)


def test_load_blacklist_wrong_type_raises(vault_dir: Path) -> None:
    (vault_dir / ".blacklist.json").write_text(json.dumps(["a", "b"]))
    with pytest.raises(BlacklistError, match="JSON object"):
        load_blacklist(vault_dir)


def test_block_adds_fingerprint(vault_dir: Path) -> None:
    block(vault_dir, FP1, "leaked")
    bl = load_blacklist(vault_dir)
    assert FP1 in bl
    assert bl[FP1] == "leaked"


def test_block_empty_fingerprint_raises(vault_dir: Path) -> None:
    with pytest.raises(BlacklistError, match="empty"):
        block(vault_dir, "", "reason")


def test_block_duplicate_raises(vault_dir: Path) -> None:
    block(vault_dir, FP1)
    with pytest.raises(BlacklistError, match="already blacklisted"):
        block(vault_dir, FP1)


def test_unblock_removes_fingerprint(vault_dir: Path) -> None:
    block(vault_dir, FP1)
    unblock(vault_dir, FP1)
    assert not is_blocked(vault_dir, FP1)


def test_unblock_missing_raises(vault_dir: Path) -> None:
    with pytest.raises(BlacklistError, match="not blacklisted"):
        unblock(vault_dir, FP1)


def test_is_blocked_true(vault_dir: Path) -> None:
    block(vault_dir, FP1)
    assert is_blocked(vault_dir, FP1) is True


def test_is_blocked_false(vault_dir: Path) -> None:
    assert is_blocked(vault_dir, FP1) is False


def test_list_blocked_returns_all(vault_dir: Path) -> None:
    block(vault_dir, FP1, "reason one")
    block(vault_dir, FP2, "reason two")
    entries = list_blocked(vault_dir)
    fingerprints = {e["fingerprint"] for e in entries}
    assert fingerprints == {FP1, FP2}


def test_list_blocked_empty(vault_dir: Path) -> None:
    assert list_blocked(vault_dir) == []
