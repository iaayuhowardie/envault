"""Sync encrypted .env vault files with remote storage backends."""

import os
import shutil
from pathlib import Path


class SyncError(Exception):
    """Raised when a sync operation fails."""


def _resolve_remote(remote_url: str) -> Path:
    """Resolve a remote URL to a local path (supports file:// and plain paths)."""
    if remote_url.startswith("file://"):
        return Path(remote_url[len("file://"):])
    return Path(remote_url)


def push(vault_dir: Path, remote_url: str) -> None:
    """Push encrypted vault files to a remote location.

    Args:
        vault_dir: Local directory containing the vault (meta + .enc files).
        remote_url: Destination path or file:// URL.

    Raises:
        SyncError: If the vault directory is missing or the push fails.
    """
    if not vault_dir.is_dir():
        raise SyncError(f"Vault directory not found: {vault_dir}")

    remote_path = _resolve_remote(remote_url)
    try:
        remote_path.mkdir(parents=True, exist_ok=True)
        for item in vault_dir.iterdir():
            dest = remote_path / item.name
            shutil.copy2(item, dest)
    except OSError as exc:
        raise SyncError(f"Push failed: {exc}") from exc


def pull(remote_url: str, vault_dir: Path) -> None:
    """Pull encrypted vault files from a remote location.

    Args:
        remote_url: Source path or file:// URL.
        vault_dir: Local directory to receive the vault files.

    Raises:
        SyncError: If the remote location is missing or the pull fails.
    """
    remote_path = _resolve_remote(remote_url)
    if not remote_path.is_dir():
        raise SyncError(f"Remote location not found: {remote_path}")

    try:
        vault_dir.mkdir(parents=True, exist_ok=True)
        for item in remote_path.iterdir():
            dest = vault_dir / item.name
            shutil.copy2(item, dest)
    except OSError as exc:
        raise SyncError(f"Pull failed: {exc}") from exc


def status(vault_dir: Path, remote_url: str) -> dict:
    """Compare local vault files against remote.

    Returns a dict with keys 'local_only', 'remote_only', and 'in_sync'.
    """
    remote_path = _resolve_remote(remote_url)

    local_files = {f.name for f in vault_dir.iterdir()} if vault_dir.is_dir() else set()
    remote_files = {f.name for f in remote_path.iterdir()} if remote_path.is_dir() else set()

    return {
        "local_only": sorted(local_files - remote_files),
        "remote_only": sorted(remote_files - local_files),
        "in_sync": sorted(local_files & remote_files),
    }
