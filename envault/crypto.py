"""GPG encryption and decryption utilities for envault."""

import subprocess
import shutil
from pathlib import Path


class GPGError(Exception):
    """Raised when a GPG operation fails."""
    pass


def _require_gpg() -> str:
    """Ensure gpg is available on the system, return its path."""
    gpg = shutil.which("gpg") or shutil.which("gpg2")
    if not gpg:
        raise GPGError(
            "GPG is not installed or not found in PATH. "
            "Install it via your package manager (e.g. brew install gnupg)."
        )
    return gpg


def list_keys() -> list[dict]:
    """Return a list of available public GPG keys."""
    gpg = _require_gpg()
    result = subprocess.run(
        [gpg, "--list-keys", "--with-colons"],
        capture_output=True, text=True, check=True
    )
    keys = []
    current: dict = {}
    for line in result.stdout.splitlines():
        parts = line.split(":")
        if parts[0] == "pub":
            current = {"fingerprint": "", "uids": []}
            keys.append(current)
        elif parts[0] == "fpr" and current:
            current["fingerprint"] = parts[9]
        elif parts[0] == "uid" and current:
            current["uids"].append(parts[9])
    return keys


def encrypt_file(input_path: Path, output_path: Path, recipients: list[str]) -> None:
    """Encrypt a file for one or more GPG recipients."""
    if not recipients:
        raise GPGError("At least one recipient fingerprint is required.")
    gpg = _require_gpg()
    cmd = [gpg, "--batch", "--yes", "--output", str(output_path), "--encrypt"]
    for recipient in recipients:
        cmd += ["--recipient", recipient]
    cmd.append(str(input_path))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise GPGError(f"Encryption failed:\n{result.stderr}")


def decrypt_file(input_path: Path, output_path: Path) -> None:
    """Decrypt a GPG-encrypted file using the local keyring."""
    gpg = _require_gpg()
    cmd = [
        gpg, "--batch", "--yes",
        "--output", str(output_path),
        "--decrypt", str(input_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise GPGError(f"Decryption failed:\n{result.stderr}")
