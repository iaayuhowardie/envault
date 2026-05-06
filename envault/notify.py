"""Notification hooks for envault events (lock, unlock, rotate, sync)."""

from __future__ import annotations

import json
import smtplib
import urllib.request
from email.message import EmailMessage
from pathlib import Path
from typing import Any


class NotifyError(Exception):
    """Raised when a notification fails to send."""


EVENTS = {"lock", "unlock", "rotate", "push", "pull"}


def _notify_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "notify.json"


def load_notify(vault_dir: Path) -> dict[str, Any]:
    """Load notification config; returns defaults if missing."""
    path = _notify_path(vault_dir)
    if not path.exists():
        return {"webhook": None, "email": None, "events": list(EVENTS)}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise NotifyError(f"Corrupt notify config: {exc}") from exc


def save_notify(vault_dir: Path, config: dict[str, Any]) -> None:
    """Persist notification config to disk."""
    path = _notify_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2))


def set_notify(vault_dir: Path, *, webhook: str | None = None,
               email: str | None = None,
               events: list[str] | None = None) -> dict[str, Any]:
    """Update notification settings."""
    unknown = set(events or []) - EVENTS
    if unknown:
        raise NotifyError(f"Unknown events: {', '.join(sorted(unknown))}")
    config = load_notify(vault_dir)
    if webhook is not None:
        config["webhook"] = webhook
    if email is not None:
        config["email"] = email
    if events is not None:
        config["events"] = events
    save_notify(vault_dir, config)
    return config


def send_webhook(url: str, event: str, payload: dict[str, Any]) -> None:
    """POST a JSON payload to *url*."""
    body = json.dumps({"event": event, **payload}).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as exc:
        raise NotifyError(f"Webhook delivery failed: {exc}") from exc


def send_email(smtp_url: str, to: str, event: str, payload: dict[str, Any]) -> None:
    """Send a plain-text notification email via *smtp_url* (host:port)."""
    host, _, port_str = smtp_url.partition(":")
    port = int(port_str) if port_str else 25
    msg = EmailMessage()
    msg["Subject"] = f"[envault] {event} event"
    msg["From"] = "envault@localhost"
    msg["To"] = to
    msg.set_content(f"Event: {event}\n\n{json.dumps(payload, indent=2)}\n")
    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.send_message(msg)
    except Exception as exc:
        raise NotifyError(f"Email delivery failed: {exc}") from exc


def dispatch(vault_dir: Path, event: str, payload: dict[str, Any] | None = None) -> None:
    """Fire all configured notifications for *event* if it is subscribed."""
    if event not in EVENTS:
        raise NotifyError(f"Unknown event: {event!r}")
    config = load_notify(vault_dir)
    if event not in config.get("events", []):
        return
    data: dict[str, Any] = payload or {}
    if config.get("webhook"):
        send_webhook(config["webhook"], event, data)
    if config.get("email"):
        smtp = config.get("smtp", "localhost:25")
        send_email(smtp, config["email"], event, data)
