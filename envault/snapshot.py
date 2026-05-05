"""Snapshot support: capture and restore named .env snapshots."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List

SNAPSHOTS_DIR = ".envault_snapshots"


class SnapshotError(Exception):
    """Raised for snapshot-related failures."""


def _snapshots_path(vault_dir: Path) -> Path:
    return vault_dir / SNAPSHOTS_DIR


def list_snapshots(vault_dir: Path) -> List[str]:
    """Return sorted list of snapshot names stored in *vault_dir*."""
    snap_dir = _snapshots_path(vault_dir)
    if not snap_dir.exists():
        return []
    return sorted(p.name for p in snap_dir.iterdir() if p.is_dir())


def create_snapshot(vault_dir: Path, name: str, env_file: Path) -> Path:
    """Copy *env_file* into a named snapshot directory.

    Returns the path to the stored snapshot file.
    Raises SnapshotError if the name is empty, already exists, or the source
    file is missing.
    """
    if not name or not name.strip():
        raise SnapshotError("Snapshot name must not be empty.")
    if not env_file.exists():
        raise SnapshotError(f"Source file not found: {env_file}")

    snap_dir = _snapshots_path(vault_dir) / name
    if snap_dir.exists():
        raise SnapshotError(f"Snapshot '{name}' already exists.")

    snap_dir.mkdir(parents=True)
    dest = snap_dir / env_file.name
    shutil.copy2(env_file, dest)

    meta = {"source": str(env_file), "filename": env_file.name}
    (snap_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    return dest


def restore_snapshot(vault_dir: Path, name: str, target: Path) -> None:
    """Overwrite *target* with the contents of snapshot *name*.

    Raises SnapshotError if the snapshot does not exist.
    """
    snap_dir = _snapshots_path(vault_dir) / name
    if not snap_dir.exists():
        raise SnapshotError(f"Snapshot '{name}' not found.")

    meta_file = snap_dir / "meta.json"
    meta: Dict[str, str] = json.loads(meta_file.read_text())
    src = snap_dir / meta["filename"]
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)


def delete_snapshot(vault_dir: Path, name: str) -> None:
    """Remove a named snapshot.

    Raises SnapshotError if the snapshot does not exist.
    """
    snap_dir = _snapshots_path(vault_dir) / name
    if not snap_dir.exists():
        raise SnapshotError(f"Snapshot '{name}' not found.")
    shutil.rmtree(snap_dir)
