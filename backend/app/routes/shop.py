"""Shop settings: hours and timezone owned by the authenticated shop."""

from fastapi import APIRouter, HTTPException

from app.dependencies import ActiveShopUser, CurrentUser, DBSession
from app.models import Shop
from app.schemas import ShopSettingsIn, ShopSettingsOut
from app.services.subscription import shop_is_locked
from app.shop_hours import shop_clock

router = APIRouter(prefix="/api/shop", tags=["shop"])


def _to_out(shop: Shop) -> ShopSettingsOut:
    clock = shop_clock(shop)
    return ShopSettingsOut(
        shop_id=shop.id,
        name=shop.name,
        phone=shop.phone or "",
        timezone=str(clock["timezone"]),
        opens_at=str(clock["opens_at"]),
        closes_at=str(clock["closes_at"]),
        weekly_off=str(clock["weekly_off"]),
        logo_url=shop.logo_url or "",
        plan=shop.plan or "trial",
        trial_started_at=shop.trial_started_at,
        trial_ends_at=shop.trial_ends_at,
        grace_ends_at=shop.grace_ends_at,
        plan_expires_at=shop.plan_expires_at,
        paid_at=shop.paid_at,
        shop_locked=shop_is_locked(shop),
        local_time=str(clock["local_time"]),
        weekday=str(clock["weekday"]),
        is_open=bool(clock["is_open"]),
    )


@router.get("", response_model=ShopSettingsOut)
def get_shop(user: CurrentUser, db: DBSession) -> ShopSettingsOut:
    shop = db.get(Shop, user.shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    return _to_out(shop)


@router.put("", response_model=ShopSettingsOut)
def update_shop(payload: ShopSettingsIn, user: ActiveShopUser, db: DBSession) -> ShopSettingsOut:
    shop = db.get(Shop, user.shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is not None:
            setattr(shop, field, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(shop)
    return _to_out(shop)
