"""CLI entry-points for envault vault management commands."""

from __future__ import annotations

import argparse
import sys

from .vault import VaultError, add_recipient, load_meta, lock, remove_recipient, unlock
from .crypto import GPGError, list_keys


def cmd_init(args: argparse.Namespace) -> int:
    """Initialise a new vault in the current directory."""
    from .vault import save_meta

    meta = load_meta(".")
    save_meta(meta, ".")
    print("Vault initialised (.envault.json created).")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    """Add a recipient fingerprint to the vault."""
    try:
        add_recipient(args.fingerprint)
        print(f"Added recipient: {args.fingerprint}")
        return 0
    except VaultError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_remove(args: argparse.Namespace) -> int:
    """Remove a recipient fingerprint from the vault."""
    try:
        remove_recipient(args.fingerprint)
        print(f"Removed recipient: {args.fingerprint}")
        return 0
    except VaultError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_lock(args: argparse.Namespace) -> int:
    """Encrypt the .env file for all recipients."""
    try:
        out = lock(".")
        print(f"Locked → {out}")
        return 0
    except (VaultError, GPGError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_unlock(args: argparse.Namespace) -> int:
    """Decrypt the encrypted file to .env."""
    try:
        out = unlock(".")
        print(f"Unlocked → {out}")
        return 0
    except (VaultError, GPGError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    """List GPG keys available in the local keyring."""
    try:
        keys = list_keys()
        if not keys:
            print("No GPG keys found.")
        for key in keys:
            print(f"  {key}")
        return 0
    except GPGError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault", description="Encrypt and sync .env files using GPG."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialise a new vault")

    p_add = sub.add_parser("add", help="Add a GPG recipient")
    p_add.add_argument("fingerprint", help="GPG key fingerprint")

    p_rm = sub.add_parser("remove", help="Remove a GPG recipient")
    p_rm.add_argument("fingerprint", help="GPG key fingerprint")

    sub.add_parser("lock", help="Encrypt .env for all recipients")
    sub.add_parser("unlock", help="Decrypt .env.gpg to .env")
    sub.add_parser("list", help="List available GPG keys")

    return parser


COMMANDS = {
    "init": cmd_init,
    "add": cmd_add,
    "remove": cmd_remove,
    "lock": cmd_lock,
    "unlock": cmd_unlock,
    "list": cmd_list,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return COMMANDS[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
