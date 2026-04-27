"""CLI sub-commands for envault export functionality."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.export import ExportError, export_file, parse_env_file, export_shell, export_json, export_dotenv


def cmd_export(args: argparse.Namespace) -> None:
    """Decrypt and export the .env file to stdout or a destination file."""
    source = Path(args.source)
    fmt: str = args.format

    try:
        env = parse_env_file(source)
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    formatters = {
        "shell": export_shell,
        "json": export_json,
        "dotenv": export_dotenv,
    }

    if fmt not in formatters:
        print(f"error: Unknown format '{fmt}'. Choose from: {', '.join(formatters)}", file=sys.stderr)
        sys.exit(1)

    output = formatters[fmt](env)

    if args.output:
        dest = Path(args.output)
        try:
            dest.write_text(output, encoding="utf-8")
            print(f"Exported {len(env)} variable(s) to {dest} [{fmt}]")
        except OSError as exc:
            print(f"error: Could not write to {dest}: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output)


def build_export_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'export' sub-command on an existing subparsers object."""
    parser = subparsers.add_parser(
        "export",
        help="Export decrypted .env variables to a chosen format",
    )
    parser.add_argument(
        "source",
        help="Path to the decrypted .env file",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["dotenv", "shell", "json"],
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Write output to FILE instead of stdout",
        metavar="FILE",
    )
    parser.set_defaults(func=cmd_export)
