"""CLI commands for managing envault lifecycle hooks."""
from __future__ import annotations

import argparse
from pathlib import Path

from envault.hooks import HookError, load_hooks, remove_hook, set_hook


def cmd_hooks(args: argparse.Namespace) -> None:
    """Dispatch hook sub-commands."""
    vault_dir = Path(args.vault_dir) if hasattr(args, "vault_dir") and args.vault_dir else Path.cwd()

    if args.hook_action == "set":
        try:
            set_hook(vault_dir, args.event, args.command)
            print(f"Hook '{args.event}' set.")
        except HookError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    elif args.hook_action == "remove":
        try:
            remove_hook(vault_dir, args.event)
            print(f"Hook '{args.event}' removed.")
        except HookError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    elif args.hook_action == "list":
        hooks = load_hooks(vault_dir)
        if not hooks:
            print("No hooks registered.")
        else:
            for event, command in sorted(hooks.items()):
                print(f"  {event}: {command}")

    else:
        raise SystemExit(f"Unknown hook action: {args.hook_action}")


def build_hooks_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Register the 'hooks' command on *subparsers*."""
    p = subparsers.add_parser("hooks", help="Manage lifecycle hooks")
    p.add_argument("--vault-dir", default=None, help="Path to vault directory")
    sub = p.add_subparsers(dest="hook_action", required=True)

    set_p = sub.add_parser("set", help="Register a hook for an event")
    set_p.add_argument("event", help="Lifecycle event name")
    set_p.add_argument("command", help="Shell command to run")

    rm_p = sub.add_parser("remove", help="Remove a registered hook")
    rm_p.add_argument("event", help="Lifecycle event name")

    sub.add_parser("list", help="List all registered hooks")

    p.set_defaults(func=cmd_hooks)
    return p
