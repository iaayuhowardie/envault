"""CLI sub-command: envault watch — auto-lock .env on change."""

import argparse
from pathlib import Path

from envault.cli import cmd_lock
from envault.watch import WatchError, watch


def _auto_lock(vault_dir: Path) -> None:
    """Callback passed to watch(); re-locks the vault when .env changes."""
    print(f"[envault] change detected in {vault_dir / '.env'} — re-locking…")
    try:
        cmd_lock(vault_dir)
        print("[envault] vault locked.")
    except Exception as exc:  # noqa: BLE001
        print(f"[envault] lock failed: {exc}")


def cmd_watch(
    vault_dir: Path,
    interval: float = 1.0,
    max_iterations: int | None = None,
) -> None:
    """
    Watch *vault_dir/.env* and re-lock the vault whenever the file changes.

    Parameters
    ----------
    vault_dir:      Root directory of the vault.
    interval:       Polling interval in seconds.
    max_iterations: Cap on poll iterations (None = run forever).
    """
    print(f"[envault] watching {vault_dir / '.env'} (interval={interval}s) …")
    try:
        watch(
            vault_dir,
            on_change=lambda p: _auto_lock(vault_dir),
            interval=interval,
            max_iterations=max_iterations,
        )
    except WatchError as exc:
        raise SystemExit(f"watch error: {exc}") from exc
    except KeyboardInterrupt:
        print("\n[envault] watch stopped.")


def build_watch_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *watch* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "watch",
        help="Watch .env for changes and auto-lock the vault.",
    )
    p.add_argument(
        "--dir",
        default=".",
        metavar="DIR",
        help="Vault directory (default: current directory).",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 1.0).",
    )
    p.set_defaults(
        func=lambda args: cmd_watch(
            vault_dir=Path(args.dir),
            interval=args.interval,
        )
    )
