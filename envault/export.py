"""Export decrypted .env contents to various formats (shell, JSON, dotenv)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List


class ExportError(Exception):
    """Raised when export operations fail."""


_ENV_LINE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")


def parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a .env file into a dict, skipping comments and blank lines."""
    if not path.exists():
        raise ExportError(f"File not found: {path}")
    result: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = _ENV_LINE_RE.match(line)
        if m:
            key, value = m.group(1), m.group(2)
            # Strip surrounding quotes if present
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            result[key] = value
    return result


def export_shell(env: Dict[str, str]) -> str:
    """Return shell export statements for all variables."""
    lines: List[str] = []
    for key, value in env.items():
        escaped = value.replace('"', '\\"')
        lines.append(f'export {key}="{escaped}"')
    return "\n".join(lines)


def export_json(env: Dict[str, str], indent: int = 2) -> str:
    """Return a JSON representation of the environment variables."""
    return json.dumps(env, indent=indent)


def export_dotenv(env: Dict[str, str]) -> str:
    """Return a canonical dotenv-formatted string."""
    lines: List[str] = []
    for key, value in env.items():
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines)


def export_file(source: Path, dest: Path, fmt: str = "dotenv") -> None:
    """Parse *source* and write the chosen format to *dest*."""
    env = parse_env_file(source)
    formatters = {
        "shell": export_shell,
        "json": export_json,
        "dotenv": export_dotenv,
    }
    if fmt not in formatters:
        raise ExportError(f"Unknown format '{fmt}'. Choose from: {', '.join(formatters)}")
    dest.write_text(formatters[fmt](env), encoding="utf-8")
