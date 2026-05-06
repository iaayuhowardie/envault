"""Tests for envault.ratelimit."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envault.ratelimit import (
    RateLimitError,
    configure,
    load_ratelimit,
    record_attempt,
    reset,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_WINDOW_SECONDS,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_ratelimit_missing_returns_defaults(vault_dir: Path) -> None:
    state = load_ratelimit(vault_dir)
    assert state["attempts"] == []
    assert state["max_attempts"] == DEFAULT_MAX_ATTEMPTS
    assert state["window"] == DEFAULT_WINDOW_SECONDS


def test_load_ratelimit_corrupt_raises(vault_dir: Path) -> None:
    path = vault_dir / ".envault" / "ratelimit.json"
    path.parent.mkdir(parents=True)
    path.write_text("not-json")
    with pytest.raises(RateLimitError, match="Corrupt"):
        load_ratelimit(vault_dir)


def test_configure_stores_values(vault_dir: Path) -> None:
    configure(vault_dir, max_attempts=3, window=30)
    state = load_ratelimit(vault_dir)
    assert state["max_attempts"] == 3
    assert state["window"] == 30


def test_configure_invalid_max_attempts_raises(vault_dir: Path) -> None:
    with pytest.raises(RateLimitError, match="max_attempts"):
        configure(vault_dir, max_attempts=0, window=60)


def test_configure_invalid_window_raises(vault_dir: Path) -> None:
    with pytest.raises(RateLimitError, match="window"):
        configure(vault_dir, max_attempts=5, window=0)


def test_record_attempt_increments_counter(vault_dir: Path) -> None:
    record_attempt(vault_dir)
    state = load_ratelimit(vault_dir)
    assert len(state["attempts"]) == 1


def test_record_attempt_raises_when_limit_exceeded(vault_dir: Path) -> None:
    configure(vault_dir, max_attempts=3, window=60)
    for _ in range(3):
        record_attempt(vault_dir)
    with pytest.raises(RateLimitError, match="Rate limit exceeded"):
        record_attempt(vault_dir)


def test_record_attempt_prunes_expired_timestamps(vault_dir: Path) -> None:
    configure(vault_dir, max_attempts=3, window=1)
    # Manually insert an old timestamp
    state = load_ratelimit(vault_dir)
    state["attempts"] = [time.time() - 5]  # expired
    from envault.ratelimit import save_ratelimit
    save_ratelimit(vault_dir, state)
    # Should not raise because old attempt is pruned
    record_attempt(vault_dir)
    state = load_ratelimit(vault_dir)
    assert len(state["attempts"]) == 1


def test_reset_clears_attempts(vault_dir: Path) -> None:
    record_attempt(vault_dir)
    record_attempt(vault_dir)
    reset(vault_dir)
    state = load_ratelimit(vault_dir)
    assert state["attempts"] == []


def test_reset_preserves_config(vault_dir: Path) -> None:
    configure(vault_dir, max_attempts=7, window=120)
    record_attempt(vault_dir)
    reset(vault_dir)
    state = load_ratelimit(vault_dir)
    assert state["max_attempts"] == 7
    assert state["window"] == 120
