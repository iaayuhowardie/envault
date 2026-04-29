"""Tests for envault.template and envault.cli_template."""

from __future__ import annotations

import argparse
import pytest
from pathlib import Path

from envault.template import (
    TemplateError,
    load_templates,
    register_template,
    render_template,
    save_templates,
)
from envault.cli_template import build_template_parser, cmd_template


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_template_parser(sub)
    return p


def _write_template(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


# --- unit tests for template.py ---

def test_load_templates_missing_returns_empty(vault_dir: Path) -> None:
    assert load_templates(vault_dir) == {}


def test_register_template_stores_entry(vault_dir: Path) -> None:
    register_template(vault_dir, "dev", ".env.dev.template")
    templates = load_templates(vault_dir)
    assert templates["dev"] == ".env.dev.template"


def test_register_duplicate_template_raises(vault_dir: Path) -> None:
    register_template(vault_dir, "dev", ".env.dev.template")
    with pytest.raises(TemplateError, match="already registered"):
        register_template(vault_dir, "dev", ".env.other.template")


def test_register_empty_name_raises(vault_dir: Path) -> None:
    with pytest.raises(TemplateError, match="must not be empty"):
        register_template(vault_dir, "", ".env.template")


def test_render_template_basic(vault_dir: Path) -> None:
    tmpl = _write_template(vault_dir / ".env.template", "DB_HOST=${DB_HOST}\n")
    result = render_template(tmpl, {"DB_HOST": "localhost"})
    assert result == "DB_HOST=localhost\n"


def test_render_template_with_default(vault_dir: Path) -> None:
    tmpl = _write_template(vault_dir / ".env.template", "PORT=${PORT:8080}\n")
    result = render_template(tmpl, {})
    assert result == "PORT=8080\n"


def test_render_template_missing_variable_raises(vault_dir: Path) -> None:
    tmpl = _write_template(vault_dir / ".env.template", "SECRET=${SECRET}\n")
    with pytest.raises(TemplateError, match="Missing required variables"):
        render_template(tmpl, {})


def test_render_template_writes_output_file(vault_dir: Path) -> None:
    tmpl = _write_template(vault_dir / ".env.template", "KEY=${KEY:val}\n")
    out = vault_dir / ".env"
    render_template(tmpl, {}, output_path=out)
    assert out.read_text() == "KEY=val\n"


def test_render_template_missing_file_raises(vault_dir: Path) -> None:
    with pytest.raises(TemplateError, match="not found"):
        render_template(vault_dir / "nonexistent.template", {})


# --- CLI tests ---

def test_build_template_parser_registers_command(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["template", "list"])
    assert args.command == "template"
    assert args.template_cmd == "list"


def test_cmd_template_list_empty(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture) -> None:
    args = parser.parse_args(["template", "list"])
    args.vault_dir = str(vault_dir)
    cmd_template(args)
    captured = capsys.readouterr()
    assert "No templates registered" in captured.out


def test_cmd_template_render_stdout(vault_dir: Path, parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture) -> None:
    tmpl = vault_dir / ".env.template"
    tmpl.write_text("APP=${APP:envault}\n")
    args = parser.parse_args(["template", "render", str(tmpl)])
    args.vault_dir = str(vault_dir)
    cmd_template(args)
    captured = capsys.readouterr()
    assert "APP=envault" in captured.out


def test_cmd_template_render_missing_var_exits(vault_dir: Path, parser: argparse.ArgumentParser) -> None:
    tmpl = vault_dir / ".env.template"
    tmpl.write_text("SECRET=${SECRET}\n")
    args = parser.parse_args(["template", "render", str(tmpl)])
    args.vault_dir = str(vault_dir)
    with pytest.raises(SystemExit):
        cmd_template(args)
