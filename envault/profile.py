"""Profile management: named sets of recipients for different environments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envault.vault import _meta_path, load_meta, save_meta


class ProfileError(Exception):
    """Raised when a profile operation fails."""


def _profiles_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "profiles.json"


def load_profiles(vault_dir: Path) -> Dict[str, List[str]]:
    """Return the profiles dict, keyed by profile name → list of fingerprints."""
    path = _profiles_path(vault_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def save_profiles(vault_dir: Path, profiles: Dict[str, List[str]]) -> None:
    """Persist profiles to disk."""
    path = _profiles_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(profiles, fh, indent=2)


def create_profile(vault_dir: Path, name: str, fingerprints: List[str]) -> None:
    """Create or overwrite a named profile."""
    if not name.strip():
        raise ProfileError("Profile name must not be empty.")
    if not fingerprints:
        raise ProfileError("A profile must contain at least one fingerprint.")
    profiles = load_profiles(vault_dir)
    profiles[name] = list(fingerprints)
    save_profiles(vault_dir, profiles)


def delete_profile(vault_dir: Path, name: str) -> None:
    """Remove a named profile."""
    profiles = load_profiles(vault_dir)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' does not exist.")
    del profiles[name]
    save_profiles(vault_dir, profiles)


def apply_profile(vault_dir: Path, name: str) -> None:
    """Replace vault recipients with those from the named profile."""
    profiles = load_profiles(vault_dir)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' does not exist.")
    meta = load_meta(vault_dir)
    meta["recipients"] = list(profiles[name])
    save_meta(vault_dir, meta)
