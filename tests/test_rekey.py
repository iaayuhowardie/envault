"""Tests for envault.rekey."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from envault.rekey import (
    RekeyError,
    clear_rekey_state,
    load_rekey_state,
    rekey,
    save_rekey_state,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    meta_dir = tmp_path / ".envault"
    meta_dir.mkdir()
    meta = '{"recipients": ["AABBCCDD"], "encrypted_file": ".env.gpg"}'
    (meta_dir / "meta.json").write_text(meta)
    (tmp_path / ".env.gpg").write_bytes(b"encrypted")
    return tmp_path


def test_load_rekey_state_missing_returns_empty(vault_dir: Path) -> None:
    assert load_rekey_state(vault_dir) == {}


def test_save_and_load_rekey_state_roundtrip(vault_dir: Path) -> None:
    state = {"status": "in_progress", "step": 1}
    save_rekey_state(vault_dir, state)
    loaded = load_rekey_state(vault_dir)
    assert loaded == state


def test_clear_rekey_state_removes_file(vault_dir: Path) -> None:
    save_rekey_state(vault_dir, {"x": 1})
    clear_rekey_state(vault_dir)
    assert not (vault_dir / ".envault" / ".rekey_state.json").exists()


def test_clear_rekey_state_noop_when_missing(vault_dir: Path) -> None:
    clear_rekey_state(vault_dir)  # should not raise


def test_rekey_no_recipients_raises(tmp_path: Path) -> None:
    meta_dir = tmp_path / ".envault"
    meta_dir.mkdir()
    (meta_dir / "meta.json").write_text('{"recipients": [], "encrypted_file": ".env.gpg"}')
    (tmp_path / ".env.gpg").write_bytes(b"data")
    with pytest.raises(RekeyError, match="No recipients"):
        rekey(tmp_path)


def test_rekey_missing_encrypted_file_raises(vault_dir: Path) -> None:
    (vault_dir / ".env.gpg").unlink()
    with pytest.raises(RekeyError, match="Encrypted file not found"):
        rekey(vault_dir)


def test_rekey_calls_decrypt_then_encrypt(vault_dir: Path) -> None:
    with (
        patch("envault.rekey.decrypt_file") as mock_dec,
        patch("envault.rekey.encrypt_file") as mock_enc,
        patch("envault.rekey.audit_record"),
    ):
        rekey(vault_dir)
        assert mock_dec.call_count == 1
        assert mock_enc.call_count == 1


def test_rekey_with_new_recipients_updates_meta(vault_dir: Path) -> None:
    new_fp = ["DEADBEEF", "CAFEBABE"]
    with (
        patch("envault.rekey.decrypt_file"),
        patch("envault.rekey.encrypt_file"),
        patch("envault.rekey.audit_record"),
        patch("envault.rekey.save_meta") as mock_save,
    ):
        rekey(vault_dir, new_recipients=new_fp)
        mock_save.assert_called_once()
        saved_meta = mock_save.call_args[0][1]
        assert saved_meta["recipients"] == new_fp


def test_rekey_cleans_tmp_file_on_gpg_error(vault_dir: Path) -> None:
    from envault.crypto import GPGError

    with (
        patch("envault.rekey.decrypt_file", side_effect=GPGError("bad")),
        patch("envault.rekey.encrypt_file"),
    ):
        with pytest.raises(RekeyError):
            rekey(vault_dir)
        tmp = vault_dir / ".env.rekey_tmp"
        assert not tmp.exists()
