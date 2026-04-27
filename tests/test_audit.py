"""Tests for envault.audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.audit import (
    AuditError,
    AUDIT_FILENAME,
    load_log,
    record,
    clear_log,
    _audit_path,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_log_missing_file_returns_empty(vault_dir: Path) -> None:
    assert load_log(vault_dir) == []


def test_record_creates_file(vault_dir: Path) -> None:
    record(vault_dir, "lock")
    assert _audit_path(vault_dir).exists()


def test_record_entry_fields(vault_dir: Path) -> None:
    entry = record(vault_dir, "lock", actor="alice", details={"file": ".env"})
    assert entry["action"] == "lock"
    assert entry["actor"] == "alice"
    assert entry["details"] == {"file": ".env"}
    assert "timestamp" in entry


def test_record_appends_multiple_entries(vault_dir: Path) -> None:
    record(vault_dir, "add_recipient", actor="alice")
    record(vault_dir, "lock", actor="alice")
    record(vault_dir, "unlock", actor="bob")
    log = load_log(vault_dir)
    assert len(log) == 3
    assert log[0]["action"] == "add_recipient"
    assert log[2]["action"] == "unlock"


def test_record_default_actor_fallback(vault_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("USER", raising=False)
    monkeypatch.delenv("USERNAME", raising=False)
    entry = record(vault_dir, "remove_recipient")
    assert entry["actor"] == "unknown"


def test_clear_log(vault_dir: Path) -> None:
    record(vault_dir, "lock", actor="alice")
    record(vault_dir, "unlock", actor="bob")
    clear_log(vault_dir)
    assert load_log(vault_dir) == []
    assert _audit_path(vault_dir).exists()


def test_load_log_corrupt_json_raises(vault_dir: Path) -> None:
    _audit_path(vault_dir).write_text("not json", encoding="utf-8")
    with pytest.raises(AuditError, match="Corrupt audit log"):
        load_log(vault_dir)


def test_load_log_wrong_type_raises(vault_dir: Path) -> None:
    _audit_path(vault_dir).write_text(json.dumps({"key": "value"}), encoding="utf-8")
    with pytest.raises(AuditError, match="expected a JSON array"):
        load_log(vault_dir)


def test_record_no_details_omits_key(vault_dir: Path) -> None:
    entry = record(vault_dir, "lock", actor="alice")
    assert "details" not in entry
