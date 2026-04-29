"""CLI commands for managing envault profiles."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.profile import (
    ProfileError,
    apply_profile,
    create_profile,
    delete_profile,
    load_profiles,
)


def cmd_profile(args: argparse.Namespace) -> None:
    vault_dir = Path(args.vault_dir) if hasattr(args, "vault_dir") else Path(".")

    if args.profile_cmd == "create":
        try:
            create_profile(vault_dir, args.name, args.fingerprints)
            print(f"Profile '{args.name}' created with {len(args.fingerprints)} recipient(s).")
        except ProfileError as exc:
            raise SystemExit(f"error: {exc}") from exc

    elif args.profile_cmd == "delete":
        try:
            delete_profile(vault_dir, args.name)
            print(f"Profile '{args.name}' deleted.")
        except ProfileError as exc:
            raise SystemExit(f"error: {exc}") from exc

    elif args.profile_cmd == "apply":
        try:
            apply_profile(vault_dir, args.name)
            print(f"Profile '{args.name}' applied to vault recipients.")
        except ProfileError as exc:
            raise SystemExit(f"error: {exc}") from exc

    elif args.profile_cmd == "list":
        profiles = load_profiles(vault_dir)
        if not profiles:
            print("No profiles defined.")
        else:
            for pname, fps in sorted(profiles.items()):
                print(f"{pname}: {', '.join(fps)}")


def build_profile_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("profile", help="Manage recipient profiles.")
    p.add_argument("--vault-dir", default=".", metavar="DIR")
    sub = p.add_subparsers(dest="profile_cmd", required=True)

    pc = sub.add_parser("create", help="Create a named profile.")
    pc.add_argument("name", help="Profile name.")
    pc.add_argument("fingerprints", nargs="+", help="GPG fingerprints.")

    pd = sub.add_parser("delete", help="Delete a named profile.")
    pd.add_argument("name", help="Profile name.")

    pa = sub.add_parser("apply", help="Apply a profile to vault recipients.")
    pa.add_argument("name", help="Profile name.")

    sub.add_parser("list", help="List all profiles.")

    p.set_defaults(func=cmd_profile)
