"""Pre/post lock and unlock hook support for envault."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

HOOKS_FILE = ".envault-hooks.json"


class HookError(Exception):
    """Raised when a hook fails or is misconfigured."""


def _hooks_path(vault_dir: Path) -> Path:
    return vault_dir / HOOKS_FILE


def load_hooks(vault_dir: Path) -> dict:
    """Load hooks config from vault_dir. Returns empty dict if missing."""
    import json

    p = _hooks_path(vault_dir)
    if not p.exists():
        return {}
    with p.open() as fh:
        return json.load(fh)


def save_hooks(vault_dir: Path, hooks: dict) -> None:
    """Persist hooks config to vault_dir."""
    import json

    p = _hooks_path(vault_dir)
    with p.open("w") as fh:
        json.dump(hooks, fh, indent=2)


def set_hook(vault_dir: Path, event: str, command: str) -> None:
    """Register a shell command for a lifecycle event.

    Valid events: pre_lock, post_lock, pre_unlock, post_unlock.
    """
    valid_events = {"pre_lock", "post_lock", "pre_unlock", "post_unlock"}
    if event not in valid_events:
        raise HookError(f"Unknown event '{event}'. Valid: {sorted(valid_events)}")
    if not command.strip():
        raise HookError("Hook command must not be empty.")
    hooks = load_hooks(vault_dir)
    hooks[event] = command
    save_hooks(vault_dir, hooks)


def remove_hook(vault_dir: Path, event: str) -> None:
    """Remove a registered hook for an event."""
    hooks = load_hooks(vault_dir)
    if event not in hooks:
        raise HookError(f"No hook registered for event '{event}'.")
    del hooks[event]
    save_hooks(vault_dir, hooks)


def run_hook(vault_dir: Path, event: str) -> None:
    """Execute the shell command registered for *event*, if any."""
    hooks = load_hooks(vault_dir)
    command = hooks.get(event)
    if not command:
        return
    result = subprocess.run(
        command,
        shell=True,
        cwd=str(vault_dir),
        env=os.environ.copy(),
    )
    if result.returncode != 0:
        raise HookError(
            f"Hook '{event}' exited with code {result.returncode}: {command}"
        )
