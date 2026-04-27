"""CLI entry points for envault."""

import sys
from pathlib import Path

from envault.vault import (
    VaultError,
    load_meta,
    save_meta,
    add_recipient,
    remove_recipient,
    lock,
    unlock,
)
from envault.sync import SyncError, push, pull, status as sync_status

_DEFAULT_VAULT = Path(".envvault")
_DEFAULT_ENV = Path(".env")


def cmd_init(env_file: Path, recipients: list[str], vault_dir: Path = _DEFAULT_VAULT) -> None:
    if not recipients:
        raise VaultError("At least one recipient GPG key is required.")
    if not env_file.exists():
        raise VaultError(f"Env file not found: {env_file}")
    vault_dir.mkdir(parents=True, exist_ok=True)
    meta = {"recipients": recipients}
    save_meta(vault_dir, meta)
    lock(env_file, vault_dir, recipients)


def cmd_add(fingerprint: str, vault_dir: Path = _DEFAULT_VAULT) -> None:
    meta = load_meta(vault_dir)
    add_recipient(meta, fingerprint)
    save_meta(vault_dir, meta)


def cmd_remove(fingerprint: str, vault_dir: Path = _DEFAULT_VAULT) -> None:
    meta = load_meta(vault_dir)
    remove_recipient(meta, fingerprint)
    save_meta(vault_dir, meta)


def cmd_lock(env_file: Path = _DEFAULT_ENV, vault_dir: Path = _DEFAULT_VAULT) -> None:
    meta = load_meta(vault_dir)
    lock(env_file, vault_dir, meta["recipients"])


def cmd_unlock(env_file: Path = _DEFAULT_ENV, vault_dir: Path = _DEFAULT_VAULT) -> None:
    unlock(vault_dir, env_file)


def cmd_push(remote_url: str, vault_dir: Path = _DEFAULT_VAULT) -> None:
    """Push local vault to a remote location."""
    try:
        push(vault_dir, remote_url)
        print(f"Vault pushed to {remote_url}")
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_pull(remote_url: str, vault_dir: Path = _DEFAULT_VAULT) -> None:
    """Pull vault from a remote location into the local vault directory."""
    try:
        pull(remote_url, vault_dir)
        print(f"Vault pulled from {remote_url}")
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_status(remote_url: str, vault_dir: Path = _DEFAULT_VAULT) -> None:
    """Show sync status between local vault and remote."""
    try:
        result = sync_status(vault_dir, remote_url)
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if result["in_sync"]:
        print("In sync:", ", ".join(result["in_sync"]))
    if result["local_only"]:
        print("Local only (not pushed):", ", ".join(result["local_only"]))
    if result["remote_only"]:
        print("Remote only (not pulled):", ", ".join(result["remote_only"]))
    if not any(result.values()):
        print("Nothing to sync — both sides are empty.")


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(prog="envault", description="Encrypt and sync .env files.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init").add_argument("recipients", nargs="+")
    sub.add_parser("add").add_argument("fingerprint")
    sub.add_parser("remove").add_argument("fingerprint")
    sub.add_parser("lock")
    sub.add_parser("unlock")
    for cmd in ("push", "pull", "status"):
        sub.add_parser(cmd).add_argument("remote")

    args = parser.parse_args(argv)
    dispatch = {
        "init": lambda: cmd_init(_DEFAULT_ENV, args.recipients),
        "add": lambda: cmd_add(args.fingerprint),
        "remove": lambda: cmd_remove(args.fingerprint),
        "lock": cmd_lock,
        "unlock": cmd_unlock,
        "push": lambda: cmd_push(args.remote),
        "pull": lambda: cmd_pull(args.remote),
        "status": lambda: cmd_status(args.remote),
    }
    dispatch[args.command]()


if __name__ == "__main__":  # pragma: no cover
    main()
