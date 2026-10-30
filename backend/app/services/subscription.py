"""Shop trial, paid plan, lock, and grace-period deletion."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    AIUsageWindow,
    BillingOrder,
    IdempotencyKey,
    Invoice,
    InvoiceItem,
    PasswordResetToken,
    Payment,
    Product,
    ReorderRequest,
    Shop,
    User,
)

TRIAL_DAYS = 30
GRACE_DAYS = 7
PLAN_MONTH_DAYS = 30
LIST_PRICE_RUPEES = 499
TEST_CHARGE_RUPEES = 1
TEST_AMOUNT_PAISE = 100
SHOP_LOCKED_DETAIL = "subscription_expired"
DEMO_SHOP_NAME = "Sharma Kirana Store"
DEMO_EMAIL = "owner@dukaan.local"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def start_trial(shop: Shop, now: datetime | None = None) -> None:
    moment = now or utc_now()
    shop.plan = "trial"
    shop.trial_started_at = moment
    shop.trial_ends_at = moment + timedelta(days=TRIAL_DAYS)
    shop.grace_ends_at = shop.trial_ends_at + timedelta(days=GRACE_DAYS)
    shop.plan_expires_at = None
    shop.paid_at = None


def activate_paid(shop: Shop, now: datetime | None = None) -> None:
    """Grant paid access for 30 days from now.

    Renewal policy: a new captured payment starts a 30-day window from activation.
    If the shop is already active with a later expiry, that expiry is kept (never shortened).
    Duplicate verification must call this only after an idempotency hit, so dates stay put.
    Trial timestamps are never rewritten here.
    """
    moment = now or utc_now()
    expires = as_utc(shop.plan_expires_at)
    if shop.plan == "active" and expires is not None and expires > moment:
        shop.paid_at = shop.paid_at or moment
        shop.admin_locked = False
        return
    shop.plan = "active"
    shop.paid_at = shop.paid_at or moment
    shop.plan_expires_at = moment + timedelta(days=PLAN_MONTH_DAYS)
    shop.admin_locked = False


def mark_active_manual(shop: Shop, now: datetime | None = None) -> None:
    """Audited admin grant of paid-shaped access without a Razorpay payment."""
    moment = now or utc_now()
    shop.plan = "active"
    shop.plan_expires_at = moment + timedelta(days=PLAN_MONTH_DAYS)
    shop.admin_locked = False


def lock_shop(shop: Shop, now: datetime | None = None) -> None:
    shop.admin_locked = True
    if as_utc(shop.grace_ends_at) is None:
        moment = now or utc_now()
        shop.grace_ends_at = moment + timedelta(days=GRACE_DAYS)


def unlock_shop(shop: Shop) -> None:
    """Clear an administrative lock. Access then follows trial/paid dates — never auto-paid."""
    shop.admin_locked = False


def extend_trial(shop: Shop, days: int = 7, now: datetime | None = None) -> None:
    moment = now or utc_now()
    current_end = as_utc(shop.trial_ends_at) or moment
    if current_end < moment:
        current_end = moment
    shop.plan = "trial"
    if shop.trial_started_at is None:
        shop.trial_started_at = moment
    shop.trial_ends_at = current_end + timedelta(days=days)
    shop.grace_ends_at = shop.trial_ends_at + timedelta(days=GRACE_DAYS)
    shop.admin_locked = False


def shop_has_access(shop: Shop, now: datetime | None = None) -> bool:
    moment = now or utc_now()
    if shop.admin_locked:
        return False
    if shop.plan == "trial":
        ends = as_utc(shop.trial_ends_at)
        return ends is None or moment < ends
    if shop.plan == "active":
        expires = as_utc(shop.plan_expires_at)
        return expires is None or moment < expires
    return False


def shop_is_locked(shop: Shop, now: datetime | None = None) -> bool:
    return not shop_has_access(shop, now)


def normalize_plan_preference(value: str | None) -> str:
    if value in {"monthly", "paid", "subscribe"}:
        return "monthly"
    return "trial"


def shop_access_state(shop: Shop, now: datetime | None = None) -> str:
    """Admin-facing state. shops.plan remains trial | active | expired."""
    moment = now or utc_now()
    if shop.admin_locked:
        return "admin_locked"
    if shop.plan == "active":
        if shop_has_access(shop, moment):
            return "paid_active"
        return "paid_expired"
    if shop.plan == "trial":
        if shop_has_access(shop, moment):
            preference = shop.checkout_preference or "trial"
            if preference == "monthly" and shop.paid_at is None:
                return "pending_payment"
            return "trial_active"
        return "trial_expired"
    if shop.paid_at:
        return "paid_expired"
    return "trial_expired"


def delete_shop_cascade(db: Session, shop: Shop) -> None:
    shop_id = shop.id
    user_ids = list(db.scalars(select(User.id).where(User.shop_id == shop_id)).all())
    invoice_ids = list(db.scalars(select(Invoice.id).where(Invoice.shop_id == shop_id)).all())

    db.execute(delete(IdempotencyKey).where(IdempotencyKey.shop_id == shop_id))
    db.execute(delete(BillingOrder).where(BillingOrder.shop_id == shop_id))
    if invoice_ids:
        db.execute(delete(InvoiceItem).where(InvoiceItem.invoice_id.in_(invoice_ids)))
        db.execute(delete(Invoice).where(Invoice.id.in_(invoice_ids)))
    db.execute(delete(ReorderRequest).where(ReorderRequest.shop_id == shop_id))
    db.execute(delete(Payment).where(Payment.shop_id == shop_id))
    db.execute(delete(Product).where(Product.shop_id == shop_id))
    if user_ids:
        db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id.in_(user_ids)))
        db.execute(delete(AIUsageWindow).where(AIUsageWindow.user_id.in_(user_ids)))
        db.execute(delete(User).where(User.id.in_(user_ids)))
    db.delete(shop)


def sync_shop_plan(db: Session, shop: Shop, now: datetime | None = None) -> Shop | None:
    """Flip trial → expired and delete shops past grace. Returns None if deleted."""
    moment = now or utc_now()
    changed = False

    if shop.plan in {"free", "test"}:
        start_trial(shop, moment)
        changed = True

    if shop.plan == "trial" and shop.trial_ends_at is None:
        start_trial(shop, moment)
        changed = True

    if shop.plan == "trial":
        ends = as_utc(shop.trial_ends_at)
        if ends is not None and moment >= ends:
            shop.plan = "expired"
            if as_utc(shop.grace_ends_at) is None:
                shop.grace_ends_at = ends + timedelta(days=GRACE_DAYS)
            changed = True

    if shop.plan == "active":
        expires = as_utc(shop.plan_expires_at)
        if expires is not None and moment >= expires:
            shop.plan = "expired"
            if as_utc(shop.grace_ends_at) is None:
                shop.grace_ends_at = expires + timedelta(days=GRACE_DAYS)
            changed = True

    if shop.plan == "expired":
        grace = as_utc(shop.grace_ends_at)
        if grace is not None and moment >= grace:
            delete_shop_cascade(db, shop)
            db.commit()
            return None

    if changed:
        db.commit()
        db.refresh(shop)
    return shop


def is_demo_shop(db: Session, shop: Shop) -> bool:
    if shop.name == DEMO_SHOP_NAME:
        return True
    owner = db.scalar(
        select(User).where(User.shop_id == shop.id, User.email == DEMO_EMAIL)
    )
    return owner is not None


def migrate_legacy_plans(db: Session) -> None:
    now = utc_now()
    shops = list(db.scalars(select(Shop)).all())
    changed = False
    for shop in shops:
        if shop.plan in {"trial", "active", "expired"}:
            if shop.plan == "trial" and shop.trial_ends_at is None:
                start_trial(shop, now)
                changed = True
            continue
        if is_demo_shop(db, shop):
            shop.plan = "active"
            shop.plan_expires_at = None
            changed = True
            continue
        start_trial(shop, now)
        changed = True
    if changed:
        db.commit()


def ensure_demo_shop_active(db: Session) -> None:
    shop = db.scalar(select(Shop).where(Shop.name == DEMO_SHOP_NAME))
    if shop is None:
        return
    if shop.plan != "active" or shop.plan_expires_at is not None:
        shop.plan = "active"
        shop.plan_expires_at = None
        db.commit()
