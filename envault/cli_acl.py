"""CLI sub-commands for ACL management."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.acl import ACLError, get_role, list_acl, remove_role, set_role


def cmd_acl(args: argparse.Namespace) -> None:
    """Dispatch ACL sub-commands."""
    vault_dir = Path(args.vault_dir)

    if args.acl_cmd == "set":
        try:
            set_role(vault_dir, args.fingerprint, args.role)
            print(f"Set role '{args.role}' for {args.fingerprint}.")
        except ACLError as exc:
            raise SystemExit(f"acl set error: {exc}") from exc

    elif args.acl_cmd == "remove":
        try:
            remove_role(vault_dir, args.fingerprint)
            print(f"Removed {args.fingerprint} from ACL.")
        except ACLError as exc:
            raise SystemExit(f"acl remove error: {exc}") from exc

    elif args.acl_cmd == "get":
        role = get_role(vault_dir, args.fingerprint)
        if role is None:
            print(f"{args.fingerprint}: (not in ACL)")
        else:
            print(f"{args.fingerprint}: {role}")

    elif args.acl_cmd == "list":
        entries = list_acl(vault_dir)
        if not entries:
            print("ACL is empty.")
        else:
            for entry in entries:
                print(f"{entry['fingerprint']}  {entry['role']}")

    else:
        raise SystemExit(f"Unknown acl sub-command: {args.acl_cmd}")


def build_acl_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'acl' command and its sub-commands."""
    acl_parser = subparsers.add_parser("acl", help="Manage vault access control list.")
    acl_parser.add_argument(
        "--vault-dir", default=".", help="Path to the vault directory (default: .)."
    )
    acl_parser.set_defaults(func=cmd_acl)

    acl_sub = acl_parser.add_subparsers(dest="acl_cmd", required=True)

    set_p = acl_sub.add_parser("set", help="Assign a role to a fingerprint.")
    set_p.add_argument("fingerprint", help="GPG key fingerprint.")
    set_p.add_argument("role", choices=["reader", "writer", "admin"], help="Role to assign.")

    rm_p = acl_sub.add_parser("remove", help="Remove a fingerprint from the ACL.")
    rm_p.add_argument("fingerprint", help="GPG key fingerprint to remove.")

    get_p = acl_sub.add_parser("get", help="Show role for a fingerprint.")
    get_p.add_argument("fingerprint", help="GPG key fingerprint.")

    acl_sub.add_parser("list", help="List all ACL entries.")
