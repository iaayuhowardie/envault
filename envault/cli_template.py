"""CLI commands for envault template management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.template import TemplateError, register_template, render_template, load_templates


def cmd_template(args: argparse.Namespace) -> None:
    vault_dir = Path(args.vault_dir) if hasattr(args, "vault_dir") and args.vault_dir else Path.cwd()

    if args.template_cmd == "register":
        try:
            register_template(vault_dir, args.name, args.path)
            print(f"Template '{args.name}' registered from {args.path}.")
        except TemplateError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise SystemExit(1)

    elif args.template_cmd == "render":
        variables: dict[str, str] = {}
        for pair in args.var or []:
            if "=" not in pair:
                print(f"Error: variable must be KEY=VALUE, got '{pair}'", file=sys.stderr)
                raise SystemExit(1)
            k, v = pair.split("=", 1)
            variables[k] = v

        output_path = Path(args.output) if args.output else None
        try:
            rendered = render_template(Path(args.template), variables, output_path)
        except TemplateError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise SystemExit(1)

        if output_path is None:
            print(rendered, end="")
        else:
            print(f"Rendered template written to {output_path}.")

    elif args.template_cmd == "list":
        templates = load_templates(vault_dir)
        if not templates:
            print("No templates registered.")
        else:
            for name, path in templates.items():
                print(f"  {name}: {path}")


def build_template_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("template", help="Manage .env templates")
    sub = p.add_subparsers(dest="template_cmd", required=True)

    reg = sub.add_parser("register", help="Register a template file")
    reg.add_argument("name", help="Alias for the template")
    reg.add_argument("path", help="Path to the .env.template file")

    rend = sub.add_parser("render", help="Render a template to a .env file")
    rend.add_argument("template", help="Path to the template file")
    rend.add_argument("-o", "--output", default=None, help="Output file path (default: stdout)")
    rend.add_argument("-v", "--var", action="append", metavar="KEY=VALUE", help="Variable overrides")

    sub.add_parser("list", help="List registered templates")

    p.set_defaults(func=cmd_template)
