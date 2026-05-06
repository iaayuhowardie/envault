"""Tests for envault.cli_ttl module."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.cli_ttl import build_ttl_parser, cmd_ttl
from envault.ttl import load_ttl, save_ttl, set_ttl


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_ttl_parser(sub)
    return p


def _args(parser: argparse.ArgumentParser, *argv: str) -> argparse.Namespace:
    return parser.parse_args(["ttl", *argv])


def test_build_ttl_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    ns = _args(parser, "--vault-dir", ".", "status")
    assert ns.command == "ttl"
    assert ns.ttl_command == "status"


def test_cmd_ttl_set(vault_dir: Path, capsys: pytest.CaptureFixture) -> None:
    ns = argparse.Namespace(vault_dir=str(vault_dir), ttl_command="set", seconds=300)
    cmd_ttl(ns)
    data = load_ttl(vault_dir)
    assert data["ttl_seconds"] == 300
    captured = capsys.readouterr()
    assert "300" in captured.out


def test_cmd_ttl_set_invalid_raises(vault_dir: Path) -> None:
    ns = argparse.Namespace(vault_dir=str(vault_dir), ttl_command="set", seconds=-5)
    with pytest.raises(SystemExit, match="positive"):
        cmd_ttl(ns)


def test_cmd_ttl_status_no_ttl(vault_dir: Path, capsys: pytest.CaptureFixture) -> None:
    ns = argparse.Namespace(vault_dir=str(vault_dir), ttl_command="status")
    cmd_ttl(ns)
    assert "No TTL" in capsys.readouterr().out


def test_cmd_ttl_status_active(vault_dir: Path, capsys: pytest.CaptureFixture) -> None:
    set_ttl(vault_dir, 9999)
    ns = argparse.Namespace(vault_dir=str(vault_dir), ttl_command="status")
    cmd_ttl(ns)
    out = capsys.readouterr().out
    assert "active" in out
    assert "Expires at" in out


def test_cmd_ttl_status_expired(vault_dir: Path, capsys: pytest.CaptureFixture) -> None:
    set_ttl(vault_dir, 1)
    data = load_ttl(vault_dir)
    past = datetime.now(timezone.utc) - timedelta(seconds=200)
    data["set_at"] = past.isoformat()
    save_ttl(vault_dir, data)
    ns = argparse.Namespace(vault_dir=str(vault_dir), ttl_command="status")
    cmd_ttl(ns)
    assert "EXPIRED" in capsys.readouterr().out


def test_cmd_ttl_clear(vault_dir: Path, capsys: pytest.CaptureFixture) -> None:
    set_ttl(vault_dir, 60)
    ns = argparse.Namespace(vault_dir=str(vault_dir), ttl_command="clear")
    cmd_ttl(ns)
    data = load_ttl(vault_dir)
    assert "ttl_seconds" not in data
    assert "cleared" in capsys.readouterr().out


def test_cmd_ttl_unknown_command_raises(vault_dir: Path) -> None:
    ns = argparse.Namespace(vault_dir=str(vault_dir), ttl_command="bogus")
    with pytest.raises(SystemExit, match="Unknown"):
        cmd_ttl(ns)
