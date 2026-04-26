"""Tests for envault.crypto GPG utilities."""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.crypto import (
    GPGError,
    _require_gpg,
    list_keys,
    encrypt_file,
    decrypt_file,
)


def test_require_gpg_found():
    with patch("shutil.which", return_value="/usr/bin/gpg"):
        assert _require_gpg() == "/usr/bin/gpg"


def test_require_gpg_not_found():
    with patch("shutil.which", return_value=None):
        with pytest.raises(GPGError, match="GPG is not installed"):
            _require_gpg()


def test_list_keys_parses_output():
    sample_output = (
        "pub::-:4096:1:ABCDEF123456:2023:::-:::scESC:\n"
        "fpr:::::::::ABCDEF1234567890ABCDEF1234567890ABCDEF12:\n"
        "uid:-::::2023::HASH::Alice <alice@example.com>:::::::::0:\n"
    )
    mock_result = MagicMock(stdout=sample_output)
    with patch("shutil.which", return_value="/usr/bin/gpg"), \
         patch("subprocess.run", return_value=mock_result):
        keys = list_keys()
    assert len(keys) == 1
    assert keys[0]["fingerprint"] == "ABCDEF1234567890ABCDEF1234567890ABCDEF12"
    assert "Alice <alice@example.com>" in keys[0]["uids"]


def test_encrypt_file_no_recipients(tmp_path):
    src = tmp_path / ".env"
    src.write_text("SECRET=hello")
    with pytest.raises(GPGError, match="At least one recipient"):
        encrypt_file(src, tmp_path / ".env.gpg", [])


def test_encrypt_file_gpg_failure(tmp_path):
    src = tmp_path / ".env"
    src.write_text("SECRET=hello")
    mock_result = MagicMock(returncode=1, stderr="no such key")
    with patch("shutil.which", return_value="/usr/bin/gpg"), \
         patch("subprocess.run", return_value=mock_result):
        with pytest.raises(GPGError, match="Encryption failed"):
            encrypt_file(src, tmp_path / ".env.gpg", ["DEADBEEF"])


def test_decrypt_file_gpg_failure(tmp_path):
    enc = tmp_path / ".env.gpg"
    enc.write_bytes(b"fake encrypted data")
    mock_result = MagicMock(returncode=2, stderr="decryption failed")
    with patch("shutil.which", return_value="/usr/bin/gpg"), \
         patch("subprocess.run", return_value=mock_result):
        with pytest.raises(GPGError, match="Decryption failed"):
            decrypt_file(enc, tmp_path / ".env")


def test_decrypt_file_success(tmp_path):
    enc = tmp_path / ".env.gpg"
    enc.write_bytes(b"fake")
    mock_result = MagicMock(returncode=0, stderr="")
    with patch("shutil.which", return_value="/usr/bin/gpg"), \
         patch("subprocess.run", return_value=mock_result):
        decrypt_file(enc, tmp_path / ".env")  # should not raise
