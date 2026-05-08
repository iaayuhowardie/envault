"""Tests for envault.changelog and envault.cli_changelog."""

from __future__ import annotations

import argparse
import json
import pytest
from pathlib import Path

from envault.changelog import (
    ChangelogError,
    _changelog_path,
    format_changelog,
    load_changelog,
    record_change,
)
from envault.cli_changelog import build_changelog_parser, cmd_changelog


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    return tmp_path


# --- load_changelog ---

def test_load_changelog_missing_returns_empty(vault_dir: Path) -> None:
    assert load_changelog(vault_dir) == []


def test_load_changelog_corrupt_raises(vault_dir: Path) -> None:
    _changelog_path(vault_dir).write_text("not json")
    with pytest.raises(ChangelogError, match="Corrupt"):
        load_changelog(vault_dir)


def test_load_changelog_wrong_type_raises(vault_dir: Path) -> None:
    _changelog_path(vault_dir).write_text(json.dumps({"bad": "type"}))
    with pytest.raises(ChangelogError, match="array"):
        load_changelog(vault_dir)


# --- record_change ---

def test_record_change_creates_file(vault_dir: Path) -> None:
    record_change(vault_dir, action="lock", fingerprint="ABCD1234")
    assert _changelog_path(vault_dir).exists()


def test_record_change_entry_fields(vault_dir: Path) -> None:
    entry = record_change(vault_dir, action="rotate", fingerprint="DEADBEEF", detail="re-keyed")
    assert entry["action"] == "rotate"
    assert entry["fingerprint"] == "DEADBEEF"
    assert entry["detail"] == "re-keyed"
    assert "timestamp" in entry


def test_record_change_appends(vault_dir: Path) -> None:
    record_change(vault_dir, action="lock", fingerprint="AAA")
    record_change(vault_dir, action="unlock", fingerprint="BBB")
    entries = load_changelog(vault_dir)
    assert len(entries) == 2
    assert entries[0]["action"] == "lock"
    assert entries[1]["action"] == "unlock"


def test_record_change_empty_action_raises(vault_dir: Path) -> None:
    with pytest.raises(ChangelogError, match="action"):
        record_change(vault_dir, action="", fingerprint="AAA")


def test_record_change_empty_fingerprint_raises(vault_dir: Path) -> None:
    with pytest.raises(ChangelogError, match="fingerprint"):
        record_change(vault_dir, action="lock", fingerprint="")


# --- format_changelog ---

def test_format_changelog_empty() -> None:
    assert format_changelog([]) == "(no changelog entries)"


def test_format_changelog_includes_fields(vault_dir: Path) -> None:
    entry = record_change(vault_dir, action="lock", fingerprint="FP1", detail="nightly")
    output = format_changelog([entry])
    assert "lock" in output
    assert "FP1" in output
    assert "nightly" in output


# --- CLI ---

@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_changelog_parser(sub)
    return p


def test_build_changelog_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["changelog", "--vault-dir", ".", "show"])
    assert args.changelog_cmd == "show"


def test_cmd_changelog_show(vault_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    record_change(vault_dir, action="lock", fingerprint="FP99")
    args = argparse.Namespace(vault_dir=str(vault_dir), changelog_cmd="show")
    cmd_changelog(args)
    out = capsys.readouterr().out
    assert "lock" in out
    assert "FP99" in out


def test_cmd_changelog_record(vault_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(
        vault_dir=str(vault_dir),
        changelog_cmd="record",
        action="rotate",
        fingerprint="CAFEBABE",
        detail="manual",
    )
    cmd_changelog(args)
    entries = load_changelog(vault_dir)
    assert len(entries) == 1
    assert entries[0]["fingerprint"] == "CAFEBABE"
