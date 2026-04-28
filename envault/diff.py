"""Diff utility for comparing decrypted .env files against a reference."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from envault.export import parse_env_file, ExportError


class DiffError(Exception):
    """Raised when a diff operation fails."""


@dataclass
class DiffResult:
    added: List[str] = field(default_factory=list)      # keys only in right
    removed: List[str] = field(default_factory=list)    # keys only in left
    changed: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, old, new)
    unchanged: List[str] = field(default_factory=list)  # keys identical in both

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def diff_env_files(left_path: str, right_path: str) -> DiffResult:
    """Compare two .env files and return a DiffResult.

    Args:
        left_path: Path to the baseline .env file.
        right_path: Path to the updated .env file.

    Returns:
        A DiffResult describing the differences.

    Raises:
        DiffError: If either file cannot be read or parsed.
    """
    for path in (left_path, right_path):
        if not os.path.exists(path):
            raise DiffError(f"File not found: {path}")

    try:
        left: Dict[str, str] = parse_env_file(left_path)
        right: Dict[str, str] = parse_env_file(right_path)
    except ExportError as exc:
        raise DiffError(str(exc)) from exc

    result = DiffResult()

    all_keys = set(left) | set(right)
    for key in sorted(all_keys):
        in_left = key in left
        in_right = key in right
        if in_left and in_right:
            if left[key] == right[key]:
                result.unchanged.append(key)
            else:
                result.changed.append((key, left[key], right[key]))
        elif in_left:
            result.removed.append(key)
        else:
            result.added.append(key)

    return result


def format_diff(result: DiffResult, redact: bool = True) -> str:
    """Render a DiffResult as a human-readable string.

    Args:
        result: The DiffResult to format.
        redact: If True, mask actual values with '***'.

    Returns:
        A formatted multi-line string.
    """
    lines: List[str] = []
    for key in result.added:
        lines.append(f"+ {key}")
    for key in result.removed:
        lines.append(f"- {key}")
    for key, old, new in result.changed:
        old_val = "***" if redact else old
        new_val = "***" if redact else new
        lines.append(f"~ {key}: {old_val} -> {new_val}")
    if not lines:
        lines.append("(no changes)")
    return "\n".join(lines)
