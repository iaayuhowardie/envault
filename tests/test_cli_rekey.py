"""Tests for envault.cli_rekey."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_rekey import build_rekey_parser, cmd_rekey
from envault.rekey import RekeyError


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    build_rekey_parser(sub)
    return root


def _args(vault_dir: Path, **kwargs) -> argparse.Namespace:  # type: ignore[type-arg]
    defaults = {
        "vault_dir": str(vault_dir),
        "recipients": None,
        "passphrase": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_rekey_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    ns = parser.parse_args(["rekey"])
    assert hasattr(ns, "func")


def test_cmd_rekey_success_no_new_recipients(vault_dir: Path, capsys) -> None:
    with patch("envault.cli_rekey.rekey") as mock_rekey:
        cmd_rekey(_args(vault_dir))
        mock_rekey.assert_called_once_with(
            vault_dir=vault_dir,
            new_recipients=None,
            passphrase=None,
        )
    out = capsys.readouterr().out
    assert "existing recipients" in out


def test_cmd_rekey_success_with_new_recipients(vault_dir: Path, capsys) -> None:
    fps = ["AABB", "CCDD"]
    with patch("envault.cli_rekey.rekey"):
        cmd_rekey(_args(vault_dir, recipients=fps))
    out = capsys.readouterr().out
    assert "2 recipient" in out


def test_cmd_rekey_raises_system_exit_on_error(vault_dir: Path) -> None:
    with patch("envault.cli_rekey.rekey", side_effect=RekeyError("boom")):
        with pytest.raises(SystemExit) as exc_info:
            cmd_rekey(_args(vault_dir))
        assert exc_info.value.code == 1


def test_cmd_rekey_error_message_to_stderr(vault_dir: Path, capsys) -> None:
    with patch("envault.cli_rekey.rekey", side_effect=RekeyError("kaboom")):
        with pytest.raises(SystemExit):
            cmd_rekey(_args(vault_dir))
    err = capsys.readouterr().err
    assert "kaboom" in err
