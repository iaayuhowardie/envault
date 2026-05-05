"""Search and filter keys across .env files and vault metadata."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional


class SearchError(Exception):
    """Raised when a search operation fails."""


class SearchResult(NamedTuple):
    file: str
    key: str
    value: str
    line_number: int


def _parse_env_lines(path: Path) -> List[tuple[int, str, str]]:
    """Return (lineno, key, value) tuples from an env file."""
    results: List[tuple[int, str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SearchError(f"Cannot read file {path}: {exc}") from exc
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        results.append((lineno, key.strip(), value.strip()))
    return results


def search_keys(
    env_files: List[Path],
    pattern: str,
    *,
    case_sensitive: bool = False,
    value_pattern: Optional[str] = None,
) -> List[SearchResult]:
    """Search for keys matching *pattern* across multiple env files.

    Args:
        env_files: Paths to .env files to search.
        pattern: Regex pattern matched against key names.
        case_sensitive: Whether the key match is case-sensitive.
        value_pattern: Optional regex pattern matched against values.

    Returns:
        List of :class:`SearchResult` instances.
    """
    if not env_files:
        raise SearchError("No env files provided to search.")

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        key_re = re.compile(pattern, flags)
    except re.error as exc:
        raise SearchError(f"Invalid key pattern: {exc}") from exc

    val_re: Optional[re.Pattern[str]] = None
    if value_pattern:
        try:
            val_re = re.compile(value_pattern, flags)
        except re.error as exc:
            raise SearchError(f"Invalid value pattern: {exc}") from exc

    results: List[SearchResult] = []
    for path in env_files:
        for lineno, key, value in _parse_env_lines(path):
            if not key_re.search(key):
                continue
            if val_re and not val_re.search(value):
                continue
            results.append(SearchResult(file=str(path), key=key, value=value, line_number=lineno))
    return results


def format_search_results(results: List[SearchResult]) -> str:
    """Format search results as a human-readable string."""
    if not results:
        return "No matches found."
    lines: List[str] = []
    current_file = None
    for r in results:
        if r.file != current_file:
            lines.append(f"\n{r.file}")
            current_file = r.file
        lines.append(f"  {r.line_number:4d}  {r.key}={r.value}")
    return "\n".join(lines).lstrip("\n")
