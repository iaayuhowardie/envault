"""Integration helpers: wire the rekey sub-command into the main CLI parser.

This module is intentionally thin — it exists so the main ``envault/__main__.py``
(or ``envault/cli.py``) can do a single import rather than duplicating the
parser-registration call.
"""

from __future__ import annotations

import argparse

from envault.cli_rekey import build_rekey_parser


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *rekey* sub-command with *subparsers*.

    Typical usage inside the main CLI setup::

        from envault.cli_rekey_integration import register as register_rekey
        register_rekey(main_subparsers)
    """
    build_rekey_parser(subparsers)


def make_standalone_parser() -> argparse.ArgumentParser:
    """Return a self-contained parser for the rekey command (useful for testing)."""
    root = argparse.ArgumentParser(
        prog="envault rekey",
        description="Re-encrypt the vault under a new set of GPG recipients.",
    )
    sub = root.add_subparsers(dest="command")
    build_rekey_parser(sub)
    return root
