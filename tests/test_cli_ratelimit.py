"""Tests for envault.cli_ratelimit."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.cli_ratelimit import build_ratelimit_parser, cmd_ratelimit
from envault.ratelimit import load_ratelimit


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_ratelimit_parser(sub)
    return p


def _args(parser: argparse.ArgumentParser, vault_dir: Path, *argv: str) -> argparse.Namespace:
    ns = parser.parse_args(["ratelimit", *argv])
    ns.vault_dir = str(vault_dir)
    return ns


def test_build_ratelimit_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    ns = parser.parse_args(["ratelimit", "show"])
    assert ns.command == "ratelimit"


def test_cmd_ratelimit_set(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture) -> None:
    ns = _args(parser, vault_dir, "set", "--max-attempts", "4", "--window", "90")
    cmd_ratelimit(ns)
    out = capsys.readouterr().out
    assert "4" in out and "90" in out
    state = load_ratelimit(vault_dir)
    assert state["max_attempts"] == 4
    assert state["window"] == 90


def test_cmd_ratelimit_show(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture) -> None:
    ns = _args(parser, vault_dir, "show")
    cmd_ratelimit(ns)
    out = capsys.readouterr().out
    assert "max_attempts" in out
    assert "window" in out
    assert "recent_hits" in out


def test_cmd_ratelimit_reset(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture) -> None:
    from envault.ratelimit import record_attempt
    record_attempt(vault_dir)
    ns = _args(parser, vault_dir, "reset")
    cmd_ratelimit(ns)
    out = capsys.readouterr().out
    assert "reset" in out.lower()
    state = load_ratelimit(vault_dir)
    assert state["attempts"] == []


def test_cmd_ratelimit_set_invalid_raises(vault_dir: Path, parser: argparse.ArgumentParser) -> None:
    ns = _args(parser, vault_dir, "set", "--max-attempts", "0")
    with pytest.raises(SystemExit, match="max_attempts"):
        cmd_ratelimit(ns)


def test_cmd_ratelimit_set_invalid_window_raises(vault_dir: Path, parser: argparse.ArgumentParser) -> None:
    """Ensure that a non-positive window value is rejected with a SystemExit."""
    ns = _args(parser, vault_dir, "set", "--window", "0")
    with pytest.raises(SystemExit, match="window"):
        cmd_ratelimit(ns)
