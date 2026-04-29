"""Tag management for envault vaults.

Allows labelling a vault with named tags (e.g. 'production', 'staging')
so teams can quickly identify the purpose of an encrypted environment.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


class TagError(Exception):
    """Raised when a tag operation fails."""


def _tags_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "tags.json"


def load_tags(vault_dir: Path) -> List[str]:
    """Return the list of tags for *vault_dir*, or [] if none recorded."""
    path = _tags_path(vault_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return list(data.get("tags", []))
    except (json.JSONDecodeError, OSError) as exc:
        raise TagError(f"Failed to read tags: {exc}") from exc


def save_tags(vault_dir: Path, tags: List[str]) -> None:
    """Persist *tags* to disk under *vault_dir*."""
    path = _tags_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps({"tags": tags}, indent=2))
    except OSError as exc:
        raise TagError(f"Failed to write tags: {exc}") from exc


def add_tag(vault_dir: Path, tag: str) -> List[str]:
    """Add *tag* to the vault.  Raises TagError if already present."""
    tag = tag.strip()
    if not tag:
        raise TagError("Tag name must not be empty.")
    tags = load_tags(vault_dir)
    if tag in tags:
        raise TagError(f"Tag '{tag}' already exists.")
    tags.append(tag)
    save_tags(vault_dir, tags)
    return tags


def remove_tag(vault_dir: Path, tag: str) -> List[str]:
    """Remove *tag* from the vault.  Raises TagError if not found."""
    tags = load_tags(vault_dir)
    if tag not in tags:
        raise TagError(f"Tag '{tag}' not found.")
    tags.remove(tag)
    save_tags(vault_dir, tags)
    return tags


def list_tags(vault_dir: Path) -> List[str]:
    """Return sorted list of tags for *vault_dir*."""
    return sorted(load_tags(vault_dir))
