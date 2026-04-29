"""Template rendering for .env files using variable substitution."""

from __future__ import annotations

import os
import re
import json
from pathlib import Path
from typing import Dict, Optional

_TEMPLATE_SUFFIX = ".template"
_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}")


class TemplateError(Exception):
    """Raised when template rendering fails."""


def _templates_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "templates.json"


def load_templates(vault_dir: Path) -> Dict[str, str]:
    """Load registered template paths from the vault metadata."""
    path = _templates_path(vault_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_templates(vault_dir: Path, templates: Dict[str, str]) -> None:
    """Persist template registry to disk."""
    path = _templates_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(templates, indent=2))


def register_template(vault_dir: Path, name: str, template_path: str) -> None:
    """Register a named template file in the vault."""
    if not name:
        raise TemplateError("Template name must not be empty.")
    templates = load_templates(vault_dir)
    if name in templates:
        raise TemplateError(f"Template '{name}' is already registered.")
    templates[name] = template_path
    save_templates(vault_dir, templates)


def render_template(
    template_path: Path,
    variables: Dict[str, str],
    output_path: Optional[Path] = None,
) -> str:
    """Render a .env template by substituting ${VAR} or ${VAR:default} tokens.

    Returns the rendered content as a string. If *output_path* is provided,
    also writes the result to that file.
    """
    if not template_path.exists():
        raise TemplateError(f"Template file not found: {template_path}")

    content = template_path.read_text()
    missing: list[str] = []

    def _replace(match: re.Match) -> str:
        var_name = match.group(1)
        default = match.group(2)
        value = variables.get(var_name) or os.environ.get(var_name)
        if value is not None:
            return value
        if default is not None:
            return default
        missing.append(var_name)
        return match.group(0)

    rendered = _VAR_PATTERN.sub(_replace, content)

    if missing:
        raise TemplateError(
            f"Missing required variables with no defaults: {', '.join(missing)}"
        )

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)

    return rendered
