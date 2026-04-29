"""Tests for envault.profile."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.profile import (
    ProfileError,
    apply_profile,
    create_profile,
    delete_profile,
    load_profiles,
    save_profiles,
)
from envault.vault import save_meta


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    save_meta(tmp_path, {"recipients": [], "encrypted_file": ".env.gpg"})
    return tmp_path


def test_load_profiles_missing_returns_empty(vault_dir):
    assert load_profiles(vault_dir) == {}


def test_create_profile_stores_fingerprints(vault_dir):
    create_profile(vault_dir, "staging", ["AAAA", "BBBB"])
    profiles = load_profiles(vault_dir)
    assert profiles["staging"] == ["AAAA", "BBBB"]


def test_create_profile_empty_name_raises(vault_dir):
    with pytest.raises(ProfileError, match="empty"):
        create_profile(vault_dir, "  ", ["AAAA"])


def test_create_profile_no_fingerprints_raises(vault_dir):
    with pytest.raises(ProfileError, match="at least one"):
        create_profile(vault_dir, "prod", [])


def test_create_profile_overwrites_existing(vault_dir):
    create_profile(vault_dir, "dev", ["AAAA"])
    create_profile(vault_dir, "dev", ["CCCC"])
    assert load_profiles(vault_dir)["dev"] == ["CCCC"]


def test_delete_profile_removes_entry(vault_dir):
    create_profile(vault_dir, "dev", ["AAAA"])
    delete_profile(vault_dir, "dev")
    assert "dev" not in load_profiles(vault_dir)


def test_delete_profile_missing_raises(vault_dir):
    with pytest.raises(ProfileError, match="does not exist"):
        delete_profile(vault_dir, "ghost")


def test_apply_profile_updates_recipients(vault_dir):
    create_profile(vault_dir, "prod", ["FP1", "FP2"])
    apply_profile(vault_dir, "prod")
    from envault.vault import load_meta
    meta = load_meta(vault_dir)
    assert meta["recipients"] == ["FP1", "FP2"]


def test_apply_profile_missing_raises(vault_dir):
    with pytest.raises(ProfileError, match="does not exist"):
        apply_profile(vault_dir, "nonexistent")


def test_save_load_roundtrip(vault_dir):
    data = {"a": ["X"], "b": ["Y", "Z"]}
    save_profiles(vault_dir, data)
    assert load_profiles(vault_dir) == data
