"""CLI interface for the envault search feature."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.search import SearchError, format_search_results, search_keys


def cmd_search(args: argparse.Namespace) -> None:
    """Execute the search sub-command."""
    env_files = [Path(f) for f in args.files]
    missing = [str(p) for p in env_files if not p.exists()]
    if missing:
        print(f"error: file(s) not found: {', '.join(missing)}", file=sys.stderr)
        raise SystemExit(1)

    try:
        results = search_keys(
            env_files,
            args.pattern,
            case_sensitive=args.case_sensitive,
            value_pattern=args.value_pattern,
        )
    except SearchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    output = format_search_results(results)
    print(output)

    if args.count:
        print(f"\n{len(results)} match(es) found.")


def build_search_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the 'search' sub-command."""
    parser = subparsers.add_parser(
        "search",
        help="Search for keys across one or more .env files.",
    )
    parser.add_argument(
        "pattern",
        help="Regex pattern to match against key names.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env file(s) to search.",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Enable case-sensitive matching (default: case-insensitive).",
    )
    parser.add_argument(
        "--value-pattern",
        default=None,
        metavar="PATTERN",
        help="Additional regex pattern matched against values.",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        default=False,
        help="Print total match count after results.",
    )
    parser.set_defaults(func=cmd_search)
    return parser
