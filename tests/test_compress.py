"""Tests for envault.compress."""
from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from envault.compress import (
    CompressError,
    compress_file,
    compressed_size,
    decompress_file,
)


@pytest.fixture()
def tmp_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.env"
    p.write_text("SECRET=hello\nANOTHER=world\n")
    return p


# ---------------------------------------------------------------------------
# compress_file
# ---------------------------------------------------------------------------

def test_compress_file_creates_gz(tmp_file: Path) -> None:
    out = compress_file(tmp_file)
    assert out == tmp_file.with_suffix(".env.gz")
    assert out.exists()


def test_compress_file_custom_dest(tmp_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out.gz"
    result = compress_file(tmp_file, dest)
    assert result == dest
    assert dest.exists()


def test_compress_file_content_is_valid_gzip(tmp_file: Path) -> None:
    out = compress_file(tmp_file)
    with gzip.open(out, "rb") as fh:
        content = fh.read().decode()
    assert "SECRET=hello" in content


def test_compress_file_missing_source_raises(tmp_path: Path) -> None:
    with pytest.raises(CompressError, match="Source file not found"):
        compress_file(tmp_path / "nonexistent.env")


# ---------------------------------------------------------------------------
# decompress_file
# ---------------------------------------------------------------------------

def test_decompress_file_restores_content(tmp_file: Path) -> None:
    gz = compress_file(tmp_file)
    restored = decompress_file(gz)
    assert restored.read_text() == tmp_file.read_text()


def test_decompress_file_custom_dest(tmp_file: Path, tmp_path: Path) -> None:
    gz = compress_file(tmp_file)
    dest = tmp_path / "restored.env"
    result = decompress_file(gz, dest)
    assert result == dest
    assert dest.read_text() == tmp_file.read_text()


def test_decompress_file_missing_source_raises(tmp_path: Path) -> None:
    with pytest.raises(CompressError, match="Source file not found"):
        decompress_file(tmp_path / "missing.gz")


def test_decompress_file_non_gz_raises(tmp_file: Path) -> None:
    with pytest.raises(CompressError, match="Expected a .gz file"):
        decompress_file(tmp_file)


# ---------------------------------------------------------------------------
# compressed_size
# ---------------------------------------------------------------------------

def test_compressed_size_returns_int(tmp_file: Path) -> None:
    size = compressed_size(tmp_file)
    assert isinstance(size, int)
    assert size > 0


def test_compressed_size_smaller_than_original_for_repetitive_data(tmp_path: Path) -> None:
    p = tmp_path / "big.env"
    p.write_text(("KEY=value\n") * 200)
    assert compressed_size(p) < p.stat().st_size


def test_compressed_size_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(CompressError, match="File not found"):
        compressed_size(tmp_path / "ghost.env")
