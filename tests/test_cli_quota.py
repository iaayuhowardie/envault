"""Tests for envault.cli_quota."""

from __future__ import annotations

import argparse
import os

import pytest

from envault.cli_quota import build_quota_parser, cmd_quota
from envault.quota import load_quota, save_quota, set_quota


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def parser(vault_dir):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_quota_parser(sub, vault_dir=vault_dir)
    return p


def _args(parser, *argv):
    return parser.parse_args(["quota", *argv])


# ---------------------------------------------------------------------------
# parser registration
# ---------------------------------------------------------------------------

def test_build_quota_parser_registers_command(parser):
    ns = _args(parser, "status")
    assert ns.command == "quota"
    assert ns.quota_cmd == "status"


# ---------------------------------------------------------------------------
# cmd_quota set
# ---------------------------------------------------------------------------

def test_cmd_quota_set(parser, vault_dir, capsys):
    ns = _args(parser, "set", "2048", "--warn", "0.75")
    cmd_quota(ns)
    cfg = load_quota(vault_dir)
    assert cfg["max_bytes"] == 2048
    assert cfg["warn_threshold"] == 0.75
    out = capsys.readouterr().out
    assert "2048" in out


def test_cmd_quota_set_invalid_raises_system_exit(parser, vault_dir):
    ns = _args(parser, "set", "0")
    with pytest.raises(SystemExit):
        cmd_quota(ns)


# ---------------------------------------------------------------------------
# cmd_quota status
# ---------------------------------------------------------------------------

def test_cmd_quota_status_prints_usage(parser, vault_dir, capsys):
    set_quota(vault_dir, max_bytes=5000)
    ns = _args(parser, "status")
    cmd_quota(ns)
    out = capsys.readouterr().out
    assert "Used:" in out


def test_cmd_quota_status_exceeded_raises_system_exit(parser, vault_dir):
    open(os.path.join(vault_dir, "big.bin"), "wb").write(b"z" * 3000)
    set_quota(vault_dir, max_bytes=100)
    ns = _args(parser, "status")
    with pytest.raises(SystemExit):
        cmd_quota(ns)


# ---------------------------------------------------------------------------
# cmd_quota show
# ---------------------------------------------------------------------------

def test_cmd_quota_show_prints_config(parser, vault_dir, capsys):
    set_quota(vault_dir, max_bytes=8192, warn_threshold=0.9)
    ns = _args(parser, "show")
    cmd_quota(ns)
    out = capsys.readouterr().out
    assert "8192" in out
    assert "0.9" in out
