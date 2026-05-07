"""Tests for envault.cli_session."""

from __future__ import annotations

import argparse
import pytest
from pathlib import Path
from unittest.mock import patch

from envault.cli_session import cmd_session, build_session_parser
from envault.session import open_session


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    return tmp_path


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_session_parser(sub)
    return root


def _args(parser, vault_dir, *argv):
    ns = parser.parse_args(["session"] + list(argv))
    ns.vault_dir = str(vault_dir)
    return ns


def test_build_session_parser_registers_command(parser):
    ns = parser.parse_args(["session", "status"])
    assert ns.command == "session"


def test_cmd_session_start(vault_dir, parser, capsys):
    ns = _args(parser, vault_dir, "start", "ABCDEF01")
    cmd_session(ns)
    out = capsys.readouterr().out
    assert "ABCDEF01" in out
    assert "Session started" in out


def test_cmd_session_stop(vault_dir, parser, capsys):
    open_session(vault_dir, "ABCDEF01", ttl_seconds=60)
    ns = _args(parser, vault_dir, "stop")
    cmd_session(ns)
    out = capsys.readouterr().out
    assert "closed" in out.lower()


def test_cmd_session_status_active(vault_dir, parser, capsys):
    open_session(vault_dir, "ABCDEF01", ttl_seconds=3600)
    ns = _args(parser, vault_dir, "status")
    cmd_session(ns)
    out = capsys.readouterr().out
    assert "ABCDEF01" in out


def test_cmd_session_status_inactive(vault_dir, parser, capsys):
    ns = _args(parser, vault_dir, "status")
    cmd_session(ns)
    out = capsys.readouterr().out
    assert "No active session" in out


def test_cmd_session_start_empty_fingerprint_raises(vault_dir, parser):
    ns = _args(parser, vault_dir, "start", "")
    with pytest.raises(SystemExit, match="fingerprint"):
        cmd_session(ns)
