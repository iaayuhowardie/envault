"""GPG signing and signature verification for encrypted vault files."""

from __future__ import annotations

import subprocess
from pathlib import Path

from envault.crypto import _require_gpg, GPGError


class SignError(Exception):
    """Raised when signing or verification fails."""


def sign_file(file_path: Path, fingerprint: str) -> Path:
    """Create a detached GPG signature for *file_path*.

    The signature is written to ``<file_path>.sig`` and that path is returned.

    Raises:
        SignError: if GPG is unavailable or the signing command fails.
    """
    gpg = _require_gpg()
    sig_path = file_path.with_suffix(file_path.suffix + ".sig")

    result = subprocess.run(
        [
            gpg,
            "--batch",
            "--yes",
            "--local-user", fingerprint,
            "--detach-sign",
            "--output", str(sig_path),
            str(file_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SignError(f"GPG signing failed: {result.stderr.strip()}")

    return sig_path


def verify_file(file_path: Path, sig_path: Path | None = None) -> str:
    """Verify the detached signature for *file_path*.

    If *sig_path* is not provided, ``<file_path>.sig`` is assumed.

    Returns the fingerprint of the signing key on success.

    Raises:
        SignError: if the signature is missing, invalid, or GPG fails.
    """
    gpg = _require_gpg()

    if sig_path is None:
        sig_path = file_path.with_suffix(file_path.suffix + ".sig")

    if not sig_path.exists():
        raise SignError(f"Signature file not found: {sig_path}")

    result = subprocess.run(
        [
            gpg,
            "--batch",
            "--status-fd", "1",
            "--verify",
            str(sig_path),
            str(file_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SignError(f"Signature verification failed: {result.stderr.strip()}")

    for line in result.stdout.splitlines():
        if "VALIDSIG" in line:
            parts = line.split()
            # [GNUPG:] VALIDSIG <fingerprint> ...
            if len(parts) >= 3:
                return parts[2]

    raise SignError("Could not extract fingerprint from GPG output.")
