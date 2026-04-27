"""Tests for envault.cli_export sub-commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envault.cli_export import build_export_parser, cmd_export


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("API_KEY=abc123\nDEBUG=false\n", encoding="utf-8")
    return p


@pytest.fixture
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    build_export_parser(sub)
    return root


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"format": "dotenv", "output": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_export_stdout_dotenv(env_file: Path, capsys) -> None:
    args = _make_args(source=str(env_file), format="dotenv")
    cmd_export(args)
    out = capsys.readouterr().out
    assert 'API_KEY="abc123"' in out


def test_cmd_export_stdout_shell(env_file: Path, capsys) -> None:
    args = _make_args(source=str(env_file), format="shell")
    cmd_export(args)
    out = capsys.readouterr().out
    assert 'export API_KEY="abc123"' in out


def test_cmd_export_stdout_json(env_file: Path, capsys) -> None:
    args = _make_args(source=str(env_file), format="json")
    cmd_export(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["API_KEY"] == "abc123"


def test_cmd_export_to_file(env_file: Path, tmp_path: Path, capsys) -> None:
    dest = tmp_path / "out.json"
    args = _make_args(source=str(env_file), format="json", output=str(dest))
    cmd_export(args)
    assert dest.exists()
    data = json.loads(dest.read_text())
    assert data["DEBUG"] == "false"
    out = capsys.readouterr().out
    assert "Exported" in out


def test_cmd_export_missing_source_exits(tmp_path: Path) -> None:
    args = _make_args(source=str(tmp_path / "missing.env"))
    with pytest.raises(SystemExit) as exc_info:
        cmd_export(args)
    assert exc_info.value.code == 1


def test_build_export_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["export", "some.env", "--format", "shell"])
    assert args.format == "shell"
    assert args.source == "some.env"
    assert args.func is not None
