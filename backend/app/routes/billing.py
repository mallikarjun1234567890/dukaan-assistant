"""Razorpay checkout. Advertised price is ₹499; test mode charges the configured test amount."""

from fastapi import APIRouter

from app.dependencies import AppSettings, CurrentUser, DBSession
from app.models import Shop
from app.schemas import BillingConfigOut, BillingOrderOut, BillingVerifyIn
from app.services.billing_service import (
    BillingError,
    billing_enabled,
    billing_environment,
    charge_rupees,
    checkout_amount_paise,
    create_checkout_order,
    list_price_rupees,
    receipt_amount_rupees,
    verify_checkout_payment,
)
from app.services.subscription import shop_is_locked

router = APIRouter(prefix="/api/billing", tags=["billing"])


def _shop_or_404(db, shop_id: int | None) -> Shop:
    from fastapi import HTTPException

    shop = db.get(Shop, shop_id) if shop_id else None
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@router.get("/config", response_model=BillingConfigOut)
def billing_config(user: CurrentUser, db: DBSession, settings: AppSettings) -> BillingConfigOut:
    shop = _shop_or_404(db, user.shop_id)
    return BillingConfigOut(
        enabled=billing_enabled(settings),
        key_id=settings.razorpay_key_id if billing_enabled(settings) else "",
        plan=shop.plan,
        checkout_preference=shop.checkout_preference or "trial",
        amount_rupees=charge_rupees(settings),
        amount_paise=checkout_amount_paise(settings),
        list_price_rupees=list_price_rupees(settings),
        environment=billing_environment(settings),
        trial_ends_at=shop.trial_ends_at,
        grace_ends_at=shop.grace_ends_at,
        plan_expires_at=shop.plan_expires_at,
        paid_at=shop.paid_at,
        shop_locked=shop_is_locked(shop),
    )


@router.post("/order", response_model=BillingOrderOut)
def create_order(user: CurrentUser, db: DBSession, settings: AppSettings) -> BillingOrderOut:
    shop = _shop_or_404(db, user.shop_id)
    row = create_checkout_order(db, shop, settings)
    return BillingOrderOut(
        order_id=row.razorpay_order_id,
        amount=row.amount_paise,
        currency=row.currency,
        key_id=settings.razorpay_key_id,
        environment=row.environment,
    )


@router.post("/verify")
def verify_payment(
    payload: BillingVerifyIn, user: CurrentUser, db: DBSession, settings: AppSettings
) -> dict[str, str]:
    shop = _shop_or_404(db, user.shop_id)
    try:
        plan, newly_captured = verify_checkout_payment(
            db,
            shop,
            settings,
            order_id=payload.razorpay_order_id,
            payment_id=payload.razorpay_payment_id,
            signature=payload.razorpay_signature,
        )
    except BillingError:
        raise
    if newly_captured:
        from app.services.email_service import deliver, send_payment_receipt

        deliver(
            settings,
            lambda: send_payment_receipt(
                settings=settings,
                to=user.email,
                shop_name=shop.name,
                amount_rupees=receipt_amount_rupees(settings),
                plan=plan,
            ),
        )
    return {"detail": "Subscription is now active", "plan": plan}
