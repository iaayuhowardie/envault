"""Watch .env file for changes and auto-lock on modification."""

import hashlib
import time
from pathlib import Path
from typing import Callable, Optional

from envault.audit import record
from envault.vault import load_meta, VaultError


class WatchError(Exception):
    """Raised when the watcher encounters an unrecoverable error."""


def _file_digest(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def watch(
    vault_dir: Path,
    on_change: Callable[[Path], None],
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """
    Poll *vault_dir/.env* and call *on_change* whenever the file is modified.

    Parameters
    ----------
    vault_dir:      Directory that contains the .env file and vault metadata.
    on_change:      Callback invoked with the .env Path when a change is detected.
    interval:       Polling interval in seconds.
    max_iterations: Stop after this many iterations (useful for testing).
    """
    meta = load_meta(vault_dir)
    env_path = vault_dir / meta.get("env_file", ".env")

    if not env_path.exists():
        raise WatchError(f"env file not found: {env_path}")

    last_digest = _file_digest(env_path)
    iterations = 0

    while True:
        if max_iterations is not None and iterations >= max_iterations:
            break
        time.sleep(interval)
        iterations += 1

        if not env_path.exists():
            raise WatchError(f"env file disappeared: {env_path}")

        current_digest = _file_digest(env_path)
        if current_digest != last_digest:
            last_digest = current_digest
            record(vault_dir, "watch", {"event": "changed", "file": str(env_path)})
            on_change(env_path)
