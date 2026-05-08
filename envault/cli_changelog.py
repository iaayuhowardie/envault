"""CLI sub-commands for the envault changelog feature."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.changelog import ChangelogError, format_changelog, load_changelog, record_change


def cmd_changelog(args: argparse.Namespace) -> None:
    """Dispatch changelog sub-commands."""
    vault_dir = Path(args.vault_dir)

    if args.changelog_cmd == "show":
        try:
            entries = load_changelog(vault_dir)
        except ChangelogError as exc:
            print(f"error: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        print(format_changelog(entries))

    elif args.changelog_cmd == "record":
        try:
            entry = record_change(
                vault_dir,
                action=args.action,
                fingerprint=args.fingerprint,
                detail=args.detail or "",
            )
        except ChangelogError as exc:
            print(f"error: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        print(f"Recorded: [{entry['timestamp']}] {entry['action']} by {entry['fingerprint']}")

    else:
        print(f"Unknown changelog command: {args.changelog_cmd}", file=sys.stderr)
        raise SystemExit(1)


def build_changelog_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the 'changelog' command and its sub-commands."""
    parser = subparsers.add_parser("changelog", help="View or record vault changelog entries")
    parser.add_argument(
        "--vault-dir", default=".", dest="vault_dir", help="Path to vault directory"
    )
    sub = parser.add_subparsers(dest="changelog_cmd", required=True)

    sub.add_parser("show", help="Print all changelog entries")

    rec = sub.add_parser("record", help="Manually record a changelog entry")
    rec.add_argument("action", help="Action label (e.g. lock, rotate)")
    rec.add_argument("fingerprint", help="GPG fingerprint of actor")
    rec.add_argument("--detail", default="", help="Optional detail message")

    parser.set_defaults(func=cmd_changelog)
    return parser
