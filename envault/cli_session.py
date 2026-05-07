"""CLI commands for session management."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.session import (
    SessionError,
    open_session,
    close_session,
    is_session_active,
    get_active_fingerprint,
)

_DEFAULT_VAULT = Path(".")


def cmd_session(args: argparse.Namespace) -> None:
    vault_dir = Path(getattr(args, "vault_dir", "."))

    if args.session_cmd == "start":
        try:
            session = open_session(vault_dir, args.fingerprint, args.ttl)
            print(f"Session started for {session['fingerprint']}")
            print(f"Expires at: {session['expires_at']:.0f}")
        except SessionError as exc:
            raise SystemExit(f"error: {exc}") from exc

    elif args.session_cmd == "stop":
        close_session(vault_dir)
        print("Session closed.")

    elif args.session_cmd == "status":
        if is_session_active(vault_dir):
            fp = get_active_fingerprint(vault_dir)
            print(f"Active session: {fp}")
        else:
            print("No active session.")

    else:
        raise SystemExit(f"Unknown session subcommand: {args.session_cmd}")


def build_session_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser("session", help="Manage unlock sessions")
    sub = p.add_subparsers(dest="session_cmd", required=True)

    start = sub.add_parser("start", help="Open a new session")
    start.add_argument("fingerprint", help="GPG fingerprint to associate with session")
    start.add_argument("--ttl", type=int, default=3600, help="Session TTL in seconds (default: 3600)")

    sub.add_parser("stop", help="Close the current session")
    sub.add_parser("status", help="Show session status")

    p.set_defaults(func=cmd_session)
    return p
