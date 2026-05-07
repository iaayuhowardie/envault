"""Tests for envault.whitelist and envault.cli_whitelist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envault.whitelist import (
    WhitelistError,
    allow,
    deny,
    is_allowed,
    load_whitelist,
    save_whitelist,
)
from envault.cli_whitelist import build_whitelist_parser, cmd_whitelist


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    return tmp_path


# --- whitelist module ---

def test_load_whitelist_missing_returns_empty(vault_dir):
    assert load_whitelist(vault_dir) == []


def test_save_and_load_whitelist_roundtrip(vault_dir):
    fps = ["AABBCCDD", "11223344"]
    save_whitelist(vault_dir, fps)
    assert load_whitelist(vault_dir) == fps


def test_load_whitelist_corrupt_raises(vault_dir):
    path = vault_dir / ".envault" / "whitelist.json"
    path.write_text("not json{")
    with pytest.raises(WhitelistError, match="Corrupt"):
        load_whitelist(vault_dir)


def test_load_whitelist_wrong_type_raises(vault_dir):
    path = vault_dir / ".envault" / "whitelist.json"
    path.write_text(json.dumps({"key": "value"}))
    with pytest.raises(WhitelistError, match="JSON array"):
        load_whitelist(vault_dir)


def test_allow_adds_fingerprint(vault_dir):
    entries = allow(vault_dir, "aabbccdd")
    assert "AABBCCDD" in entries


def test_allow_duplicate_raises(vault_dir):
    allow(vault_dir, "AABBCCDD")
    with pytest.raises(WhitelistError, match="already whitelisted"):
        allow(vault_dir, "aabbccdd")


def test_allow_empty_fingerprint_raises(vault_dir):
    with pytest.raises(WhitelistError, match="empty"):
        allow(vault_dir, "   ")


def test_deny_removes_fingerprint(vault_dir):
    allow(vault_dir, "AABBCCDD")
    entries = deny(vault_dir, "AABBCCDD")
    assert "AABBCCDD" not in entries


def test_deny_missing_fingerprint_raises(vault_dir):
    with pytest.raises(WhitelistError, match="not in whitelist"):
        deny(vault_dir, "DEADBEEF")


def test_is_allowed_empty_whitelist_returns_true(vault_dir):
    assert is_allowed(vault_dir, "ANYTHING") is True


def test_is_allowed_present_returns_true(vault_dir):
    allow(vault_dir, "AABBCCDD")
    assert is_allowed(vault_dir, "aabbccdd") is True


def test_is_allowed_absent_returns_false(vault_dir):
    allow(vault_dir, "AABBCCDD")
    assert is_allowed(vault_dir, "DEADBEEF") is False


# --- CLI ---

@pytest.fixture()
def parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_whitelist_parser(sub)
    return root


def _args(parser, vault_dir, *extra):
    return parser.parse_args(["whitelist", "--vault-dir", str(vault_dir), *extra])


def test_build_whitelist_parser_registers_command(parser):
    ns = parser.parse_args(["whitelist", "--vault-dir", ".", "list"])
    assert ns.command == "whitelist"


def test_cmd_whitelist_add(vault_dir, parser, capsys):
    ns = _args(parser, vault_dir, "add", "AABBCCDD")
    cmd_whitelist(ns)
    out = capsys.readouterr().out
    assert "AABBCCDD" in out


def test_cmd_whitelist_list_empty(vault_dir, parser, capsys):
    ns = _args(parser, vault_dir, "list")
    cmd_whitelist(ns)
    out = capsys.readouterr().out
    assert "empty" in out


def test_cmd_whitelist_check_allowed(vault_dir, parser, capsys):
    allow(vault_dir, "AABBCCDD")
    ns = _args(parser, vault_dir, "check", "AABBCCDD")
    cmd_whitelist(ns)
    assert "ALLOWED" in capsys.readouterr().out


def test_cmd_whitelist_remove_raises_on_missing(vault_dir, parser):
    ns = _args(parser, vault_dir, "remove", "DEADBEEF")
    with pytest.raises(SystemExit, match="not in whitelist"):
        cmd_whitelist(ns)
