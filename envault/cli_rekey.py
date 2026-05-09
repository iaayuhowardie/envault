"""CLI sub-commands for the re-key feature."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.rekey import RekeyError, rekey


def cmd_rekey(args: argparse.Namespace) -> None:
    """Handle the ``envault rekey`` sub-command."""
    vault_dir = Path(args.vault_dir)
    new_recipients = args.recipients if args.recipients else None

    try:
        rekey(
            vault_dir=vault_dir,
            new_recipients=new_recipients,
            passphrase=args.passphrase,
        )
    except RekeyError as exc:
        print(f"rekey error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if new_recipients:
        print(f"Vault re-keyed for {len(new_recipients)} recipient(s).")
    else:
        print("Vault re-encrypted under existing recipients.")


def build_rekey_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "rekey",
        help="Re-encrypt the vault, optionally changing recipients.",
    )
    parser.add_argument(
        "--vault-dir",
        default=".",
        metavar="DIR",
        help="Path to the vault directory (default: current directory).",
    )
    parser.add_argument(
        "--recipients",
        nargs="+",
        metavar="FINGERPRINT",
        help="New GPG fingerprints to encrypt for. Omit to reuse existing.",
    )
    parser.add_argument(
        "--passphrase",
        default=None,
        metavar="PASSPHRASE",
        help="Passphrase for decryption (if key is passphrase-protected).",
    )
    parser.set_defaults(func=cmd_rekey)
    return parser
