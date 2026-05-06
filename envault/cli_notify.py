"""CLI sub-commands for managing envault notifications."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.notify import NotifyError, dispatch, load_notify, set_notify, EVENTS


def cmd_notify(args: argparse.Namespace) -> None:
    vault_dir = Path(args.vault_dir)

    if args.notify_cmd == "show":
        config = load_notify(vault_dir)
        print(f"Webhook : {config.get('webhook') or '(none)'}")
        print(f"Email   : {config.get('email') or '(none)'}")
        print(f"Events  : {', '.join(config.get('events', []))}")

    elif args.notify_cmd == "set":
        events = args.events.split(",") if args.events else None
        try:
            config = set_notify(
                vault_dir,
                webhook=args.webhook,
                email=args.email,
                events=events,
            )
        except NotifyError as exc:
            raise SystemExit(f"error: {exc}") from exc
        print("Notification config updated.")
        if config.get("webhook"):
            print(f"  webhook -> {config['webhook']}")
        if config.get("email"):
            print(f"  email   -> {config['email']}")
        print(f"  events  -> {', '.join(config['events'])}")

    elif args.notify_cmd == "test":
        event = args.event
        try:
            dispatch(vault_dir, event, {"test": True})
        except NotifyError as exc:
            raise SystemExit(f"error: {exc}") from exc
        print(f"Test notification dispatched for event '{event}'.")

    else:
        raise SystemExit("Unknown notify sub-command.")


def build_notify_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("notify", help="Manage event notifications")
    p.add_argument("--vault-dir", default=".", help="Vault directory")
    sub = p.add_subparsers(dest="notify_cmd", required=True)

    sub.add_parser("show", help="Show current notification config")

    p_set = sub.add_parser("set", help="Configure notifications")
    p_set.add_argument("--webhook", default=None, help="Webhook URL")
    p_set.add_argument("--email", default=None, help="Recipient email address")
    p_set.add_argument(
        "--events", default=None,
        help=f"Comma-separated events to subscribe ({', '.join(sorted(EVENTS))})",
    )

    p_test = sub.add_parser("test", help="Send a test notification")
    p_test.add_argument("event", choices=sorted(EVENTS), help="Event to simulate")

    p.set_defaults(func=cmd_notify)
