"""Tests for envault.sync module."""

import pytest
from pathlib import Path

from envault.sync import SyncError, push, pull, status


@pytest.fixture()
def local_vault(tmp_path):
    vault = tmp_path / ".envvault"
    vault.mkdir()
    (vault / "meta.json").write_text('{"recipients": []}')
    (vault / "env.enc").write_bytes(b"encrypted-data")
    return vault


@pytest.fixture()
def remote_dir(tmp_path):
    remote = tmp_path / "remote"
    remote.mkdir()
    return remote


def test_push_copies_files(local_vault, remote_dir):
    push(local_vault, str(remote_dir))
    assert (remote_dir / "meta.json").exists()
    assert (remote_dir / "env.enc").read_bytes() == b"encrypted-data"


def test_push_creates_remote_dir(local_vault, tmp_path):
    remote = tmp_path / "new_remote" / "nested"
    push(local_vault, str(remote))
    assert remote.is_dir()
    assert (remote / "meta.json").exists()


def test_push_missing_vault_raises(tmp_path, remote_dir):
    missing = tmp_path / "nonexistent"
    with pytest.raises(SyncError, match="Vault directory not found"):
        push(missing, str(remote_dir))


def test_pull_copies_files(local_vault, remote_dir):
    # seed remote
    (remote_dir / "meta.json").write_text('{"recipients": ["alice"]}')
    (remote_dir / "env.enc").write_bytes(b"remote-data")

    dest = local_vault.parent / "pulled_vault"
    pull(str(remote_dir), dest)

    assert (dest / "meta.json").read_text() == '{"recipients": ["alice"]}'
    assert (dest / "env.enc").read_bytes() == b"remote-data"


def test_pull_missing_remote_raises(tmp_path, local_vault):
    missing = tmp_path / "no_remote"
    with pytest.raises(SyncError, match="Remote location not found"):
        pull(str(missing), local_vault)


def test_pull_accepts_file_url(local_vault, remote_dir):
    (remote_dir / "env.enc").write_bytes(b"x")
    dest = local_vault.parent / "dest"
    pull(f"file://{remote_dir}", dest)
    assert (dest / "env.enc").exists()


def test_status_in_sync(local_vault, remote_dir):
    push(local_vault, str(remote_dir))
    result = status(local_vault, str(remote_dir))
    assert set(result["in_sync"]) == {"meta.json", "env.enc"}
    assert result["local_only"] == []
    assert result["remote_only"] == []


def test_status_local_only(local_vault, remote_dir):
    result = status(local_vault, str(remote_dir))
    assert set(result["local_only"]) == {"meta.json", "env.enc"}
    assert result["remote_only"] == []


def test_status_remote_only(local_vault, remote_dir):
    (remote_dir / "extra.enc").write_bytes(b"extra")
    result = status(local_vault, str(remote_dir))
    assert "extra.enc" in result["remote_only"]
