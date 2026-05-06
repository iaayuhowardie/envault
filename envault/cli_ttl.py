"""CLI commands for managing vault TTL (time-to-live)."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.ttl import TTLError, clear_ttl, get_expiry, is_expired, set_ttl


def cmd_ttl(args: argparse.Namespace) -> None:
    """Dispatch TTL sub-commands."""
    vault_dir = Path(args.vault_dir)

    if args.ttl_command == "set":
        try:
            set_ttl(vault_dir, args.seconds)
            print(f"TTL set to {args.seconds} seconds.")
        except TTLError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    elif args.ttl_command == "status":
        try:
            expiry = get_expiry(vault_dir)
        except TTLError as exc:
            raise SystemExit(f"Error: {exc}") from exc
        if expiry is None:
            print("No TTL configured for this vault.")
        else:
            expired = is_expired(vault_dir)
            state = "EXPIRED" if expired else "active"
            print(f"Expires at: {expiry.isoformat()}  [{state}]")

    elif args.ttl_command == "clear":
        try:
            clear_ttl(vault_dir)
            print("TTL cleared.")
        except TTLError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    else:
        raise SystemExit(f"Unknown ttl command: {args.ttl_command}")


def build_ttl_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'ttl' command and its sub-commands."""
    ttl_parser = subparsers.add_parser("ttl", help="Manage vault TTL")
    ttl_parser.add_argument(
        "--vault-dir", default=".", dest="vault_dir", help="Path to vault directory"
    )
    ttl_parser.set_defaults(func=cmd_ttl)

    ttl_sub = ttl_parser.add_subparsers(dest="ttl_command", required=True)

    set_p = ttl_sub.add_parser("set", help="Set TTL in seconds")
    set_p.add_argument("seconds", type=int, help="TTL duration in seconds")

    ttl_sub.add_parser("status", help="Show current TTL and expiry")
    ttl_sub.add_parser("clear", help="Remove TTL from vault")
