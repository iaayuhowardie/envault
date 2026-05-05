"""Tests for envault.acl and envault.cli_acl."""

from __future__ import annotations

import argparse
import json
import pytest
from pathlib import Path

from envault.acl import (
    ACLError,
    get_role,
    list_acl,
    load_acl,
    remove_role,
    save_acl,
    set_role,
    _acl_path,
)
from envault.cli_acl import build_acl_parser, cmd_acl


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# acl.py unit tests
# ---------------------------------------------------------------------------

def test_load_acl_missing_returns_empty(vault_dir: Path) -> None:
    assert load_acl(vault_dir) == {}


def test_save_and_load_acl_roundtrip(vault_dir: Path) -> None:
    data = {"AAAA1111": "reader", "BBBB2222": "admin"}
    save_acl(vault_dir, data)
    assert load_acl(vault_dir) == data


def test_load_acl_corrupt_raises(vault_dir: Path) -> None:
    _acl_path(vault_dir).write_text("not json")
    with pytest.raises(ACLError, match="Corrupt"):
        load_acl(vault_dir)


def test_set_role_creates_entry(vault_dir: Path) -> None:
    set_role(vault_dir, "FP123", "writer")
    assert load_acl(vault_dir)["FP123"] == "writer"


def test_set_role_updates_existing(vault_dir: Path) -> None:
    set_role(vault_dir, "FP123", "reader")
    set_role(vault_dir, "FP123", "admin")
    assert load_acl(vault_dir)["FP123"] == "admin"


def test_set_role_invalid_role_raises(vault_dir: Path) -> None:
    with pytest.raises(ACLError, match="Invalid role"):
        set_role(vault_dir, "FP123", "superuser")


def test_set_role_empty_fingerprint_raises(vault_dir: Path) -> None:
    with pytest.raises(ACLError, match="empty"):
        set_role(vault_dir, "", "reader")


def test_remove_role_removes_entry(vault_dir: Path) -> None:
    set_role(vault_dir, "FP123", "reader")
    remove_role(vault_dir, "FP123")
    assert "FP123" not in load_acl(vault_dir)


def test_remove_role_missing_raises(vault_dir: Path) -> None:
    with pytest.raises(ACLError, match="not found"):
        remove_role(vault_dir, "GHOST")


def test_get_role_returns_role(vault_dir: Path) -> None:
    set_role(vault_dir, "FP123", "admin")
    assert get_role(vault_dir, "FP123") == "admin"


def test_get_role_missing_returns_none(vault_dir: Path) -> None:
    assert get_role(vault_dir, "NOBODY") is None


def test_list_acl_returns_entries(vault_dir: Path) -> None:
    set_role(vault_dir, "FP1", "reader")
    set_role(vault_dir, "FP2", "writer")
    entries = list_acl(vault_dir)
    fps = {e["fingerprint"] for e in entries}
    assert fps == {"FP1", "FP2"}


# ---------------------------------------------------------------------------
# cli_acl.py tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    build_acl_parser(p.add_subparsers(dest="cmd"))
    return p


def _args(parser: argparse.ArgumentParser, vault_dir: Path, *extra: str) -> argparse.Namespace:
    return parser.parse_args(["acl", "--vault-dir", str(vault_dir), *extra])


def test_build_acl_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    ns = parser.parse_args(["acl", "--vault-dir", ".", "list"])
    assert ns.cmd == "acl"


def test_cmd_acl_set(vault_dir: Path, parser: argparse.ArgumentParser) -> None:
    ns = _args(parser, vault_dir, "set", "ABCD1234", "reader")
    cmd_acl(ns)
    assert load_acl(vault_dir)["ABCD1234"] == "reader"


def test_cmd_acl_remove(vault_dir: Path, parser: argparse.ArgumentParser) -> None:
    set_role(vault_dir, "ABCD1234", "writer")
    ns = _args(parser, vault_dir, "remove", "ABCD1234")
    cmd_acl(ns)
    assert "ABCD1234" not in load_acl(vault_dir)


def test_cmd_acl_remove_missing_raises_system_exit(
    vault_dir: Path, parser: argparse.ArgumentParser
) -> None:
    ns = _args(parser, vault_dir, "remove", "GHOST")
    with pytest.raises(SystemExit):
        cmd_acl(ns)


def test_cmd_acl_list_empty(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture) -> None:
    ns = _args(parser, vault_dir, "list")
    cmd_acl(ns)
    assert "empty" in capsys.readouterr().out


def test_cmd_acl_get(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture) -> None:
    set_role(vault_dir, "FP99", "admin")
    ns = _args(parser, vault_dir, "get", "FP99")
    cmd_acl(ns)
    assert "admin" in capsys.readouterr().out
