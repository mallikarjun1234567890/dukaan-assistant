"""Razorpay checkout for the ₹499/month plan. Test mode charges ₹1."""

import hashlib
import hmac

from fastapi import APIRouter, HTTPException

from app.dependencies import AppSettings, CurrentUser, DBSession
from app.models import Payment, Shop
from app.schemas import BillingConfigOut, BillingOrderOut, BillingVerifyIn
from app.services.subscription import (
    LIST_PRICE_RUPEES,
    TEST_AMOUNT_PAISE,
    TEST_CHARGE_RUPEES,
    activate_paid,
    shop_is_locked,
)

router = APIRouter(prefix="/api/billing", tags=["billing"])


def _enabled(settings) -> bool:
    return bool(settings.razorpay_key_id.strip() and settings.razorpay_key_secret.strip())


def _shop_or_404(db, shop_id: int | None) -> Shop:
    shop = db.get(Shop, shop_id) if shop_id else None
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@router.get("/config", response_model=BillingConfigOut)
def billing_config(user: CurrentUser, db: DBSession, settings: AppSettings) -> BillingConfigOut:
    shop = _shop_or_404(db, user.shop_id)
    return BillingConfigOut(
        enabled=_enabled(settings),
        key_id=settings.razorpay_key_id if _enabled(settings) else "",
        plan=shop.plan,
        amount_rupees=TEST_CHARGE_RUPEES,
        list_price_rupees=LIST_PRICE_RUPEES,
        trial_ends_at=shop.trial_ends_at,
        grace_ends_at=shop.grace_ends_at,
        plan_expires_at=shop.plan_expires_at,
        paid_at=shop.paid_at,
        shop_locked=shop_is_locked(shop),
    )


@router.post("/order", response_model=BillingOrderOut)
def create_order(user: CurrentUser, db: DBSession, settings: AppSettings) -> BillingOrderOut:
    _shop_or_404(db, user.shop_id)
    if not _enabled(settings):
        raise HTTPException(
            status_code=503,
            detail="Razorpay test keys are not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.",
        )
    try:
        import razorpay
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Razorpay SDK is not installed") from exc

    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    order = client.order.create(
        {"amount": TEST_AMOUNT_PAISE, "currency": "INR", "payment_capture": 1}
    )
    return BillingOrderOut(
        order_id=order["id"],
        amount=order["amount"],
        currency=order["currency"],
        key_id=settings.razorpay_key_id,
    )


@router.post("/verify")
def verify_payment(
    payload: BillingVerifyIn, user: CurrentUser, db: DBSession, settings: AppSettings
) -> dict[str, str]:
    if not _enabled(settings):
        raise HTTPException(status_code=503, detail="Razorpay is not configured")
    body = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected = hmac.new(
        settings.razorpay_key_secret.encode(), body.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, payload.razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment signature is invalid")
    shop = _shop_or_404(db, user.shop_id)
    activate_paid(shop)
    db.add(
        Payment(
            shop_id=shop.id,
            amount_paise=TEST_AMOUNT_PAISE,
            plan=shop.plan,
        )
    )
    db.commit()
    from app.services.email_service import deliver, send_payment_receipt

    deliver(
        settings,
        lambda: send_payment_receipt(
            settings=settings,
            to=user.email,
            shop_name=shop.name,
            amount_rupees=TEST_CHARGE_RUPEES,
            plan=shop.plan,
        ),
    )
    return {"detail": "Subscription is now active", "plan": shop.plan}
