"""Email delivery logic for the AI Reader's Digest."""

from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"


def send_email(subject: str, html_content: str) -> bool:
    """Send an HTML digest email through Gmail SMTP."""

    load_dotenv(ENV_PATH)

    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")

    missing = [
        name
        for name, value in {
            "EMAIL_SENDER": sender,
            "EMAIL_PASSWORD": password,
            "EMAIL_RECEIVER": receiver,
        }.items()
        if not value
    ]
    if missing:
        print(f"❌ Email not sent. Missing environment variables: {', '.join(missing)}")
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receiver
    message.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, receiver, message.as_string())
    except smtplib.SMTPAuthenticationError:
        print(
            "❌ Email failed: Gmail rejected the login. "
            "Use a Gmail App Password, not your normal Gmail password."
        )
        return False
    except smtplib.SMTPException as exc:
        print(f"❌ Email failed: SMTP error: {exc}")
        return False
    except OSError as exc:
        print(f"❌ Email failed: network error: {exc}")
        return False

    print("✅ Email sent successfully")
    return True


def send_digest_email(digest: dict[str, Any], recipient: str) -> bool:
    """Backward-compatible plain HTML wrapper for older callers."""

    html = _digest_to_html(digest)
    subject = "AI Reader's Digest"
    os.environ.setdefault("EMAIL_RECEIVER", recipient)
    return send_email(subject, html)


def _digest_to_text(digest: dict[str, Any]) -> str:
    lines = [f"AI Reader Digest - {digest.get('generated_at')}", ""]
    for article in digest.get("articles", []):
        lines.extend(
            [
                article.get("title") or "Untitled",
                article.get("url") or "",
                article.get("summary") or "",
                "",
            ]
        )
    return "\n".join(lines)


def _digest_to_html(digest: dict[str, Any]) -> str:
    text = _digest_to_text(digest)
    return f"<pre>{text}</pre>"
