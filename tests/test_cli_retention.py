"""Tests for envault.cli_retention."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.cli_retention import build_retention_parser, cmd_retention
from envault.retention import save_retention


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_retention_parser(sub)
    return p


def _args(parser: argparse.ArgumentParser, vault_dir: Path, *extra: str) -> argparse.Namespace:
    return parser.parse_args(["retention", "--vault-dir", str(vault_dir), *extra])


def test_build_retention_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    assert parser.parse_args(["retention", "--vault-dir", ".", "show"]) is not None


def test_cmd_retention_show(vault_dir: Path, parser: argparse.ArgumentParser, capsys) -> None:
    save_retention(vault_dir, {"max_snapshots": 7, "max_days": 45})
    args = _args(parser, vault_dir, "show")
    cmd_retention(args)
    out = capsys.readouterr().out
    assert "7" in out
    assert "45" in out


def test_cmd_retention_set(vault_dir: Path, parser: argparse.ArgumentParser, capsys) -> None:
    args = _args(parser, vault_dir, "set", "--max-snapshots", "4", "--max-days", "20")
    cmd_retention(args)
    out = capsys.readouterr().out
    assert "4" in out
    assert "20" in out
    from envault.retention import load_retention
    policy = load_retention(vault_dir)
    assert policy["max_snapshots"] == 4
    assert policy["max_days"] == 20


def test_cmd_retention_set_invalid_raises(vault_dir: Path, parser: argparse.ArgumentParser) -> None:
    args = _args(parser, vault_dir, "set", "--max-snapshots", "0")
    with pytest.raises(SystemExit, match="max_snapshots"):
        cmd_retention(args)


def test_cmd_retention_prune(vault_dir: Path, parser: argparse.ArgumentParser, capsys) -> None:
    import datetime
    from envault.retention import set_retention

    set_retention(vault_dir, max_snapshots=1, max_days=9999)
    snaps_dir = vault_dir / ".envault_snapshots"
    snaps_dir.mkdir()
    meta = []
    for i in range(3):
        name = f"snap_{i}.enc"
        (snaps_dir / name).write_text(f"data{i}")
        created = (datetime.datetime.utcnow() - datetime.timedelta(days=i)).isoformat()
        meta.append({"name": name, "created_at": created})
    (vault_dir / ".envault_snapshots_meta.json").write_text(json.dumps(meta))

    with patch("envault.cli_retention.list_snapshots", return_value=meta):
        with patch("envault.cli_retention._snapshots_path", return_value=snaps_dir):
            args = _args(parser, vault_dir, "prune")
            cmd_retention(args)

    out = capsys.readouterr().out
    assert "pruned" in out.lower()
