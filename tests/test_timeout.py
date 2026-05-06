"""Tests for envault.timeout."""

from __future__ import annotations

import json
import time

import pytest

from envault.timeout import (
    DEFAULT_TIMEOUT_SECONDS,
    TimeoutError,
    clear_session,
    is_expired,
    load_timeout,
    remaining,
    save_timeout,
    set_timeout,
    start_session,
)


@pytest.fixture()
def vault_dir(tmp_path):
    return tmp_path


def test_load_timeout_missing_returns_defaults(vault_dir):
    data = load_timeout(vault_dir)
    assert data["seconds"] == DEFAULT_TIMEOUT_SECONDS
    assert data["session_start"] is None


def test_load_timeout_corrupt_raises(vault_dir):
    (vault_dir / ".envault_timeout.json").write_text("not-json")
    with pytest.raises(TimeoutError, match="Corrupt"):
        load_timeout(vault_dir)


def test_save_and_load_roundtrip(vault_dir):
    save_timeout(vault_dir, {"seconds": 300, "session_start": 12345.0})
    data = load_timeout(vault_dir)
    assert data["seconds"] == 300
    assert data["session_start"] == 12345.0


def test_set_timeout_stores_value(vault_dir):
    set_timeout(vault_dir, 600)
    data = load_timeout(vault_dir)
    assert data["seconds"] == 600


def test_set_timeout_zero_raises(vault_dir):
    with pytest.raises(TimeoutError, match="positive"):
        set_timeout(vault_dir, 0)


def test_set_timeout_negative_raises(vault_dir):
    with pytest.raises(TimeoutError, match="positive"):
        set_timeout(vault_dir, -60)


def test_start_session_records_timestamp(vault_dir):
    before = time.time()
    ts = start_session(vault_dir)
    after = time.time()
    assert before <= ts <= after
    data = load_timeout(vault_dir)
    assert data["session_start"] == ts


def test_clear_session_removes_timestamp(vault_dir):
    start_session(vault_dir)
    clear_session(vault_dir)
    data = load_timeout(vault_dir)
    assert data["session_start"] is None


def test_is_expired_no_session(vault_dir):
    assert is_expired(vault_dir) is True


def test_is_expired_within_window(vault_dir):
    set_timeout(vault_dir, 300)
    now = time.time()
    start_session(vault_dir)
    # Simulate only 10 seconds having passed
    assert is_expired(vault_dir, now=now + 10) is False


def test_is_expired_past_window(vault_dir):
    set_timeout(vault_dir, 300)
    now = time.time()
    start_session(vault_dir)
    assert is_expired(vault_dir, now=now + 400) is True


def test_remaining_no_session_returns_zero(vault_dir):
    assert remaining(vault_dir) == 0.0


def test_remaining_within_session(vault_dir):
    set_timeout(vault_dir, 300)
    now = time.time()
    start_session(vault_dir)
    secs = remaining(vault_dir, now=now + 100)
    assert abs(secs - 200.0) < 1.0


def test_remaining_expired_session_returns_zero(vault_dir):
    set_timeout(vault_dir, 60)
    now = time.time()
    start_session(vault_dir)
    assert remaining(vault_dir, now=now + 120) == 0.0
