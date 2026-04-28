"""Tests for envault.cli_watch."""

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.cli_watch import build_watch_parser, cmd_watch


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("SECRET=abc\n")
    meta = tmp_path / ".envault_meta.json"
    meta.write_text(
        json.dumps({"recipients": ["bob@example.com"], "env_file": ".env"})
    )
    return tmp_path


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    build_watch_parser(subs)
    return root


def test_build_watch_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["watch", "--dir", "/tmp", "--interval", "2.5"])
    assert args.interval == 2.5


def test_cmd_watch_calls_watch(vault_dir: Path) -> None:
    with patch("envault.cli_watch.watch") as mock_watch:
        cmd_watch(vault_dir, interval=0.1, max_iterations=0)
        mock_watch.assert_called_once()
        _, kwargs = mock_watch.call_args
        assert kwargs["interval"] == 0.1
        assert kwargs["max_iterations"] == 0


def test_cmd_watch_raises_system_exit_on_watch_error(vault_dir: Path) -> None:
    from envault.watch import WatchError

    with patch("envault.cli_watch.watch", side_effect=WatchError("boom")):
        with pytest.raises(SystemExit, match="boom"):
            cmd_watch(vault_dir)


def test_cmd_watch_keyboard_interrupt_exits_cleanly(
    vault_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    with patch("envault.cli_watch.watch", side_effect=KeyboardInterrupt):
        cmd_watch(vault_dir)  # should not raise
    captured = capsys.readouterr()
    assert "stopped" in captured.out


def test_auto_lock_invoked_on_change(vault_dir: Path) -> None:
    env = vault_dir / ".env"
    call_log: list[Path] = []

    def fake_watch(vault_dir, on_change, interval, max_iterations):
        on_change(env)

    with patch("envault.cli_watch.watch", side_effect=fake_watch):
        with patch("envault.cli_watch.cmd_lock") as mock_lock:
            cmd_watch(vault_dir, interval=0)
            mock_lock.assert_called_once_with(vault_dir)
