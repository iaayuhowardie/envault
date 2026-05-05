"""CLI commands for signing and verifying vault files."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.sign import sign_file, verify_file, SignError


def cmd_sign(args: argparse.Namespace) -> None:
    """Sign an encrypted vault file with the given GPG key."""
    file_path = Path(args.file)
    if not file_path.exists():
        raise SystemExit(f"error: file not found: {file_path}")

    try:
        sig_path = sign_file(file_path, args.fingerprint)
        print(f"Signed: {sig_path}")
    except SignError as exc:
        raise SystemExit(f"error: {exc}") from exc


def cmd_verify(args: argparse.Namespace) -> None:
    """Verify the detached signature of a vault file."""
    file_path = Path(args.file)
    sig_path = Path(args.sig) if args.sig else None

    try:
        fingerprint = verify_file(file_path, sig_path)
        print(f"Valid signature by: {fingerprint}")
    except SignError as exc:
        raise SystemExit(f"error: {exc}") from exc


def build_sign_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *sign* and *verify* sub-commands."""
    # sign
    p_sign = subparsers.add_parser("sign", help="Sign an encrypted vault file.")
    p_sign.add_argument("file", help="Path to the encrypted file.")
    p_sign.add_argument(
        "--fingerprint", required=True, help="GPG fingerprint of the signing key."
    )
    p_sign.set_defaults(func=cmd_sign)

    # verify
    p_verify = subparsers.add_parser("verify", help="Verify the signature of a vault file.")
    p_verify.add_argument("file", help="Path to the encrypted file.")
    p_verify.add_argument("--sig", default=None, help="Path to the .sig file (optional).")
    p_verify.set_defaults(func=cmd_verify)
