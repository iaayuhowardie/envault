"""CLI commands for configuring and inspecting envault rate limiting."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.ratelimit import configure, load_ratelimit, reset, RateLimitError


def cmd_ratelimit(args: argparse.Namespace) -> None:
    vault_dir = Path(args.vault_dir) if hasattr(args, "vault_dir") and args.vault_dir else Path.cwd()

    if args.ratelimit_cmd == "set":
        try:
            configure(vault_dir, max_attempts=args.max_attempts, window=args.window)
            print(f"Rate limit set: {args.max_attempts} attempts per {args.window}s.")
        except RateLimitError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    elif args.ratelimit_cmd == "show":
        try:
            state = load_ratelimit(vault_dir)
        except RateLimitError as exc:
            raise SystemExit(f"Error: {exc}") from exc
        print(f"max_attempts : {state['max_attempts']}")
        print(f"window       : {state['window']}s")
        print(f"recent_hits  : {len(state['attempts'])}")

    elif args.ratelimit_cmd == "reset":
        try:
            reset(vault_dir)
            print("Rate limit counter reset.")
        except RateLimitError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    else:
        raise SystemExit(f"Unknown sub-command: {args.ratelimit_cmd}")


def build_ratelimit_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("ratelimit", help="Configure unlock rate limiting")
    sub = p.add_subparsers(dest="ratelimit_cmd", required=True)

    # set
    s = sub.add_parser("set", help="Set rate limit parameters")
    s.add_argument("--max-attempts", type=int, default=5, dest="max_attempts",
                   help="Max unlock attempts before lockout (default: 5)")
    s.add_argument("--window", type=int, default=60,
                   help="Time window in seconds (default: 60)")

    # show
    sub.add_parser("show", help="Show current rate limit configuration and hit count")

    # reset
    sub.add_parser("reset", help="Reset the attempt counter")

    p.set_defaults(func=cmd_ratelimit)
