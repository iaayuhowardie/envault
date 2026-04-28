"""Tests for envault.watch."""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.watch import WatchError, _file_digest, watch


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("KEY=value\n")
    meta = tmp_path / ".envault_meta.json"
    import json
    meta.write_text(json.dumps({"recipients": ["alice@example.com"], "env_file": ".env"}))
    return tmp_path


def test_file_digest_stable(vault_dir: Path) -> None:
    env = vault_dir / ".env"
    assert _file_digest(env) == _file_digest(env)


def test_file_digest_changes_on_write(vault_dir: Path) -> None:
    env = vault_dir / ".env"
    d1 = _file_digest(env)
    env.write_text("KEY=other\n")
    d2 = _file_digest(env)
    assert d1 != d2


def test_watch_missing_env_raises(tmp_path: Path) -> None:
    import json
    meta = tmp_path / ".envault_meta.json"
    meta.write_text(json.dumps({"recipients": [], "env_file": ".env"}))
    with pytest.raises(WatchError, match="env file not found"):
        watch(tmp_path, on_change=MagicMock(), interval=0, max_iterations=0)


def test_watch_no_change_does_not_call_callback(vault_dir: Path) -> None:
    callback = MagicMock()
    with patch("envault.watch.time.sleep"):
        watch(vault_dir, on_change=callback, interval=0, max_iterations=3)
    callback.assert_not_called()


def test_watch_detects_change_calls_callback(vault_dir: Path) -> None:
    env = vault_dir / ".env"
    callback = MagicMock()
    call_count = 0

    original_digest = _file_digest(env)

    def fake_sleep(_: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            env.write_text("KEY=changed\n")

    with patch("envault.watch.time.sleep", side_effect=fake_sleep):
        watch(vault_dir, on_change=callback, interval=0, max_iterations=4)

    callback.assert_called_once_with(env)


def test_watch_records_audit_entry(vault_dir: Path) -> None:
    env = vault_dir / ".env"

    def fake_sleep(_: float) -> None:
        env.write_text("KEY=new\n")

    with patch("envault.watch.time.sleep", side_effect=fake_sleep):
        watch(vault_dir, on_change=MagicMock(), interval=0, max_iterations=1)

    from envault.audit import load_log
    log = load_log(vault_dir)
    assert any(e["action"] == "watch" for e in log)


def test_watch_disappeared_env_raises(vault_dir: Path) -> None:
    env = vault_dir / ".env"

    def fake_sleep(_: float) -> None:
        env.unlink()

    with patch("envault.watch.time.sleep", side_effect=fake_sleep):
        with pytest.raises(WatchError, match="disappeared"):
            watch(vault_dir, on_change=MagicMock(), interval=0, max_iterations=1)
