"""Tests for envault.search and envault.cli_search."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.search import (
    SearchError,
    SearchResult,
    format_search_results,
    search_keys,
)
from envault.cli_search import build_search_parser, cmd_search


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write_env(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# search_keys
# ---------------------------------------------------------------------------

def test_search_keys_basic_match(env_dir: Path) -> None:
    f = _write_env(env_dir, ".env", "DATABASE_URL=postgres://localhost\nSECRET_KEY=abc123\n")
    results = search_keys([f], "DATABASE")
    assert len(results) == 1
    assert results[0].key == "DATABASE_URL"
    assert results[0].line_number == 1


def test_search_keys_no_match_returns_empty(env_dir: Path) -> None:
    f = _write_env(env_dir, ".env", "FOO=bar\n")
    assert search_keys([f], "MISSING") == []


def test_search_keys_case_insensitive_default(env_dir: Path) -> None:
    f = _write_env(env_dir, ".env", "Api_Key=secret\n")
    results = search_keys([f], "api_key")
    assert len(results) == 1


def test_search_keys_case_sensitive(env_dir: Path) -> None:
    f = _write_env(env_dir, ".env", "API_KEY=secret\n")
    assert search_keys([f], "api_key", case_sensitive=True) == []
    results = search_keys([f], "API_KEY", case_sensitive=True)
    assert len(results) == 1


def test_search_keys_value_pattern_filter(env_dir: Path) -> None:
    f = _write_env(env_dir, ".env", "DB=postgres://host\nCACHE=redis://host\n")
    results = search_keys([f], "", value_pattern="postgres")
    assert len(results) == 1
    assert results[0].key == "DB"


def test_search_keys_multiple_files(env_dir: Path) -> None:
    f1 = _write_env(env_dir, ".env.dev", "TOKEN=dev_token\n")
    f2 = _write_env(env_dir, ".env.prod", "TOKEN=prod_token\n")
    results = search_keys([f1, f2], "TOKEN")
    assert len(results) == 2
    files = {r.file for r in results}
    assert str(f1) in files and str(f2) in files


def test_search_keys_skips_comments_and_blanks(env_dir: Path) -> None:
    f = _write_env(env_dir, ".env", "# COMMENT=ignored\n\nFOO=bar\n")
    results = search_keys([f], "COMMENT")
    assert results == []


def test_search_keys_no_files_raises() -> None:
    with pytest.raises(SearchError, match="No env files"):
        search_keys([], "ANYTHING")


def test_search_keys_missing_file_raises(env_dir: Path) -> None:
    with pytest.raises(SearchError, match="Cannot read file"):
        search_keys([env_dir / "ghost.env"], "KEY")


def test_search_keys_invalid_pattern_raises(env_dir: Path) -> None:
    f = _write_env(env_dir, ".env", "FOO=bar\n")
    with pytest.raises(SearchError, match="Invalid key pattern"):
        search_keys([f], "[invalid")


# ---------------------------------------------------------------------------
# format_search_results
# ---------------------------------------------------------------------------

def test_format_search_results_empty() -> None:
    assert format_search_results([]) == "No matches found."


def test_format_search_results_groups_by_file() -> None:
    results = [
        SearchResult(file="a.env", key="FOO", value="1", line_number=1),
        SearchResult(file="a.env", key="BAR", value="2", line_number=2),
        SearchResult(file="b.env", key="BAZ", value="3", line_number=1),
    ]
    output = format_search_results(results)
    assert "a.env" in output
    assert "b.env" in output
    assert "FOO=1" in output
    assert "BAZ=3" in output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    build_search_parser(sub)
    return root


def test_build_search_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["search", "TOKEN", "some.env"])
    assert args.pattern == "TOKEN"
    assert args.files == ["some.env"]


def test_cmd_search_prints_results(env_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    f = _write_env(env_dir, ".env", "TOKEN=abc\n")
    ns = argparse.Namespace(
        pattern="TOKEN",
        files=[str(f)],
        case_sensitive=False,
        value_pattern=None,
        count=False,
    )
    cmd_search(ns)
    captured = capsys.readouterr()
    assert "TOKEN=abc" in captured.out


def test_cmd_search_missing_file_exits(env_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ns = argparse.Namespace(
        pattern="KEY",
        files=[str(env_dir / "nope.env")],
        case_sensitive=False,
        value_pattern=None,
        count=False,
    )
    with pytest.raises(SystemExit) as exc_info:
        cmd_search(ns)
    assert exc_info.value.code == 1


def test_cmd_search_count_flag(env_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    f = _write_env(env_dir, ".env", "A=1\nAB=2\n")
    ns = argparse.Namespace(
        pattern="A",
        files=[str(f)],
        case_sensitive=False,
        value_pattern=None,
        count=True,
    )
    cmd_search(ns)
    captured = capsys.readouterr()
    assert "2 match(es)" in captured.out
