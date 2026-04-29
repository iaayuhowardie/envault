"""Tests for envault.verify."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.verify import (
    VerifyError,
    _checksums_path,
    load_checksums,
    record_checksum,
    save_checksums,
    verify,
    verify_all,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------

def test_load_checksums_missing_returns_empty(vault_dir: Path) -> None:
    assert load_checksums(vault_dir) == {}


def test_save_and_load_checksums_roundtrip(vault_dir: Path) -> None:
    data = {"env.gpg": "abc123", "other.gpg": "def456"}
    save_checksums(vault_dir, data)
    assert load_checksums(vault_dir) == data


# ---------------------------------------------------------------------------
# record_checksum
# ---------------------------------------------------------------------------

def test_record_checksum_creates_entry(vault_dir: Path) -> None:
    enc = vault_dir / "env.gpg"
    enc.write_bytes(b"encrypted-data")
    digest = record_checksum(vault_dir, enc)
    assert len(digest) == 64  # SHA-256 hex
    stored = load_checksums(vault_dir)
    assert stored["env.gpg"] == digest


def test_record_checksum_updates_on_change(vault_dir: Path) -> None:
    enc = vault_dir / "env.gpg"
    enc.write_bytes(b"first")
    d1 = record_checksum(vault_dir, enc)
    enc.write_bytes(b"second")
    d2 = record_checksum(vault_dir, enc)
    assert d1 != d2


def test_record_checksum_missing_file_raises(vault_dir: Path) -> None:
    with pytest.raises(VerifyError, match="not found"):
        record_checksum(vault_dir, vault_dir / "ghost.gpg")


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------

def test_verify_returns_true_for_unchanged_file(vault_dir: Path) -> None:
    enc = vault_dir / "env.gpg"
    enc.write_bytes(b"stable")
    record_checksum(vault_dir, enc)
    assert verify(vault_dir, enc) is True


def test_verify_returns_false_after_tampering(vault_dir: Path) -> None:
    enc = vault_dir / "env.gpg"
    enc.write_bytes(b"original")
    record_checksum(vault_dir, enc)
    enc.write_bytes(b"tampered!")
    assert verify(vault_dir, enc) is False


def test_verify_raises_when_no_checksum_recorded(vault_dir: Path) -> None:
    enc = vault_dir / "env.gpg"
    enc.write_bytes(b"data")
    with pytest.raises(VerifyError, match="No checksum recorded"):
        verify(vault_dir, enc)


def test_verify_missing_file_raises(vault_dir: Path) -> None:
    with pytest.raises(VerifyError, match="not found"):
        verify(vault_dir, vault_dir / "missing.gpg")


# ---------------------------------------------------------------------------
# verify_all
# ---------------------------------------------------------------------------

def test_verify_all_empty_returns_empty_list(vault_dir: Path) -> None:
    assert verify_all(vault_dir) == []


def test_verify_all_detects_tampered_file(vault_dir: Path) -> None:
    enc = vault_dir / "env.gpg"
    enc.write_bytes(b"good")
    record_checksum(vault_dir, enc)
    enc.write_bytes(b"bad")
    assert verify_all(vault_dir) == ["env.gpg"]


def test_verify_all_detects_missing_file(vault_dir: Path) -> None:
    enc = vault_dir / "env.gpg"
    enc.write_bytes(b"data")
    record_checksum(vault_dir, enc)
    enc.unlink()
    assert verify_all(vault_dir) == ["env.gpg"]


def test_verify_all_passes_when_all_match(vault_dir: Path) -> None:
    for name in ("a.gpg", "b.gpg"):
        f = vault_dir / name
        f.write_bytes(name.encode())
        record_checksum(vault_dir, f)
    assert verify_all(vault_dir) == []
