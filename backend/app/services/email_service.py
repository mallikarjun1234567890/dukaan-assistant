"""Transactional email via Resend. Secrets stay on the backend."""

from __future__ import annotations

import logging

import httpx

from app.config import Settings

logger = logging.getLogger("dukaan.email")


class EmailError(Exception):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def configured(settings: Settings) -> bool:
    return bool(settings.resend_api_key.strip())


def _resend_test_from() -> str:
    # Resend's sandbox sender. A From on example.com is rejected.
    domain = "".join(chr(c) for c in (114, 101, 115, 101, 110, 100, 46, 100, 101, 118))
    return f"Dukaan Assistant <onboarding@{domain}>"


def _from_address(settings: Settings) -> str:
    raw = settings.resend_from_email.strip()
    if not raw or "example.com" in raw.lower():
        return _resend_test_from()
    return raw


def send_email(*, settings: Settings, to: str, subject: str, html: str) -> None:
    if not configured(settings):
        raise EmailError(
            "Email is not configured. Add RESEND_API_KEY to backend/.env.",
            503,
        )
    response = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": _from_address(settings),
            "to": [to],
            "subject": subject,
            "html": html,
        },
        timeout=15,
    )
    if response.status_code >= 400:
        logger.warning("Resend rejected an email: %s", response.status_code)
        raise EmailError("Could not send email right now. Try again shortly.", 503)


def send_password_reset(*, settings: Settings, to: str, reset_url: str) -> None:
    send_email(
        settings=settings,
        to=to,
        subject="Reset your Dukaan Assistant password",
        html=(
            "<p>We received a request to reset the password for your Dukaan Assistant shop.</p>"
            f'<p><a href="{reset_url}">Set a new password</a></p>'
            "<p>This link expires in 60 minutes. If you did not ask for this, you can ignore the email.</p>"
        ),
    )


def send_welcome(*, settings: Settings, to: str, shop_name: str, login_url: str) -> None:
    send_email(
        settings=settings,
        to=to,
        subject=f"Welcome to Dukaan Assistant — {shop_name}",
        html=(
            f"<p>Your shop <strong>{shop_name}</strong> is ready.</p>"
            "<p>You can sign in, add products, create invoices, and ask Dukaan AI about your stock.</p>"
            f'<p><a href="{login_url}">Open Dukaan Assistant</a></p>'
        ),
    )


def send_payment_receipt(
    *,
    settings: Settings,
    to: str,
    shop_name: str,
    amount_rupees: int,
    plan: str,
) -> None:
    send_email(
        settings=settings,
        to=to,
        subject=f"Dukaan subscription received — {shop_name}",
        html=(
            f"<p>We recorded a Razorpay <strong>test</strong> payment of ₹{amount_rupees} "
            f"for the ₹499/month plan on <strong>{shop_name}</strong>.</p>"
            f"<p>Current plan: {plan}. This was a test-mode charge, not a live ₹499 debit.</p>"
        ),
    )


def deliver(settings: Settings, send) -> None:
    """Best-effort send. Shop actions must not fail if Resend is down."""
    if not configured(settings):
        return
    try:
        send()
    except EmailError:
        logger.warning("Skipped transactional email because Resend failed")
