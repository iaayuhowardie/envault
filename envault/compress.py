"""Compression support for encrypted vault files."""
from __future__ import annotations

import gzip
import shutil
from pathlib import Path


class CompressError(Exception):
    """Raised when a compression or decompression operation fails."""


def compress_file(src: Path, dest: Path | None = None) -> Path:
    """Compress *src* with gzip and write to *dest*.

    If *dest* is omitted the output path is ``src`` with a ``.gz`` suffix
    appended.  Returns the path of the compressed file.
    """
    if not src.exists():
        raise CompressError(f"Source file not found: {src}")

    out = dest if dest is not None else src.with_suffix(src.suffix + ".gz")

    try:
        with src.open("rb") as f_in, gzip.open(out, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    except OSError as exc:
        raise CompressError(f"Failed to compress {src}: {exc}") from exc

    return out


def decompress_file(src: Path, dest: Path | None = None) -> Path:
    """Decompress a gzip-compressed *src* and write to *dest*.

    If *dest* is omitted the output path is *src* with the trailing ``.gz``
    suffix stripped.  Raises :class:`CompressError` when *src* does not end
    with ``.gz``.
    """
    if not src.exists():
        raise CompressError(f"Source file not found: {src}")

    if src.suffix != ".gz":
        raise CompressError(f"Expected a .gz file, got: {src}")

    out = dest if dest is not None else src.with_suffix("")

    try:
        with gzip.open(src, "rb") as f_in, out.open("wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    except (OSError, gzip.BadGzipFile) as exc:
        raise CompressError(f"Failed to decompress {src}: {exc}") from exc

    return out


def compressed_size(path: Path) -> int:
    """Return the byte size of *path* after gzip compression (in-memory)."""
    if not path.exists():
        raise CompressError(f"File not found: {path}")

    import io

    buf = io.BytesIO()
    try:
        with path.open("rb") as f_in, gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            shutil.copyfileobj(f_in, gz)
    except OSError as exc:
        raise CompressError(f"Could not read {path}: {exc}") from exc

    return buf.tell()
