"""Tests for envault.passphrase module."""
from __future__ import annotations

import json
import pytest

from envault.passphrase import (
    DEFAULT_POLICY,
    PassphraseError,
    load_policy,
    save_policy,
    set_policy,
    validate_passphrase,
)


@pytest.fixture()
def vault_dir(tmp_path):
    return tmp_path


# ---------------------------------------------------------------------------
# load_policy
# ---------------------------------------------------------------------------

def test_load_policy_missing_returns_defaults(vault_dir):
    policy = load_policy(vault_dir)
    assert policy == DEFAULT_POLICY


def test_load_policy_corrupt_raises(vault_dir):
    (vault_dir / ".envault_passphrase_policy.json").write_text("not-json")
    with pytest.raises(PassphraseError, match="Corrupt"):
        load_policy(vault_dir)


def test_load_policy_wrong_type_raises(vault_dir):
    (vault_dir / ".envault_passphrase_policy.json").write_text("[1,2,3]")
    with pytest.raises(PassphraseError, match="JSON object"):
        load_policy(vault_dir)


# ---------------------------------------------------------------------------
# save / load roundtrip
# ---------------------------------------------------------------------------

def test_save_and_load_policy_roundtrip(vault_dir):
    policy = {"min_length": 20, "require_uppercase": False, "require_digit": True, "require_special": False}
    save_policy(vault_dir, policy)
    loaded = load_policy(vault_dir)
    assert loaded["min_length"] == 20
    assert loaded["require_uppercase"] is False


# ---------------------------------------------------------------------------
# set_policy
# ---------------------------------------------------------------------------

def test_set_policy_updates_min_length(vault_dir):
    policy = set_policy(vault_dir, min_length=16)
    assert policy["min_length"] == 16


def test_set_policy_invalid_min_length_raises(vault_dir):
    with pytest.raises(PassphraseError, match="min_length must be at least 1"):
        set_policy(vault_dir, min_length=0)


def test_set_policy_persists(vault_dir):
    set_policy(vault_dir, min_length=18, require_special=False)
    policy = load_policy(vault_dir)
    assert policy["min_length"] == 18
    assert policy["require_special"] is False


# ---------------------------------------------------------------------------
# validate_passphrase
# ---------------------------------------------------------------------------

def test_validate_passphrase_valid(vault_dir):
    policy = load_policy(vault_dir)
    # Should not raise
    validate_passphrase("Str0ng!Pass#2024", policy)


def test_validate_passphrase_too_short(vault_dir):
    policy = load_policy(vault_dir)
    with pytest.raises(PassphraseError, match="at least"):
        validate_passphrase("Sh0rt!", policy)


def test_validate_passphrase_no_uppercase(vault_dir):
    policy = {**DEFAULT_POLICY, "min_length": 4, "require_uppercase": True}
    with pytest.raises(PassphraseError, match="uppercase"):
        validate_passphrase("abc1!", policy)


def test_validate_passphrase_no_digit(vault_dir):
    policy = {**DEFAULT_POLICY, "min_length": 4, "require_digit": True}
    with pytest.raises(PassphraseError, match="digit"):
        validate_passphrase("Abcd!", policy)


def test_validate_passphrase_no_special(vault_dir):
    policy = {**DEFAULT_POLICY, "min_length": 4, "require_special": True}
    with pytest.raises(PassphraseError, match="special"):
        validate_passphrase("Abcd1234", policy)
