"""Tests for envault/cli_sign.py."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_sign import cmd_sign, cmd_verify, build_sign_parser
from envault.sign import SignError


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    enc = tmp_path / "secrets.env.gpg"
    enc.write_bytes(b"data")
    return tmp_path


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    build_sign_parser(p.add_subparsers())
    return p


def _args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_build_sign_parser_registers_commands(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["sign", "file.gpg", "--fingerprint", "ABCD"])
    assert args.func is cmd_sign
    assert args.fingerprint == "ABCD"

    args2 = parser.parse_args(["verify", "file.gpg"])
    assert args2.func is cmd_verify


def test_cmd_sign_prints_sig_path(vault_dir: Path, capsys) -> None:
    enc = vault_dir / "secrets.env.gpg"
    sig = enc.with_suffix(".gpg.sig")

    with patch("envault.cli_sign.sign_file", return_value=sig) as mock_sign:
        cmd_sign(_args(file=str(enc), fingerprint="ABCD1234"))

    mock_sign.assert_called_once_with(enc, "ABCD1234")
    out = capsys.readouterr().out
    assert "secrets.env.gpg.sig" in out


def test_cmd_sign_missing_file_raises_system_exit(vault_dir: Path) -> None:
    with pytest.raises(SystemExit, match="file not found"):
        cmd_sign(_args(file=str(vault_dir / "missing.gpg"), fingerprint="ABCD"))


def test_cmd_sign_sign_error_raises_system_exit(vault_dir: Path) -> None:
    enc = vault_dir / "secrets.env.gpg"

    with patch("envault.cli_sign.sign_file", side_effect=SignError("gpg died")):
        with pytest.raises(SystemExit, match="gpg died"):
            cmd_sign(_args(file=str(enc), fingerprint="ABCD"))


def test_cmd_verify_prints_fingerprint(vault_dir: Path, capsys) -> None:
    enc = vault_dir / "secrets.env.gpg"

    with patch("envault.cli_sign.verify_file", return_value="FINGERPRINT99"):
        cmd_verify(_args(file=str(enc), sig=None))

    out = capsys.readouterr().out
    assert "FINGERPRINT99" in out


def test_cmd_verify_sign_error_raises_system_exit(vault_dir: Path) -> None:
    enc = vault_dir / "secrets.env.gpg"

    with patch("envault.cli_sign.verify_file", side_effect=SignError("bad sig")):
        with pytest.raises(SystemExit, match="bad sig"):
            cmd_verify(_args(file=str(enc), sig=None))
