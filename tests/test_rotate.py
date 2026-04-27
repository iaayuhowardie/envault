"""Tests for envault.rotate."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from envault.rotate import RotateError, rotate


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    """Return a vault directory pre-populated with meta and a dummy env.gpg."""
    meta_path = tmp_path / ".envault"
    meta_path.write_text(
        '{"recipients": ["AAAA1111", "BBBB2222"], "env_file": ".env"}'
    )
    (tmp_path / "env.gpg").write_bytes(b"encrypted-blob")
    return tmp_path


def test_rotate_no_recipients_raises(tmp_path: Path) -> None:
    meta_path = tmp_path / ".envault"
    meta_path.write_text('{"recipients": []}')
    (tmp_path / "env.gpg").write_bytes(b"data")

    with pytest.raises(RotateError, match="No recipients"):
        rotate(tmp_path, actor="AAAA1111")


def test_rotate_missing_encrypted_file_raises(tmp_path: Path) -> None:
    meta_path = tmp_path / ".envault"
    meta_path.write_text('{"recipients": ["AAAA1111"]}')
    # env.gpg intentionally absent

    with pytest.raises(RotateError, match="Encrypted file not found"):
        rotate(tmp_path, actor="AAAA1111")


def test_rotate_calls_decrypt_then_encrypt(vault_dir: Path) -> None:
    with (
        patch("envault.rotate.decrypt_file") as mock_decrypt,
        patch("envault.rotate.encrypt_file") as mock_encrypt,
        patch("envault.rotate.record") as mock_record,
        patch("shutil.move") as mock_move,
    ):
        rotate(vault_dir, added=["CCCC3333"], removed=[], actor="AAAA1111")

    assert mock_decrypt.call_count == 1
    assert mock_encrypt.call_count == 1

    # encrypt_file must be called with both existing recipients
    _, _, recipients_arg = mock_encrypt.call_args.args
    assert set(recipients_arg) == {"AAAA1111", "BBBB2222"}


def test_rotate_records_audit_entry(vault_dir: Path) -> None:
    with (
        patch("envault.rotate.decrypt_file"),
        patch("envault.rotate.encrypt_file"),
        patch("shutil.move"),
        patch("envault.rotate.record") as mock_record,
    ):
        rotate(
            vault_dir,
            added=["CCCC3333"],
            removed=["DDDD4444"],
            actor="AAAA1111",
        )

    mock_record.assert_called_once()
    _, kwargs = mock_record.call_args[0], mock_record.call_args[1]
    call_args = mock_record.call_args
    assert call_args.kwargs["action"] == "rotate" or call_args.args[1] == "rotate"


def test_rotate_saves_updated_meta(vault_dir: Path) -> None:
    with (
        patch("envault.rotate.decrypt_file"),
        patch("envault.rotate.encrypt_file"),
        patch("shutil.move"),
        patch("envault.rotate.record"),
        patch("envault.rotate.save_meta") as mock_save,
    ):
        rotate(vault_dir, actor="AAAA1111")

    mock_save.assert_called_once()
