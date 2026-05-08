"""CLI commands for managing GPG fingerprint trust levels."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.trust import TRUST_LEVELS, TrustError, get_trust, load_trust, remove_trust, set_trust


def cmd_trust(args: argparse.Namespace) -> None:
    vault_dir = Path(args.vault_dir)

    if args.trust_command == "set":
        try:
            set_trust(vault_dir, args.fingerprint, args.level)
            print(f"Trust level '{args.level}' set for {args.fingerprint}")
        except TrustError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    elif args.trust_command == "get":
        try:
            level = get_trust(vault_dir, args.fingerprint)
        except TrustError as exc:
            raise SystemExit(f"Error: {exc}") from exc
        if level is None:
            print(f"{args.fingerprint}: (not set)")
        else:
            print(f"{args.fingerprint}: {level}")

    elif args.trust_command == "remove":
        try:
            remove_trust(vault_dir, args.fingerprint)
            print(f"Removed trust entry for {args.fingerprint}")
        except TrustError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    elif args.trust_command == "list":
        try:
            trust = load_trust(vault_dir)
        except TrustError as exc:
            raise SystemExit(f"Error: {exc}") from exc
        if not trust:
            print("No trust entries found.")
        else:
            for fp, lvl in trust.items():
                print(f"  {fp}: {lvl}")


def build_trust_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    trust_parser = subparsers.add_parser("trust", help="Manage fingerprint trust levels")
    trust_parser.add_argument("--vault-dir", default=".", help="Path to vault directory")
    trust_sub = trust_parser.add_subparsers(dest="trust_command", required=True)

    p_set = trust_sub.add_parser("set", help="Set trust level for a fingerprint")
    p_set.add_argument("fingerprint", help="GPG fingerprint")
    p_set.add_argument("level", choices=TRUST_LEVELS, help="Trust level")

    p_get = trust_sub.add_parser("get", help="Get trust level for a fingerprint")
    p_get.add_argument("fingerprint", help="GPG fingerprint")

    p_rm = trust_sub.add_parser("remove", help="Remove trust entry for a fingerprint")
    p_rm.add_argument("fingerprint", help="GPG fingerprint")

    trust_sub.add_parser("list", help="List all trust entries")

    trust_parser.set_defaults(func=cmd_trust)
