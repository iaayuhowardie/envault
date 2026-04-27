"""Tests for envault.export module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.export import (
    ExportError,
    export_dotenv,
    export_file,
    export_json,
    export_shell,
    parse_env_file,
)


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "# comment\n"
        "DB_HOST=localhost\n"
        'DB_PASS="secret value"\n'
        "DEBUG=true\n"
        "\n"
        "EMPTY=\n",
        encoding="utf-8",
    )
    return p


def test_parse_env_file_basic(env_file: Path) -> None:
    env = parse_env_file(env_file)
    assert env["DB_HOST"] == "localhost"
    assert env["DB_PASS"] == "secret value"
    assert env["DEBUG"] == "true"
    assert "EMPTY" in env


def test_parse_env_file_skips_comments(env_file: Path) -> None:
    env = parse_env_file(env_file)
    assert all(not k.startswith("#") for k in env)


def test_parse_env_file_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(ExportError, match="File not found"):
        parse_env_file(tmp_path / "nonexistent.env")


def test_export_shell_format(env_file: Path) -> None:
    env = parse_env_file(env_file)
    output = export_shell(env)
    assert 'export DB_HOST="localhost"' in output
    assert 'export DB_PASS="secret value"' in output


def test_export_json_format(env_file: Path) -> None:
    env = parse_env_file(env_file)
    output = export_json(env)
    parsed = json.loads(output)
    assert parsed["DB_HOST"] == "localhost"
    assert parsed["DB_PASS"] == "secret value"


def test_export_dotenv_format(env_file: Path) -> None:
    env = parse_env_file(env_file)
    output = export_dotenv(env)
    assert 'DB_HOST="localhost"' in output
    assert 'DB_PASS="secret value"' in output


def test_export_file_writes_json(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "output.json"
    export_file(env_file, dest, fmt="json")
    assert dest.exists()
    data = json.loads(dest.read_text())
    assert data["DB_HOST"] == "localhost"


def test_export_file_writes_shell(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "env.sh"
    export_file(env_file, dest, fmt="shell")
    content = dest.read_text()
    assert "export" in content


def test_export_file_unknown_format_raises(env_file: Path, tmp_path: Path) -> None:
    with pytest.raises(ExportError, match="Unknown format"):
        export_file(env_file, tmp_path / "out", fmt="xml")
