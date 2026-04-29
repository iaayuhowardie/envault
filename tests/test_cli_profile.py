"""Tests for envault.cli_profile."""

from __future__ import annotations

import argparse
import pytest
from pathlib import Path

from envault.cli_profile import build_profile_parser, cmd_profile
from envault.profile import create_profile, load_profiles
from envault.vault import load_meta, save_meta


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    save_meta(tmp_path, {"recipients": [], "encrypted_file": ".env.gpg"})
    return tmp_path


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_profile_parser(sub)
    return p


def _args(parser, vault_dir, *extra):
    return parser.parse_args(["profile", "--vault-dir", str(vault_dir), *extra])


def test_build_profile_parser_registers_command(parser):
    assert parser.parse_args(["profile", "--vault-dir", ".", "list"]) is not None


def test_cmd_profile_create(parser, vault_dir):
    args = _args(parser, vault_dir, "create", "prod", "FP1", "FP2")
    cmd_profile(args)
    assert load_profiles(vault_dir)["prod"] == ["FP1", "FP2"]


def test_cmd_profile_delete(parser, vault_dir):
    create_profile(vault_dir, "dev", ["FP3"])
    args = _args(parser, vault_dir, "delete", "dev")
    cmd_profile(args)
    assert "dev" not in load_profiles(vault_dir)


def test_cmd_profile_apply(parser, vault_dir):
    create_profile(vault_dir, "staging", ["FP4"])
    args = _args(parser, vault_dir, "apply", "staging")
    cmd_profile(args)
    assert load_meta(vault_dir)["recipients"] == ["FP4"]


def test_cmd_profile_list_empty(parser, vault_dir, capsys):
    args = _args(parser, vault_dir, "list")
    cmd_profile(args)
    assert "No profiles" in capsys.readouterr().out


def test_cmd_profile_list_shows_profiles(parser, vault_dir, capsys):
    create_profile(vault_dir, "alpha", ["FP5"])
    args = _args(parser, vault_dir, "list")
    cmd_profile(args)
    out = capsys.readouterr().out
    assert "alpha" in out and "FP5" in out


def test_cmd_profile_create_error_raises_system_exit(parser, vault_dir):
    args = _args(parser, vault_dir, "create", "bad")  # no fingerprints
    args.fingerprints = []
    with pytest.raises(SystemExit, match="error"):
        cmd_profile(args)


def test_cmd_profile_apply_missing_raises_system_exit(parser, vault_dir):
    args = _args(parser, vault_dir, "apply", "ghost")
    with pytest.raises(SystemExit, match="error"):
        cmd_profile(args)
