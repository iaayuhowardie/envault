"""Tests for envault.hooks."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.hooks import (
    HookError,
    load_hooks,
    remove_hook,
    run_hook,
    save_hooks,
    set_hook,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_hooks_missing_returns_empty(vault_dir):
    assert load_hooks(vault_dir) == {}


def test_save_and_load_hooks_roundtrip(vault_dir):
    hooks = {"post_lock": "echo locked"}
    save_hooks(vault_dir, hooks)
    assert load_hooks(vault_dir) == hooks


def test_set_hook_stores_command(vault_dir):
    set_hook(vault_dir, "pre_lock", "make lint")
    hooks = load_hooks(vault_dir)
    assert hooks["pre_lock"] == "make lint"


def test_set_hook_invalid_event_raises(vault_dir):
    with pytest.raises(HookError, match="Unknown event"):
        set_hook(vault_dir, "on_deploy", "echo hi")


def test_set_hook_empty_command_raises(vault_dir):
    with pytest.raises(HookError, match="must not be empty"):
        set_hook(vault_dir, "post_unlock", "   ")


def test_set_hook_overwrites_existing(vault_dir):
    set_hook(vault_dir, "post_lock", "echo first")
    set_hook(vault_dir, "post_lock", "echo second")
    assert load_hooks(vault_dir)["post_lock"] == "echo second"


def test_remove_hook_deletes_entry(vault_dir):
    set_hook(vault_dir, "pre_unlock", "echo before")
    remove_hook(vault_dir, "pre_unlock")
    assert "pre_unlock" not in load_hooks(vault_dir)


def test_remove_hook_missing_event_raises(vault_dir):
    with pytest.raises(HookError, match="No hook registered"):
        remove_hook(vault_dir, "pre_lock")


def test_run_hook_no_hook_registered_does_nothing(vault_dir):
    # Should not raise even if no hook is set
    run_hook(vault_dir, "post_lock")


def test_run_hook_executes_command(vault_dir):
    marker = vault_dir / "ran.txt"
    set_hook(vault_dir, "post_unlock", f"touch {marker}")
    run_hook(vault_dir, "post_unlock")
    assert marker.exists()


def test_run_hook_nonzero_exit_raises(vault_dir):
    set_hook(vault_dir, "pre_lock", "exit 1")
    with pytest.raises(HookError, match="exited with code 1"):
        run_hook(vault_dir, "pre_lock")
