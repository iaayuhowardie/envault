"""Tests for envault.tags and envault.cli_tags."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.tags import (
    TagError,
    add_tag,
    list_tags,
    load_tags,
    remove_tag,
    save_tags,
)
from envault.cli_tags import build_tags_parser, cmd_tags


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# tags.py unit tests
# ---------------------------------------------------------------------------

def test_load_tags_missing_returns_empty(vault_dir: Path) -> None:
    assert load_tags(vault_dir) == []


def test_save_and_load_tags_roundtrip(vault_dir: Path) -> None:
    save_tags(vault_dir, ["production", "staging"])
    assert load_tags(vault_dir) == ["production", "staging"]


def test_add_tag_stores_tag(vault_dir: Path) -> None:
    tags = add_tag(vault_dir, "production")
    assert "production" in tags
    assert load_tags(vault_dir) == ["production"]


def test_add_duplicate_tag_raises(vault_dir: Path) -> None:
    add_tag(vault_dir, "production")
    with pytest.raises(TagError, match="already exists"):
        add_tag(vault_dir, "production")


def test_add_empty_tag_raises(vault_dir: Path) -> None:
    with pytest.raises(TagError, match="must not be empty"):
        add_tag(vault_dir, "   ")


def test_remove_tag_removes_it(vault_dir: Path) -> None:
    add_tag(vault_dir, "staging")
    tags = remove_tag(vault_dir, "staging")
    assert "staging" not in tags


def test_remove_nonexistent_tag_raises(vault_dir: Path) -> None:
    with pytest.raises(TagError, match="not found"):
        remove_tag(vault_dir, "ghost")


def test_list_tags_returns_sorted(vault_dir: Path) -> None:
    save_tags(vault_dir, ["staging", "production", "dev"])
    assert list_tags(vault_dir) == ["dev", "production", "staging"]


# ---------------------------------------------------------------------------
# cli_tags.py tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    subs = root.add_subparsers(dest="command")
    build_tags_parser(subs)
    return root


def test_build_tags_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["tags", "list"])
    assert args.command == "tags"
    assert args.tag_action == "list"


def test_cmd_tags_add(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture) -> None:
    args = parser.parse_args(["tags", "add", "production"])
    args.vault_dir = str(vault_dir)
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "production" in out


def test_cmd_tags_list(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture) -> None:
    add_tag(vault_dir, "staging")
    args = parser.parse_args(["tags", "list"])
    args.vault_dir = str(vault_dir)
    cmd_tags(args)
    assert "staging" in capsys.readouterr().out


def test_cmd_tags_remove(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture) -> None:
    add_tag(vault_dir, "staging")
    args = parser.parse_args(["tags", "remove", "staging"])
    args.vault_dir = str(vault_dir)
    cmd_tags(args)
    assert "staging" in capsys.readouterr().out
    assert "staging" not in load_tags(vault_dir)


def test_cmd_tags_error_exits(vault_dir: Path, parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["tags", "remove", "nonexistent"])
    args.vault_dir = str(vault_dir)
    with pytest.raises(SystemExit) as exc_info:
        cmd_tags(args)
    assert exc_info.value.code == 1
