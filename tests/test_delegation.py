"""Tests for envault.delegation."""

import pytest
from pathlib import Path

from envault.delegation import (
    DelegationError,
    grant,
    is_delegate,
    load_delegations,
    revoke,
    save_delegations,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    return tmp_path


def test_load_delegations_missing_returns_empty(vault_dir: Path) -> None:
    assert load_delegations(vault_dir) == {}


def test_save_and_load_delegations_roundtrip(vault_dir: Path) -> None:
    data = {"AAAA": ["BBBB", "CCCC"]}
    save_delegations(vault_dir, data)
    assert load_delegations(vault_dir) == data


def test_load_delegations_corrupt_raises(vault_dir: Path) -> None:
    path = vault_dir / ".envault" / "delegations.json"
    path.write_text("not json")
    with pytest.raises(DelegationError, match="Corrupt"):
        load_delegations(vault_dir)


def test_load_delegations_wrong_type_raises(vault_dir: Path) -> None:
    path = vault_dir / ".envault" / "delegations.json"
    path.write_text("[1, 2, 3]")
    with pytest.raises(DelegationError, match="JSON object"):
        load_delegations(vault_dir)


def test_grant_stores_delegate(vault_dir: Path) -> None:
    grant(vault_dir, "AAAA", "BBBB")
    assert load_delegations(vault_dir) == {"AAAA": ["BBBB"]}


def test_grant_multiple_delegates(vault_dir: Path) -> None:
    grant(vault_dir, "AAAA", "BBBB")
    grant(vault_dir, "AAAA", "CCCC")
    assert load_delegations(vault_dir)["AAAA"] == ["BBBB", "CCCC"]


def test_grant_duplicate_raises(vault_dir: Path) -> None:
    grant(vault_dir, "AAAA", "BBBB")
    with pytest.raises(DelegationError, match="already a delegate"):
        grant(vault_dir, "AAAA", "BBBB")


def test_grant_self_delegation_raises(vault_dir: Path) -> None:
    with pytest.raises(DelegationError, match="cannot delegate to itself"):
        grant(vault_dir, "AAAA", "AAAA")


def test_grant_empty_grantor_raises(vault_dir: Path) -> None:
    with pytest.raises(DelegationError, match="Grantor"):
        grant(vault_dir, "", "BBBB")


def test_grant_empty_delegate_raises(vault_dir: Path) -> None:
    with pytest.raises(DelegationError, match="Delegate"):
        grant(vault_dir, "AAAA", "")


def test_revoke_removes_delegate(vault_dir: Path) -> None:
    grant(vault_dir, "AAAA", "BBBB")
    revoke(vault_dir, "AAAA", "BBBB")
    assert load_delegations(vault_dir) == {}


def test_revoke_nonexistent_raises(vault_dir: Path) -> None:
    with pytest.raises(DelegationError, match="not a delegate"):
        revoke(vault_dir, "AAAA", "BBBB")


def test_is_delegate_true(vault_dir: Path) -> None:
    grant(vault_dir, "AAAA", "BBBB")
    assert is_delegate(vault_dir, "AAAA", "BBBB") is True


def test_is_delegate_false(vault_dir: Path) -> None:
    assert is_delegate(vault_dir, "AAAA", "BBBB") is False
