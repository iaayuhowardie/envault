"""Tests for envault.diff module."""

from __future__ import annotations

import os
import pytest

from envault.diff import diff_env_files, format_diff, DiffError, DiffResult


@pytest.fixture
def env_dir(tmp_path):
    return tmp_path


def _write_env(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


def test_diff_no_changes(env_dir):
    left = str(env_dir / "left.env")
    right = str(env_dir / "right.env")
    _write_env(left, "FOO=bar\nBAZ=qux\n")
    _write_env(right, "FOO=bar\nBAZ=qux\n")

    result = diff_env_files(left, right)
    assert not result.has_changes
    assert set(result.unchanged) == {"FOO", "BAZ"}


def test_diff_added_key(env_dir):
    left = str(env_dir / "left.env")
    right = str(env_dir / "right.env")
    _write_env(left, "FOO=bar\n")
    _write_env(right, "FOO=bar\nNEW=value\n")

    result = diff_env_files(left, right)
    assert result.has_changes
    assert "NEW" in result.added
    assert result.removed == []
    assert result.changed == []


def test_diff_removed_key(env_dir):
    left = str(env_dir / "left.env")
    right = str(env_dir / "right.env")
    _write_env(left, "FOO=bar\nOLD=gone\n")
    _write_env(right, "FOO=bar\n")

    result = diff_env_files(left, right)
    assert result.has_changes
    assert "OLD" in result.removed
    assert result.added == []


def test_diff_changed_key(env_dir):
    left = str(env_dir / "left.env")
    right = str(env_dir / "right.env")
    _write_env(left, "SECRET=old_value\n")
    _write_env(right, "SECRET=new_value\n")

    result = diff_env_files(left, right)
    assert result.has_changes
    assert len(result.changed) == 1
    key, old, new = result.changed[0]
    assert key == "SECRET"
    assert old == "old_value"
    assert new == "new_value"


def test_diff_missing_file_raises(env_dir):
    left = str(env_dir / "left.env")
    _write_env(left, "FOO=bar\n")
    with pytest.raises(DiffError, match="File not found"):
        diff_env_files(left, str(env_dir / "nonexistent.env"))


def test_format_diff_redacts_values(env_dir):
    left = str(env_dir / "left.env")
    right = str(env_dir / "right.env")
    _write_env(left, "SECRET=old\n")
    _write_env(right, "SECRET=new\n")

    result = diff_env_files(left, right)
    output = format_diff(result, redact=True)
    assert "old" not in output
    assert "new" not in output
    assert "***" in output


def test_format_diff_shows_values_when_not_redacted(env_dir):
    left = str(env_dir / "left.env")
    right = str(env_dir / "right.env")
    _write_env(left, "SECRET=old\n")
    _write_env(right, "SECRET=new\n")

    result = diff_env_files(left, right)
    output = format_diff(result, redact=False)
    assert "old" in output
    assert "new" in output


def test_format_diff_no_changes_message(env_dir):
    left = str(env_dir / "left.env")
    right = str(env_dir / "right.env")
    _write_env(left, "FOO=bar\n")
    _write_env(right, "FOO=bar\n")

    result = diff_env_files(left, right)
    output = format_diff(result)
    assert "(no changes)" in output
