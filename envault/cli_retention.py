"""CLI commands for managing snapshot retention policies."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.retention import RetentionError, apply_retention, load_retention, set_retention
from envault.snapshot import list_snapshots


def cmd_retention(args: argparse.Namespace) -> None:
    vault_dir = Path(args.vault_dir)

    if args.retention_cmd == "show":
        policy = load_retention(vault_dir)
        print(f"max_snapshots : {policy['max_snapshots']}")
        print(f"max_days      : {policy['max_days']}")

    elif args.retention_cmd == "set":
        try:
            policy = set_retention(
                vault_dir,
                max_snapshots=args.max_snapshots,
                max_days=args.max_days,
            )
        except RetentionError as exc:
            raise SystemExit(f"retention error: {exc}") from exc
        print(f"Retention policy updated: max_snapshots={policy['max_snapshots']}, max_days={policy['max_days']}")

    elif args.retention_cmd == "prune":
        snapshots = list_snapshots(vault_dir)
        prunable = apply_retention(vault_dir, snapshots)
        if not prunable:
            print("Nothing to prune.")
            return
        from envault.snapshot import _snapshots_path  # noqa: PLC0415

        snaps_dir = _snapshots_path(vault_dir)
        for snap in prunable:
            snap_file = snaps_dir / snap["name"]
            if snap_file.exists():
                snap_file.unlink()
            print(f"Pruned: {snap['name']}")
        print(f"{len(prunable)} snapshot(s) pruned.")
    else:
        raise SystemExit(f"Unknown retention sub-command: {args.retention_cmd}")


def build_retention_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("retention", help="Manage snapshot retention policy")
    p.add_argument("--vault-dir", default=".", help="Path to vault directory")
    sub = p.add_subparsers(dest="retention_cmd", required=True)

    sub.add_parser("show", help="Show current retention policy")

    set_p = sub.add_parser("set", help="Update retention policy")
    set_p.add_argument("--max-snapshots", type=int, default=None, dest="max_snapshots",
                       help="Maximum number of snapshots to keep")
    set_p.add_argument("--max-days", type=int, default=None, dest="max_days",
                       help="Maximum age of snapshots in days")

    sub.add_parser("prune", help="Remove snapshots that exceed the retention policy")

    p.set_defaults(func=cmd_retention)
