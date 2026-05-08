"""Tests for envault/cli_trust.py."""

from __future__ import annotations

import argparse
import pytest
from pathlib import Path

from envault.cli_trust import build_trust_parser, cmd_trust
from envault.trust import load_trust, set_trust


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    return tmp_path


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_trust_parser(sub)
    return p


def _args(parser: argparse.ArgumentParser, *argv: str) -> argparse.Namespace:
    return parser.parse_args(["trust", *argv])


def test_build_trust_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    args = _args(parser, "list")
    assert args.command == "trust"


def test_cmd_trust_set(vault_dir: Path, parser: argparse.ArgumentParser, capsys) -> None:
    args = _args(parser, "--vault-dir", str(vault_dir), "set", "AABBCC", "full")
    cmd_trust(args)
    out = capsys.readouterr().out
    assert "full" in out
    assert "AABBCC" in out


def test_cmd_trust_get(vault_dir: Path, parser: argparse.ArgumentParser, capsys) -> None:
    set_trust(vault_dir, "AABBCC", "marginal")
    args = _args(parser, "--vault-dir", str(vault_dir), "get", "AABBCC")
    cmd_trust(args)
    out = capsys.readouterr().out
    assert "marginal" in out


def test_cmd_trust_get_not_set(vault_dir: Path, parser: argparse.ArgumentParser, capsys) -> None:
    args = _args(parser, "--vault-dir", str(vault_dir), "get", "UNKNOWN")
    cmd_trust(args)
    out = capsys.readouterr().out
    assert "not set" in out


def test_cmd_trust_remove(vault_dir: Path, parser: argparse.ArgumentParser, capsys) -> None:
    set_trust(vault_dir, "AABBCC", "full")
    args = _args(parser, "--vault-dir", str(vault_dir), "remove", "AABBCC")
    cmd_trust(args)
    assert "AABBCC" not in load_trust(vault_dir)


def test_cmd_trust_remove_missing_raises(vault_dir: Path, parser: argparse.ArgumentParser) -> None:
    args = _args(parser, "--vault-dir", str(vault_dir), "remove", "NOTHERE")
    with pytest.raises(SystemExit, match="not found"):
        cmd_trust(args)


def test_cmd_trust_list(vault_dir: Path, parser: argparse.ArgumentParser, capsys) -> None:
    set_trust(vault_dir, "FP01", "full")
    set_trust(vault_dir, "FP02", "marginal")
    args = _args(parser, "--vault-dir", str(vault_dir), "list")
    cmd_trust(args)
    out = capsys.readouterr().out
    assert "FP01" in out
    assert "FP02" in out


def test_cmd_trust_list_empty(vault_dir: Path, parser: argparse.ArgumentParser, capsys) -> None:
    args = _args(parser, "--vault-dir", str(vault_dir), "list")
    cmd_trust(args)
    out = capsys.readouterr().out
    assert "No trust entries" in out
