"""Tests for envault.pin."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.pin import (
    PIN_FILENAME,
    PinError,
    check_pin,
    load_pin,
    remove_pin,
    save_pin,
    set_pin,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def enc_file(vault_dir: Path) -> Path:
    f = vault_dir / ".env.gpg"
    f.write_bytes(b"encrypted-content-v1")
    return f


def test_load_pin_missing_returns_empty(vault_dir: Path) -> None:
    assert load_pin(vault_dir) == {}


def test_save_and_load_pin_roundtrip(vault_dir: Path) -> None:
    record = {"some/path": "abc123"}
    save_pin(vault_dir, record)
    assert load_pin(vault_dir) == record


def test_load_pin_corrupt_raises(vault_dir: Path) -> None:
    (vault_dir / PIN_FILENAME).write_text("not json!!!")
    with pytest.raises(PinError, match="Corrupt pin file"):
        load_pin(vault_dir)


def test_set_pin_returns_hex_digest(vault_dir: Path, enc_file: Path) -> None:
    digest = set_pin(vault_dir, enc_file)
    assert len(digest) == 64  # sha256 hex
    assert all(c in "0123456789abcdef" for c in digest)


def test_set_pin_persists_record(vault_dir: Path, enc_file: Path) -> None:
    digest = set_pin(vault_dir, enc_file)
    record = load_pin(vault_dir)
    assert str(enc_file.resolve()) in record
    assert record[str(enc_file.resolve())] == digest


def test_set_pin_missing_file_raises(vault_dir: Path) -> None:
    missing = vault_dir / "ghost.gpg"
    with pytest.raises(PinError, match="Encrypted file not found"):
        set_pin(vault_dir, missing)


def test_check_pin_matches_unchanged_file(vault_dir: Path, enc_file: Path) -> None:
    set_pin(vault_dir, enc_file)
    assert check_pin(vault_dir, enc_file) is True


def test_check_pin_detects_tampered_file(vault_dir: Path, enc_file: Path) -> None:
    set_pin(vault_dir, enc_file)
    enc_file.write_bytes(b"tampered-content!")
    assert check_pin(vault_dir, enc_file) is False


def test_check_pin_no_pin_recorded_returns_true(vault_dir: Path, enc_file: Path) -> None:
    # No set_pin called — should pass silently
    assert check_pin(vault_dir, enc_file) is True


def test_remove_pin_clears_entry(vault_dir: Path, enc_file: Path) -> None:
    set_pin(vault_dir, enc_file)
    remove_pin(vault_dir, enc_file)
    assert load_pin(vault_dir) == {}


def test_remove_pin_all_clears_everything(vault_dir: Path, enc_file: Path) -> None:
    set_pin(vault_dir, enc_file)
    remove_pin(vault_dir)  # no file arg → wipe all
    assert load_pin(vault_dir) == {}


def test_remove_pin_missing_raises(vault_dir: Path, enc_file: Path) -> None:
    with pytest.raises(PinError, match="No pin found for"):
        remove_pin(vault_dir, enc_file)
