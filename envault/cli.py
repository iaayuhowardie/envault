"""Main CLI entry-point for envault."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.vault import VaultError, add_recipient, init_vault, remove_recipient
from envault.crypto import GPGError, decrypt_file, encrypt_file
from envault.audit import record as audit_record
from envault.cli_export import build_export_parser
from envault.cli_watch import build_watch_parser
from envault.cli_profile import build_profile_parser
from envault.cli_tags import build_tags_parser
from envault.cli_hooks import build_hooks_parser
from envault.cli_template import build_template_parser
from envault.cli_acl import build_acl_parser
from envault.cli_sign import build_sign_parser
from envault.cli_search import build_search_parser
from envault.cli_quota import build_quota_parser

DEFAULT_ENV = ".env"
DEFAULT_VAULT = ".envault"


def cmd_init(args: argparse.Namespace) -> None:
    try:
        init_vault(
            vault_dir=args.vault_dir,
            env_file=args.env_file,
            recipients=args.recipients,
        )
        print(f"Vault initialised in {args.vault_dir}")
    except (VaultError, GPGError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def cmd_add(args: argparse.Namespace) -> None:
    try:
        add_recipient(args.vault_dir, args.fingerprint)
        audit_record(args.vault_dir, "add_recipient", {"fingerprint": args.fingerprint})
        print(f"Added recipient {args.fingerprint}")
    except VaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def cmd_remove(args: argparse.Namespace) -> None:
    try:
        remove_recipient(args.vault_dir, args.fingerprint)
        audit_record(args.vault_dir, "remove_recipient", {"fingerprint": args.fingerprint})
        print(f"Removed recipient {args.fingerprint}")
    except VaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def cmd_lock(args: argparse.Namespace) -> None:
    try:
        encrypt_file(
            src=args.env_file,
            dest=args.encrypted_file,
            recipients=args.recipients or [],
            vault_dir=args.vault_dir,
        )
        audit_record(args.vault_dir, "lock", {})
        print(f"Locked {args.env_file} -> {args.encrypted_file}")
    except (VaultError, GPGError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def cmd_unlock(args: argparse.Namespace) -> None:
    try:
        decrypt_file(src=args.encrypted_file, dest=args.env_file)
        audit_record(args.vault_dir, "unlock", {})
        print(f"Unlocked {args.encrypted_file} -> {args.env_file}")
    except GPGError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def build_parser(vault_dir: str = DEFAULT_VAULT, env_file: str = DEFAULT_ENV) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="envault", description="Encrypt and sync .env files")
    sub = p.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialise a new vault")
    p_init.add_argument("--vault-dir", default=vault_dir)
    p_init.add_argument("--env-file", default=env_file)
    p_init.add_argument("recipients", nargs="+")
    p_init.set_defaults(func=cmd_init)

    # add
    p_add = sub.add_parser("add", help="Add a recipient")
    p_add.add_argument("--vault-dir", default=vault_dir)
    p_add.add_argument("fingerprint")
    p_add.set_defaults(func=cmd_add)

    # remove
    p_rm = sub.add_parser("remove", help="Remove a recipient")
    p_rm.add_argument("--vault-dir", default=vault_dir)
    p_rm.add_argument("fingerprint")
    p_rm.set_defaults(func=cmd_remove)

    # lock
    p_lock = sub.add_parser("lock", help="Encrypt .env file")
    p_lock.add_argument("--vault-dir", default=vault_dir)
    p_lock.add_argument("--env-file", default=env_file)
    p_lock.add_argument("--encrypted-file", default=f"{env_file}.gpg")
    p_lock.add_argument("--recipients", nargs="*")
    p_lock.set_defaults(func=cmd_lock)

    # unlock
    p_unlock = sub.add_parser("unlock", help="Decrypt .env file")
    p_unlock.add_argument("--vault-dir", default=vault_dir)
    p_unlock.add_argument("--env-file", default=env_file)
    p_unlock.add_argument("--encrypted-file", default=f"{env_file}.gpg")
    p_unlock.set_defaults(func=cmd_unlock)

    build_export_parser(sub, vault_dir=vault_dir)
    build_watch_parser(sub, vault_dir=vault_dir)
    build_profile_parser(sub, vault_dir=vault_dir)
    build_tags_parser(sub, vault_dir=vault_dir)
    build_hooks_parser(sub, vault_dir=vault_dir)
    build_template_parser(sub, vault_dir=vault_dir)
    build_acl_parser(sub, vault_dir=vault_dir)
    build_sign_parser(sub, vault_dir=vault_dir)
    build_search_parser(sub, vault_dir=vault_dir)
    build_quota_parser(sub, vault_dir=vault_dir)

    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
