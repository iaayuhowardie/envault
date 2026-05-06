"""Tests for envault.notify and envault.cli_notify."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.notify import (
    EVENTS,
    NotifyError,
    dispatch,
    load_notify,
    save_notify,
    send_webhook,
    set_notify,
)
from envault.cli_notify import build_notify_parser, cmd_notify


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# load_notify
# ---------------------------------------------------------------------------

def test_load_notify_missing_returns_defaults(vault_dir: Path) -> None:
    config = load_notify(vault_dir)
    assert config["webhook"] is None
    assert config["email"] is None
    assert set(config["events"]) == EVENTS


def test_load_notify_corrupt_raises(vault_dir: Path) -> None:
    (vault_dir / ".envault" / "notify.json").write_text("{bad json")
    with pytest.raises(NotifyError, match="Corrupt"):
        load_notify(vault_dir)


# ---------------------------------------------------------------------------
# save / set_notify
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(vault_dir: Path) -> None:
    cfg = {"webhook": "https://example.com/hook", "email": None, "events": ["lock"]}
    save_notify(vault_dir, cfg)
    loaded = load_notify(vault_dir)
    assert loaded["webhook"] == "https://example.com/hook"
    assert loaded["events"] == ["lock"]


def test_set_notify_updates_webhook(vault_dir: Path) -> None:
    cfg = set_notify(vault_dir, webhook="https://hook.example")
    assert cfg["webhook"] == "https://hook.example"


def test_set_notify_unknown_event_raises(vault_dir: Path) -> None:
    with pytest.raises(NotifyError, match="Unknown events"):
        set_notify(vault_dir, events=["bogus"])


# ---------------------------------------------------------------------------
# send_webhook
# ---------------------------------------------------------------------------

def test_send_webhook_posts_json() -> None:
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        send_webhook("https://example.com/hook", "lock", {"user": "alice"})
    mock_open.assert_called_once()


def test_send_webhook_raises_on_failure() -> None:
    with patch("urllib.request.urlopen", side_effect=OSError("timeout")):
        with pytest.raises(NotifyError, match="Webhook delivery failed"):
            send_webhook("https://example.com/hook", "lock", {})


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------

def test_dispatch_unknown_event_raises(vault_dir: Path) -> None:
    with pytest.raises(NotifyError, match="Unknown event"):
        dispatch(vault_dir, "explode")


def test_dispatch_skips_unsubscribed_event(vault_dir: Path) -> None:
    set_notify(vault_dir, events=["lock"])
    with patch("envault.notify.send_webhook") as mock_wh:
        dispatch(vault_dir, "pull")  # not subscribed
    mock_wh.assert_not_called()


def test_dispatch_calls_webhook_when_subscribed(vault_dir: Path) -> None:
    set_notify(vault_dir, webhook="https://hook.example", events=["rotate"])
    with patch("envault.notify.send_webhook") as mock_wh:
        dispatch(vault_dir, "rotate", {"keys": 3})
    mock_wh.assert_called_once_with("https://hook.example", "rotate", {"keys": 3})


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_notify_parser(sub)
    return p


def _args(parser: argparse.ArgumentParser, *argv: str) -> argparse.Namespace:
    return parser.parse_args(argv)


def test_build_notify_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    ns = _args(parser, "notify", "show")
    assert ns.command == "notify"
    assert ns.notify_cmd == "show"


def test_cmd_notify_show(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture[str]) -> None:
    set_notify(vault_dir, webhook="https://w.example")
    ns = _args(parser, "notify", "show")
    ns.vault_dir = str(vault_dir)
    cmd_notify(ns)
    out = capsys.readouterr().out
    assert "https://w.example" in out


def test_cmd_notify_set_and_show(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture[str]) -> None:
    ns = _args(parser, "notify", "set", "--webhook", "https://x.example", "--events", "lock,push")
    ns.vault_dir = str(vault_dir)
    cmd_notify(ns)
    config = load_notify(vault_dir)
    assert config["webhook"] == "https://x.example"
    assert set(config["events"]) == {"lock", "push"}


def test_cmd_notify_set_bad_event_raises_system_exit(vault_dir: Path, parser: argparse.ArgumentParser) -> None:
    ns = _args(parser, "notify", "set", "--events", "bad_event")
    ns.vault_dir = str(vault_dir)
    with pytest.raises(SystemExit):
        cmd_notify(ns)


def test_cmd_notify_test_dispatches(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture[str]) -> None:
    set_notify(vault_dir, events=["lock"])
    ns = _args(parser, "notify", "test", "lock")
    ns.vault_dir = str(vault_dir)
    with patch("envault.notify.send_webhook"):
        with patch("envault.notify.send_email"):
            cmd_notify(ns)
    out = capsys.readouterr().out
    assert "lock" in out
