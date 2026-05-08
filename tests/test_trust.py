"""Tests for envault/trust.py."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.trust import (
    TRUST_LEVELS,
    TrustError,
    get_trust,
    load_trust,
    remove_trust,
    save_trust,
    set_trust,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    (tmp_path / ".envault").mkdir()
    return tmp_path


def test_load_trust_missing_returns_empty(vault_dir: Path) -> None:
    assert load_trust(vault_dir) == {}


def test_save_and_load_trust_roundtrip(vault_dir: Path) -> None:
    data = {"AABBCC": "full", "DDEEFF": "marginal"}
    save_trust(vault_dir, data)
    assert load_trust(vault_dir) == data


def test_load_trust_corrupt_raises(vault_dir: Path) -> None:
    (vault_dir / ".envault" / "trust.json").write_text("not json")
    with pytest.raises(TrustError, match="Corrupt"):
        load_trust(vault_dir)


def test_load_trust_wrong_type_raises(vault_dir: Path) -> None:
    (vault_dir / ".envault" / "trust.json").write_text(json.dumps(["a", "b"]))
    with pytest.raises(TrustError, match="JSON object"):
        load_trust(vault_dir)


def test_set_trust_stores_level(vault_dir: Path) -> None:
    set_trust(vault_dir, "AABBCC", "full")
    assert load_trust(vault_dir)["AABBCC"] == "full"


def test_set_trust_invalid_level_raises(vault_dir: Path) -> None:
    with pytest.raises(TrustError, match="Invalid trust level"):
        set_trust(vault_dir, "AABBCC", "superduper")


def test_set_trust_empty_fingerprint_raises(vault_dir: Path) -> None:
    with pytest.raises(TrustError, match="empty"):
        set_trust(vault_dir, "", "full")


def test_set_trust_overwrites_existing(vault_dir: Path) -> None:
    set_trust(vault_dir, "AABBCC", "marginal")
    set_trust(vault_dir, "AABBCC", "ultimate")
    assert load_trust(vault_dir)["AABBCC"] == "ultimate"


def test_get_trust_returns_level(vault_dir: Path) -> None:
    set_trust(vault_dir, "AABBCC", "full")
    assert get_trust(vault_dir, "AABBCC") == "full"


def test_get_trust_missing_returns_none(vault_dir: Path) -> None:
    assert get_trust(vault_dir, "NOTHERE") is None


def test_remove_trust_deletes_entry(vault_dir: Path) -> None:
    set_trust(vault_dir, "AABBCC", "full")
    remove_trust(vault_dir, "AABBCC")
    assert "AABBCC" not in load_trust(vault_dir)


def test_remove_trust_missing_raises(vault_dir: Path) -> None:
    with pytest.raises(TrustError, match="not found"):
        remove_trust(vault_dir, "NOTHERE")


def test_all_trust_levels_accepted(vault_dir: Path) -> None:
    for i, level in enumerate(TRUST_LEVELS):
        fp = f"FP{i:04d}"
        set_trust(vault_dir, fp, level)
        assert get_trust(vault_dir, fp) == level
