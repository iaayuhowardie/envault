"""CLI sub-commands for tag management."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.tags import TagError, add_tag, list_tags, remove_tag


def cmd_tags(args: argparse.Namespace) -> None:
    """Dispatch tag sub-commands."""
    vault_dir = Path(args.vault_dir) if hasattr(args, "vault_dir") and args.vault_dir else Path.cwd()

    try:
        if args.tag_action == "add":
            tags = add_tag(vault_dir, args.name)
            print(f"Tag '{args.name}' added. Current tags: {', '.join(tags) or '(none)'}")

        elif args.tag_action == "remove":
            tags = remove_tag(vault_dir, args.name)
            print(f"Tag '{args.name}' removed. Current tags: {', '.join(tags) or '(none)'}")

        elif args.tag_action == "list":
            tags = list_tags(vault_dir)
            if tags:
                for tag in tags:
                    print(tag)
            else:
                print("(no tags)")

        else:
            print(f"Unknown tag action: {args.tag_action}", file=sys.stderr)
            sys.exit(1)

    except TagError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_tags_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the *tags* command onto *subparsers*."""
    parser = subparsers.add_parser("tags", help="Manage vault tags")
    parser.add_argument(
        "--vault-dir",
        default=None,
        metavar="DIR",
        help="Path to vault directory (default: cwd)",
    )
    tag_sub = parser.add_subparsers(dest="tag_action", required=True)

    add_p = tag_sub.add_parser("add", help="Add a tag")
    add_p.add_argument("name", help="Tag name to add")

    rm_p = tag_sub.add_parser("remove", help="Remove a tag")
    rm_p.add_argument("name", help="Tag name to remove")

    tag_sub.add_parser("list", help="List all tags")

    parser.set_defaults(func=cmd_tags)
    return parser
