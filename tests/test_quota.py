"""Tests for envault.quota."""

from __future__ import annotations

import json
import os

import pytest

from envault.quota import (
    DEFAULT_MAX_BYTES,
    QuotaError,
    check_quota,
    load_quota,
    save_quota,
    set_quota,
    vault_size,
)


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# load_quota
# ---------------------------------------------------------------------------

def test_load_quota_missing_returns_defaults(vault_dir):
    config = load_quota(vault_dir)
    assert config["max_bytes"] == DEFAULT_MAX_BYTES
    assert config["warn_threshold"] == 0.8


def test_load_quota_corrupt_raises(vault_dir):
    path = os.path.join(vault_dir, ".quota.json")
    open(path, "w").write("{bad json")
    with pytest.raises(QuotaError, match="Corrupt"):
        load_quota(vault_dir)


# ---------------------------------------------------------------------------
# save_quota / roundtrip
# ---------------------------------------------------------------------------

def test_save_and_load_quota_roundtrip(vault_dir):
    cfg = {"max_bytes": 1234, "warn_threshold": 0.5}
    save_quota(vault_dir, cfg)
    loaded = load_quota(vault_dir)
    assert loaded == cfg


# ---------------------------------------------------------------------------
# set_quota
# ---------------------------------------------------------------------------

def test_set_quota_stores_values(vault_dir):
    set_quota(vault_dir, max_bytes=5000, warn_threshold=0.7)
    cfg = load_quota(vault_dir)
    assert cfg["max_bytes"] == 5000
    assert cfg["warn_threshold"] == 0.7


def test_set_quota_zero_raises(vault_dir):
    with pytest.raises(QuotaError, match="positive"):
        set_quota(vault_dir, max_bytes=0)


def test_set_quota_bad_threshold_raises(vault_dir):
    with pytest.raises(QuotaError, match="warn_threshold"):
        set_quota(vault_dir, max_bytes=1000, warn_threshold=1.5)


# ---------------------------------------------------------------------------
# vault_size
# ---------------------------------------------------------------------------

def test_vault_size_empty_dir(vault_dir):
    assert vault_size(vault_dir) == 0


def test_vault_size_counts_bytes(vault_dir):
    path = os.path.join(vault_dir, "file.txt")
    content = b"hello world"
    open(path, "wb").write(content)
    assert vault_size(vault_dir) == len(content)


# ---------------------------------------------------------------------------
# check_quota
# ---------------------------------------------------------------------------

def test_check_quota_within_limit(vault_dir):
    set_quota(vault_dir, max_bytes=DEFAULT_MAX_BYTES)
    status = check_quota(vault_dir)
    assert not status["exceeded"]
    assert isinstance(status["ratio"], float)


def test_check_quota_warning_flag(vault_dir):
    data = b"x" * 900
    open(os.path.join(vault_dir, "big.bin"), "wb").write(data)
    # quota file itself is small; set limit so used/max > 0.8
    set_quota(vault_dir, max_bytes=1000, warn_threshold=0.8)
    status = check_quota(vault_dir)
    assert status["warning"]


def test_check_quota_exceeded_raises(vault_dir):
    open(os.path.join(vault_dir, "big.bin"), "wb").write(b"x" * 2000)
    set_quota(vault_dir, max_bytes=100)
    with pytest.raises(QuotaError, match="exceeds quota"):
        check_quota(vault_dir)
