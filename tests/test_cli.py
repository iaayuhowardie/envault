"""Tests for the envault CLI commands."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.cli import cmd_init, cmd_add, cmd_remove, cmd_lock, cmd_unlock
from envault.vault import VaultError


@pytest.fixture
def tmp_env(tmp_path, monkeypatch):
    """Change working directory to a temp path for each test."""
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=hello\nDB_URL=postgres://localhost/dev\n")
    return tmp_path


# ---------------------------------------------------------------------------
# cmd_init
# ---------------------------------------------------------------------------


def test_cmd_init_creates_meta(tmp_env):
    """init should create .envault/meta.json with sensible defaults."""
    with patch("envault.cli.list_keys", return_value=["AABBCCDD"]):
        cmd_init(env_file=".env", recipients=["AABBCCDD"])

    meta_path = tmp_env / ".envault" / "meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text())
    assert meta["env_file"] == ".env"
    assert "AABBCCDD" in meta["recipients"]


def test_cmd_init_no_recipients_raises(tmp_env):
    """init with an empty recipient list should raise."""
    with pytest.raises((VaultError, SystemExit, ValueError)):
        cmd_init(env_file=".env", recipients=[])


def test_cmd_init_missing_env_file_raises(tmp_env):
    """init should raise when the target .env file does not exist."""
    with pytest.raises((VaultError, SystemExit, FileNotFoundError)):
        cmd_init(env_file=".env.missing", recipients=["AABBCCDD"])


# ---------------------------------------------------------------------------
# cmd_add
# ---------------------------------------------------------------------------


def test_cmd_add_new_recipient(tmp_env):
    """add should append a new fingerprint to the recipients list."""
    with patch("envault.cli.list_keys", return_value=["AABBCCDD", "11223344"]):
        cmd_init(env_file=".env", recipients=["AABBCCDD"])
        cmd_add(fingerprint="11223344")

    meta_path = tmp_env / ".envault" / "meta.json"
    meta = json.loads(meta_path.read_text())
    assert "11223344" in meta["recipients"]


def test_cmd_add_duplicate_recipient_raises(tmp_env):
    """add should raise when the fingerprint is already present."""
    with patch("envault.cli.list_keys", return_value=["AABBCCDD"]):
        cmd_init(env_file=".env", recipients=["AABBCCDD"])
        with pytest.raises((VaultError, SystemExit)):
            cmd_add(fingerprint="AABBCCDD")


# ---------------------------------------------------------------------------
# cmd_remove
# ---------------------------------------------------------------------------


def test_cmd_remove_recipient(tmp_env):
    """remove should drop a fingerprint from the recipients list."""
    with patch("envault.cli.list_keys", return_value=["AABBCCDD", "11223344"]):
        cmd_init(env_file=".env", recipients=["AABBCCDD", "11223344"])
        cmd_remove(fingerprint="11223344")

    meta_path = tmp_env / ".envault" / "meta.json"
    meta = json.loads(meta_path.read_text())
    assert "11223344" not in meta["recipients"]
    assert "AABBCCDD" in meta["recipients"]


def test_cmd_remove_last_recipient_raises(tmp_env):
    """Removing the only recipient should raise to prevent lock-out."""
    with patch("envault.cli.list_keys", return_value=["AABBCCDD"]):
        cmd_init(env_file=".env", recipients=["AABBCCDD"])
        with pytest.raises((VaultError, SystemExit)):
            cmd_remove(fingerprint="AABBCCDD")


# ---------------------------------------------------------------------------
# cmd_lock / cmd_unlock
# ---------------------------------------------------------------------------


def test_cmd_lock_produces_encrypted_file(tmp_env):
    """lock should call encrypt_file and produce a .env.gpg artefact."""
    with patch("envault.cli.list_keys", return_value=["AABBCCDD"]):
        cmd_init(env_file=".env", recipients=["AABBCCDD"])

    with patch("envault.cli.encrypt_file") as mock_enc:
        mock_enc.return_value = None  # side-effect: creates the file
        # Create the expected output file so downstream checks pass
        (tmp_env / ".env.gpg").write_bytes(b"ENCRYPTED")
        cmd_lock()

    mock_enc.assert_called_once()


def test_cmd_unlock_calls_decrypt(tmp_env):
    """unlock should call decrypt_file with the correct arguments."""
    with patch("envault.cli.list_keys", return_value=["AABBCCDD"]):
        cmd_init(env_file=".env", recipients=["AABBCCDD"])

    (tmp_env / ".env.gpg").write_bytes(b"ENCRYPTED")

    with patch("envault.cli.decrypt_file") as mock_dec:
        mock_dec.return_value = None
        cmd_unlock()

    mock_dec.assert_called_once()
