"""Tests for envault.session."""

from __future__ import annotations

import time
import json
import pytest
from pathlib import Path

from envault.session import (
    SessionError,
    _session_path,
    load_session,
    save_session,
    open_session,
    close_session,
    is_session_active,
    get_active_fingerprint,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    return tmp_path


def test_load_session_missing_returns_empty(vault_dir):
    assert load_session(vault_dir) == {}


def test_load_session_corrupt_returns_empty(vault_dir):
    _session_path(vault_dir).write_text("not json")
    assert load_session(vault_dir) == {}


def test_save_and_load_session_roundtrip(vault_dir):
    data = {"fingerprint": "ABCD1234", "created_at": 1000.0, "expires_at": 2000.0}
    save_session(vault_dir, data)
    assert load_session(vault_dir) == data


def test_open_session_stores_fingerprint(vault_dir):
    session = open_session(vault_dir, "DEADBEEF", ttl_seconds=60)
    assert session["fingerprint"] == "DEADBEEF"
    assert session["expires_at"] > session["created_at"]


def test_open_session_empty_fingerprint_raises(vault_dir):
    with pytest.raises(SessionError, match="fingerprint"):
        open_session(vault_dir, "", ttl_seconds=60)


def test_open_session_non_positive_ttl_raises(vault_dir):
    with pytest.raises(SessionError, match="ttl_seconds"):
        open_session(vault_dir, "ABCD", ttl_seconds=0)


def test_close_session_removes_file(vault_dir):
    open_session(vault_dir, "ABCD", ttl_seconds=60)
    assert _session_path(vault_dir).exists()
    close_session(vault_dir)
    assert not _session_path(vault_dir).exists()


def test_close_session_no_file_is_noop(vault_dir):
    close_session(vault_dir)  # should not raise


def test_is_session_active_with_valid_session(vault_dir):
    open_session(vault_dir, "ABCD", ttl_seconds=3600)
    assert is_session_active(vault_dir) is True


def test_is_session_active_with_expired_session(vault_dir):
    session = {
        "fingerprint": "ABCD",
        "created_at": time.time() - 7200,
        "expires_at": time.time() - 3600,
    }
    save_session(vault_dir, session)
    assert is_session_active(vault_dir) is False


def test_is_session_active_no_session(vault_dir):
    assert is_session_active(vault_dir) is False


def test_get_active_fingerprint_returns_fingerprint(vault_dir):
    open_session(vault_dir, "CAFEBABE", ttl_seconds=3600)
    assert get_active_fingerprint(vault_dir) == "CAFEBABE"


def test_get_active_fingerprint_expired_returns_none(vault_dir):
    session = {
        "fingerprint": "CAFEBABE",
        "created_at": time.time() - 7200,
        "expires_at": time.time() - 1,
    }
    save_session(vault_dir, session)
    assert get_active_fingerprint(vault_dir) is None
