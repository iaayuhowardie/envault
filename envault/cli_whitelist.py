"""CLI commands for managing the envault whitelist."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.whitelist import WhitelistError, allow, deny, is_allowed, load_whitelist


def cmd_whitelist(args: argparse.Namespace) -> None:
    vault_dir = Path(args.vault_dir)

    if args.whitelist_cmd == "add":
        try:
            entries = allow(vault_dir, args.fingerprint)
            print(f"Whitelisted: {args.fingerprint.strip().upper()}")
            print(f"Total approved fingerprints: {len(entries)}")
        except WhitelistError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    elif args.whitelist_cmd == "remove":
        try:
            entries = deny(vault_dir, args.fingerprint)
            print(f"Removed from whitelist: {args.fingerprint.strip().upper()}")
            print(f"Remaining approved fingerprints: {len(entries)}")
        except WhitelistError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    elif args.whitelist_cmd == "check":
        try:
            allowed = is_allowed(vault_dir, args.fingerprint)
            status = "ALLOWED" if allowed else "DENIED"
            print(f"{args.fingerprint.strip().upper()}: {status}")
        except WhitelistError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    elif args.whitelist_cmd == "list":
        try:
            entries = load_whitelist(vault_dir)
        except WhitelistError as exc:
            raise SystemExit(f"Error: {exc}") from exc
        if not entries:
            print("Whitelist is empty (all fingerprints allowed).")
        else:
            for fp in entries:
                print(fp)
    else:
        raise SystemExit("Unknown whitelist sub-command.")


def build_whitelist_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser("whitelist", help="Manage approved GPG fingerprints.")
    p.add_argument("--vault-dir", default=".", help="Path to the vault directory.")
    sub = p.add_subparsers(dest="whitelist_cmd", required=True)

    add_p = sub.add_parser("add", help="Approve a fingerprint.")
    add_p.add_argument("fingerprint", help="GPG fingerprint to approve.")

    rm_p = sub.add_parser("remove", help="Revoke a fingerprint.")
    rm_p.add_argument("fingerprint", help="GPG fingerprint to revoke.")

    chk_p = sub.add_parser("check", help="Check whether a fingerprint is allowed.")
    chk_p.add_argument("fingerprint", help="GPG fingerprint to check.")

    sub.add_parser("list", help="List all approved fingerprints.")

    p.set_defaults(func=cmd_whitelist)
    return p
