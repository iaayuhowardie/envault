"""Tests for envault.vault module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.vault import (
    VaultError,
    add_recipient,
    load_meta,
    lock,
    remove_recipient,
    save_meta,
    unlock,
)


def test_load_meta_defaults(tmp_path):
    meta = load_meta(tmp_path)
    assert meta["recipients"] == []
    assert meta["env_file"] == ".env"
    assert meta["encrypted_file"] == ".env.gpg"


def test_save_and_load_meta_roundtrip(tmp_path):
    meta = {"recipients": ["DEADBEEF"], "env_file": ".env", "encrypted_file": ".env.gpg"}
    save_meta(meta, tmp_path)
    loaded = load_meta(tmp_path)
    assert loaded == meta
    assert (tmp_path / ".envault.json").exists()


def test_add_recipient(tmp_path):
    add_recipient("AAAA1111", tmp_path)
    meta = load_meta(tmp_path)
    assert "AAAA1111" in meta["recipients"]


def test_add_duplicate_recipient_raises(tmp_path):
    add_recipient("AAAA1111", tmp_path)
    with pytest.raises(VaultError, match="already in the vault"):
        add_recipient("AAAA1111", tmp_path)


def test_remove_recipient(tmp_path):
    add_recipient("BBBB2222", tmp_path)
    remove_recipient("BBBB2222", tmp_path)
    meta = load_meta(tmp_path)
    assert "BBBB2222" not in meta["recipients"]


def test_remove_missing_recipient_raises(tmp_path):
    with pytest.raises(VaultError, match="not found in the vault"):
        remove_recipient("NONEXISTENT", tmp_path)


def test_lock_calls_encrypt(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=hello\n")
    add_recipient("CCCC3333", tmp_path)

    with patch("envault.vault.encrypt_file") as mock_enc:
        result = lock(tmp_path)

    mock_enc.assert_called_once_with(
        str(env_file), ["CCCC3333"], str(tmp_path / ".env.gpg")
    )
    assert result == tmp_path / ".env.gpg"


def test_lock_missing_env_raises(tmp_path):
    add_recipient("DDDD4444", tmp_path)
    with pytest.raises(VaultError, match="does not exist"):
        lock(tmp_path)


def test_unlock_calls_decrypt(tmp_path):
    enc_file = tmp_path / ".env.gpg"
    enc_file.write_bytes(b"encrypted")

    with patch("envault.vault.decrypt_file") as mock_dec:
        result = unlock(tmp_path)

    mock_dec.assert_called_once_with(str(enc_file), str(tmp_path / ".env"))
    assert result == tmp_path / ".env"


def test_unlock_missing_encrypted_file_raises(tmp_path):
    with pytest.raises(VaultError, match="does not exist"):
        unlock(tmp_path)
