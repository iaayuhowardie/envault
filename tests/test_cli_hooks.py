"""Tests for envault.cli_hooks."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_hooks import build_hooks_parser, cmd_hooks
from envault.hooks import load_hooks, set_hook


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_hooks_parser(sub)
    return root


def _args(parser, vault_dir, *argv):
    ns = parser.parse_args(["hooks", "--vault-dir", str(vault_dir), *argv])
    return ns


def test_build_hooks_parser_registers_command(parser):
    cmds = [a.dest for a in parser._subparsers._actions if hasattr(a, '_name_parser_map')]
    assert any(
        "hooks" in getattr(a, '_name_parser_map', {})
        for a in parser._subparsers._actions
    )


def test_cmd_hooks_set(vault_dir, parser, capsys):
    args = _args(parser, vault_dir, "set", "pre_lock", "echo hello")
    cmd_hooks(args)
    assert load_hooks(vault_dir).get("pre_lock") == "echo hello"
    out = capsys.readouterr().out
    assert "pre_lock" in out


def test_cmd_hooks_set_invalid_event_raises_system_exit(vault_dir, parser):
    args = _args(parser, vault_dir, "set", "bad_event", "echo x")
    with pytest.raises(SystemExit, match="Unknown event"):
        cmd_hooks(args)


def test_cmd_hooks_remove(vault_dir, parser, capsys):
    set_hook(vault_dir, "post_lock", "echo done")
    args = _args(parser, vault_dir, "remove", "post_lock")
    cmd_hooks(args)
    assert "post_lock" not in load_hooks(vault_dir)
    out = capsys.readouterr().out
    assert "removed" in out


def test_cmd_hooks_remove_missing_raises_system_exit(vault_dir, parser):
    args = _args(parser, vault_dir, "remove", "pre_lock")
    with pytest.raises(SystemExit, match="No hook registered"):
        cmd_hooks(args)


def test_cmd_hooks_list_empty(vault_dir, parser, capsys):
    args = _args(parser, vault_dir, "list")
    cmd_hooks(args)
    out = capsys.readouterr().out
    assert "No hooks" in out


def test_cmd_hooks_list_shows_hooks(vault_dir, parser, capsys):
    set_hook(vault_dir, "pre_unlock", "./pre.sh")
    args = _args(parser, vault_dir, "list")
    cmd_hooks(args)
    out = capsys.readouterr().out
    assert "pre_unlock" in out
    assert "./pre.sh" in out
