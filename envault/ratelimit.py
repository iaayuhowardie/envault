"""Rate limiting for envault operations (e.g. unlock attempts)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any


class RateLimitError(Exception):
    """Raised when a rate limit is exceeded or config is invalid."""


DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_WINDOW_SECONDS = 60


def _ratelimit_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "ratelimit.json"


def load_ratelimit(vault_dir: Path) -> Dict[str, Any]:
    """Load rate limit state from disk; return defaults if missing or corrupt."""
    path = _ratelimit_path(vault_dir)
    if not path.exists():
        return {"attempts": [], "max_attempts": DEFAULT_MAX_ATTEMPTS, "window": DEFAULT_WINDOW_SECONDS}
    try:
        data = json.loads(path.read_text())
        data.setdefault("attempts", [])
        data.setdefault("max_attempts", DEFAULT_MAX_ATTEMPTS)
        data.setdefault("window", DEFAULT_WINDOW_SECONDS)
        return data
    except (json.JSONDecodeError, ValueError) as exc:
        raise RateLimitError(f"Corrupt ratelimit file: {exc}") from exc


def save_ratelimit(vault_dir: Path, state: Dict[str, Any]) -> None:
    """Persist rate limit state to disk."""
    path = _ratelimit_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


def configure(vault_dir: Path, max_attempts: int, window: int) -> None:
    """Set the max attempts and time window (seconds) for rate limiting."""
    if max_attempts < 1:
        raise RateLimitError("max_attempts must be >= 1")
    if window < 1:
        raise RateLimitError("window must be >= 1 second")
    state = load_ratelimit(vault_dir)
    state["max_attempts"] = max_attempts
    state["window"] = window
    save_ratelimit(vault_dir, state)


def record_attempt(vault_dir: Path) -> None:
    """Record a new attempt timestamp; raise RateLimitError if limit exceeded."""
    state = load_ratelimit(vault_dir)
    now = time.time()
    window = state["window"]
    # Prune expired timestamps
    state["attempts"] = [t for t in state["attempts"] if now - t < window]
    if len(state["attempts"]) >= state["max_attempts"]:
        wait = int(window - (now - state["attempts"][0])) + 1
        raise RateLimitError(
            f"Rate limit exceeded: {state['max_attempts']} attempts in {window}s. "
            f"Try again in ~{wait}s."
        )
    state["attempts"].append(now)
    save_ratelimit(vault_dir, state)


def reset(vault_dir: Path) -> None:
    """Clear all recorded attempts (e.g. after a successful unlock)."""
    state = load_ratelimit(vault_dir)
    state["attempts"] = []
    save_ratelimit(vault_dir, state)
