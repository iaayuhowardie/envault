"""Tests for envault/sign.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.sign import sign_file, verify_file, SignError


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    enc = tmp_path / "secrets.env.gpg"
    enc.write_bytes(b"encrypted-data")
    return tmp_path


# ---------------------------------------------------------------------------
# sign_file
# ---------------------------------------------------------------------------

def test_sign_file_returns_sig_path(tmp_vault: Path) -> None:
    enc = tmp_vault / "secrets.env.gpg"
    mock_result = MagicMock(returncode=0, stderr="")

    with patch("envault.sign._require_gpg", return_value="gpg"), \
         patch("envault.sign.subprocess.run", return_value=mock_result) as mock_run:
        sig = sign_file(enc, "DEADBEEF")

    assert sig == enc.with_suffix(".gpg.sig")
    args = mock_run.call_args[0][0]
    assert "--detach-sign" in args
    assert "--local-user" in args
    assert "DEADBEEF" in args


def test_sign_file_gpg_failure_raises(tmp_vault: Path) -> None:
    enc = tmp_vault / "secrets.env.gpg"
    mock_result = MagicMock(returncode=2, stderr="key not found")

    with patch("envault.sign._require_gpg", return_value="gpg"), \
         patch("envault.sign.subprocess.run", return_value=mock_result):
        with pytest.raises(SignError, match="key not found"):
            sign_file(enc, "DEADBEEF")


# ---------------------------------------------------------------------------
# verify_file
# ---------------------------------------------------------------------------

def test_verify_file_returns_fingerprint(tmp_vault: Path) -> None:
    enc = tmp_vault / "secrets.env.gpg"
    sig = enc.with_suffix(".gpg.sig")
    sig.write_bytes(b"sig-data")

    gpg_output = "[GNUPG:] VALIDSIG AABBCCDD1122334455667788 2024-01-01 ...\n"
    mock_result = MagicMock(returncode=0, stdout=gpg_output, stderr="")

    with patch("envault.sign._require_gpg", return_value="gpg"), \
         patch("envault.sign.subprocess.run", return_value=mock_result):
        fp = verify_file(enc)

    assert fp == "AABBCCDD1122334455667788"


def test_verify_file_missing_sig_raises(tmp_vault: Path) -> None:
    enc = tmp_vault / "secrets.env.gpg"

    with patch("envault.sign._require_gpg", return_value="gpg"):
        with pytest.raises(SignError, match="Signature file not found"):
            verify_file(enc)


def test_verify_file_bad_signature_raises(tmp_vault: Path) -> None:
    enc = tmp_vault / "secrets.env.gpg"
    sig = enc.with_suffix(".gpg.sig")
    sig.write_bytes(b"bad-sig")

    mock_result = MagicMock(returncode=1, stdout="", stderr="bad signature")

    with patch("envault.sign._require_gpg", return_value="gpg"), \
         patch("envault.sign.subprocess.run", return_value=mock_result):
        with pytest.raises(SignError, match="bad signature"):
            verify_file(enc)


def test_verify_file_custom_sig_path(tmp_vault: Path) -> None:
    enc = tmp_vault / "secrets.env.gpg"
    sig = tmp_vault / "custom.sig"
    sig.write_bytes(b"sig")

    gpg_output = "[GNUPG:] VALIDSIG FINGERPRINT123 2024-01-01\n"
    mock_result = MagicMock(returncode=0, stdout=gpg_output, stderr="")

    with patch("envault.sign._require_gpg", return_value="gpg"), \
         patch("envault.sign.subprocess.run", return_value=mock_result) as mock_run:
        fp = verify_file(enc, sig)

    assert fp == "FINGERPRINT123"
    args = mock_run.call_args[0][0]
    assert str(sig) in args
