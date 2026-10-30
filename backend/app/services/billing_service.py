"""Server-side Razorpay checkout. Amounts and secrets never come from the browser."""

from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import BillingOrder, Payment, Shop
from app.services.subscription import (
    LIST_PRICE_RUPEES,
    TEST_CHARGE_RUPEES,
    activate_paid,
    utc_now,
)

logger = logging.getLogger("dukaan.billing")

CURRENCY = "INR"
CAPTURED = "captured"


class BillingError(HTTPException):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


def billing_enabled(settings: Settings) -> bool:
    return bool(settings.razorpay_key_id.strip() and settings.razorpay_key_secret.strip())


def billing_environment(settings: Settings) -> str:
    mode = settings.razorpay_mode.strip().lower()
    if mode in {"live", "prod", "production"}:
        return "live"
    if mode in {"test", "sandbox"}:
        return "test"
    key = settings.razorpay_key_id.strip()
    if key.startswith("rzp_live_"):
        return "live"
    return "test"


def checkout_amount_paise(settings: Settings) -> int:
    if billing_environment(settings) == "live":
        return int(settings.billing_list_amount_paise)
    return int(settings.billing_test_amount_paise)


def list_price_rupees(_settings: Settings | None = None) -> int:
    return LIST_PRICE_RUPEES


def charge_rupees(settings: Settings) -> int:
    return checkout_amount_paise(settings) // 100


def assert_key_matches_mode(settings: Settings) -> None:
    env = billing_environment(settings)
    key = settings.razorpay_key_id.strip()
    if env == "live" and key.startswith("rzp_test_"):
        raise BillingError(
            "Live billing mode requires live Razorpay keys.",
            status_code=503,
        )
    if env == "test" and key.startswith("rzp_live_"):
        raise BillingError(
            "Test billing mode cannot use live Razorpay keys.",
            status_code=503,
        )


def _client(settings: Settings):
    try:
        import razorpay
    except ImportError as exc:
        raise BillingError("Razorpay SDK is not installed", status_code=503) from exc
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


def verify_signature(settings: Settings, order_id: str, payment_id: str, signature: str) -> None:
    body = f"{order_id}|{payment_id}"
    expected = hmac.new(
        settings.razorpay_key_secret.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise BillingError("Payment signature is invalid")


def fetch_razorpay_payment(settings: Settings, payment_id: str) -> dict:
    try:
        payment = _client(settings).payment.fetch(payment_id)
    except BillingError:
        raise
    except Exception as exc:
        logger.warning("Razorpay payment lookup failed: %s", type(exc).__name__)
        raise BillingError("Payment could not be verified with Razorpay", status_code=503) from exc
    if not isinstance(payment, dict):
        raise BillingError("Payment could not be verified with Razorpay", status_code=503)
    return payment


def create_checkout_order(db: Session, shop: Shop, settings: Settings) -> BillingOrder:
    if not billing_enabled(settings):
        raise BillingError(
            "Razorpay test keys are not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.",
            status_code=503,
        )
    assert_key_matches_mode(settings)
    amount = checkout_amount_paise(settings)
    if amount <= 0:
        raise BillingError("Billing amount is not configured", status_code=503)
    environment = billing_environment(settings)
    try:
        remote = _client(settings).order.create(
            {
                "amount": amount,
                "currency": CURRENCY,
                "payment_capture": 1,
                "notes": {"shop_id": str(shop.id)},
            }
        )
    except BillingError:
        raise
    except Exception as exc:
        logger.warning("Razorpay order create failed: %s", type(exc).__name__)
        raise BillingError("Could not create a checkout order", status_code=503) from exc

    remote_id = str(remote.get("id") or "")
    remote_amount = int(remote.get("amount") or 0)
    remote_currency = str(remote.get("currency") or "")
    if not remote_id or remote_amount != amount or remote_currency != CURRENCY:
        raise BillingError("Razorpay returned an unexpected order", status_code=503)

    row = BillingOrder(
        shop_id=shop.id,
        razorpay_order_id=remote_id,
        amount_paise=amount,
        currency=CURRENCY,
        environment=environment,
        status="created",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _already_processed(db: Session, shop: Shop, payment_id: str, order_id: str) -> Payment | None:
    existing = db.scalar(select(Payment).where(Payment.razorpay_payment_id == payment_id))
    if existing is None:
        by_order = db.scalar(select(Payment).where(Payment.razorpay_order_id == order_id))
        if by_order is None:
            return None
        if by_order.razorpay_payment_id and by_order.razorpay_payment_id != payment_id:
            raise BillingError("This order was already paid with a different payment")
        if by_order.shop_id != shop.id:
            raise BillingError("Payment does not belong to this shop")
        return by_order
    if existing.shop_id != shop.id:
        raise BillingError("Payment does not belong to this shop")
    if existing.razorpay_order_id and existing.razorpay_order_id != order_id:
        raise BillingError("Payment does not belong to this order")
    return existing


def verify_checkout_payment(
    db: Session,
    shop: Shop,
    settings: Settings,
    *,
    order_id: str,
    payment_id: str,
    signature: str,
) -> tuple[str, bool]:
    """Return (plan, newly_captured). newly_captured is False for idempotent replays."""
    if not billing_enabled(settings):
        raise BillingError("Razorpay is not configured", status_code=503)
    if not order_id.strip() or not payment_id.strip() or not signature.strip():
        raise BillingError("Payment details are incomplete")

    verify_signature(settings, order_id, payment_id, signature)

    replay = _already_processed(db, shop, payment_id, order_id)
    if replay is not None:
        return shop.plan, False

    order = db.scalar(select(BillingOrder).where(BillingOrder.razorpay_order_id == order_id))
    if order is None:
        raise BillingError("Unknown checkout order")
    if order.shop_id != shop.id:
        raise BillingError("This order does not belong to this shop")
    if order.environment != billing_environment(settings):
        raise BillingError("Checkout order environment does not match billing mode")
    if order.amount_paise != checkout_amount_paise(settings) or order.currency != CURRENCY:
        raise BillingError("Checkout amount does not match the configured plan")
    if order.status == "paid":
        raise BillingError("This order was already paid with a different payment")

    remote = fetch_razorpay_payment(settings, payment_id)
    remote_order = str(remote.get("order_id") or "")
    remote_status = str(remote.get("status") or "").lower()
    try:
        remote_amount = int(remote.get("amount") or 0)
    except (TypeError, ValueError):
        remote_amount = 0
    remote_currency = str(remote.get("currency") or CURRENCY)

    if remote_order != order_id:
        raise BillingError("Payment does not belong to this order")
    if remote_status != CAPTURED:
        raise BillingError("Payment has not been captured")
    if remote_amount != order.amount_paise:
        raise BillingError("Payment amount does not match the order")
    if remote_currency != order.currency:
        raise BillingError("Payment currency does not match the order")

    environment = billing_environment(settings)
    record = Payment(
        shop_id=shop.id,
        amount_paise=order.amount_paise,
        currency=order.currency,
        plan="active",
        razorpay_order_id=order_id,
        razorpay_payment_id=payment_id,
        status=CAPTURED,
        environment=environment,
        is_test=environment != "live",
    )
    try:
        db.add(record)
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        shop = db.get(Shop, shop.id) or shop
        replay = _already_processed(db, shop, payment_id, order_id)
        if replay is not None:
            return shop.plan, False
        raise BillingError("Payment was already processed") from exc

    activate_paid(shop)
    order.status = "paid"
    order.updated_at = utc_now()
    record.plan = shop.plan
    db.commit()
    db.refresh(shop)
    return shop.plan, True


def captured_revenue_paise(db: Session, *, live: bool) -> int:
    rows = list(
        db.scalars(
            select(Payment).where(
                Payment.status == CAPTURED,
                Payment.is_test.is_(not live),
            )
        ).all()
    )
    return sum(row.amount_paise for row in rows)


def captured_payment_count(db: Session) -> int:
    from sqlalchemy import func

    return db.scalar(select(func.count(Payment.id)).where(Payment.status == CAPTURED)) or 0


def receipt_amount_rupees(settings: Settings) -> int:
    rupees = charge_rupees(settings)
    if billing_environment(settings) == "live":
        return rupees
    return rupees if rupees > 0 else TEST_CHARGE_RUPEES
