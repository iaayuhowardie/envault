"""CLI commands for managing vault storage quotas."""

from __future__ import annotations

import argparse
import sys

from envault.quota import QuotaError, check_quota, load_quota, set_quota


def cmd_quota(args: argparse.Namespace) -> None:
    """Dispatch quota sub-commands."""
    vault_dir: str = args.vault_dir

    if args.quota_cmd == "set":
        try:
            set_quota(
                vault_dir,
                max_bytes=args.max_bytes,
                warn_threshold=args.warn_threshold,
            )
            print(
                f"Quota set: max={args.max_bytes} bytes, "
                f"warn at {int(args.warn_threshold * 100)}%"
            )
        except QuotaError as exc:
            print(f"error: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

    elif args.quota_cmd == "status":
        try:
            status = check_quota(vault_dir)
            pct = status["ratio"] * 100
            tag = " [WARNING]" if status["warning"] else ""
            print(
                f"Used: {status['used_bytes']} / {status['max_bytes']} bytes "
                f"({pct:.1f}%){tag}"
            )
        except QuotaError as exc:
            print(f"error: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

    elif args.quota_cmd == "show":
        config = load_quota(vault_dir)
        print(f"max_bytes      : {config['max_bytes']}")
        print(f"warn_threshold : {config['warn_threshold']}")

    else:
        print("Unknown quota command.", file=sys.stderr)
        raise SystemExit(1)


def build_quota_parser(
    subparsers: argparse._SubParsersAction,
    vault_dir: str = ".",
) -> argparse.ArgumentParser:
    """Register the 'quota' command and its sub-commands."""
    p = subparsers.add_parser("quota", help="Manage vault storage quotas")
    p.set_defaults(vault_dir=vault_dir)
    sub = p.add_subparsers(dest="quota_cmd", required=True)

    # set
    p_set = sub.add_parser("set", help="Configure quota limits")
    p_set.add_argument("max_bytes", type=int, help="Maximum vault size in bytes")
    p_set.add_argument(
        "--warn",
        dest="warn_threshold",
        type=float,
        default=0.8,
        help="Warning threshold as a fraction (default: 0.8)",
    )

    # status
    sub.add_parser("status", help="Show current usage vs quota")

    # show
    sub.add_parser("show", help="Show quota configuration")

    p.set_defaults(func=cmd_quota)
    return p
