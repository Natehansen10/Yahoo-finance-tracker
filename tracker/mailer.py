"""Send the daily report by email over SMTP. Credentials live in .env, never in the repo."""

import smtplib
from email.message import EmailMessage
from pathlib import Path


def load_env(path: Path) -> dict[str, str]:
    """Read KEY=VALUE lines. Blank lines and # comments are ignored."""
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"')
    return env


def send(subject: str, body: str, env: dict[str, str]) -> bool:
    """Send one plain-text email. Returns False when email is not set up."""
    user = env.get("TRACKER_EMAIL_USER", "")
    password = env.get("TRACKER_EMAIL_PASSWORD", "").replace(" ", "")  # Google shows app passwords with spaces
    if not user or not password:
        return False

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = env.get("TRACKER_EMAIL_TO") or user
    msg["Subject"] = subject
    msg.set_content(body)

    host = env.get("TRACKER_SMTP_HOST", "smtp.gmail.com")
    port = int(env.get("TRACKER_SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(host, port, timeout=30) as server:
        server.login(user, password)
        server.send_message(msg)
    return True
