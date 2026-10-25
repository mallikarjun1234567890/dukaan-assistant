"""Platform admin: list shops and subscription controls. No shop editor or AI."""

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select

from app.dependencies import AppSettings, DBSession, PlatformAdmin
from app.models import Payment, Shop, User
from app.routes.auth import _set_auth_cookies, user_to_out
from app.schemas import (
    AdminShopListOut,
    AdminShopOut,
    AdminStatsOut,
    AuthResponse,
    LoginRequest,
)
from app.security import create_access_token, new_csrf_token, verify_password
from app.services.subscription import (
    LIST_PRICE_RUPEES,
    TEST_CHARGE_RUPEES,
    delete_shop_cascade,
    extend_trial,
    lock_shop,
    mark_active_manual,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _shop_or_404(db, shop_id: int) -> Shop:
    shop = db.get(Shop, shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


def _owner_email(db, shop_id: int) -> str:
    owner = db.scalar(
        select(User).where(User.shop_id == shop_id, User.role == "shop_owner")
    )
    return owner.email if owner else ""


def _to_out(db, shop: Shop) -> AdminShopOut:
    return AdminShopOut(
        id=shop.id,
        name=shop.name,
        owner_email=_owner_email(db, shop.id),
        phone=shop.phone or "",
        plan=shop.plan,
        trial_ends_at=shop.trial_ends_at,
        grace_ends_at=shop.grace_ends_at,
        plan_expires_at=shop.plan_expires_at,
        paid_at=shop.paid_at,
        created_at=shop.created_at,
    )


@router.post("/login", response_model=AuthResponse)
def admin_login(
    payload: LoginRequest,
    response: Response,
    db: DBSession,
    settings: AppSettings,
) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if (
        user is None
        or user.role != "platform_admin"
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin email or password",
        )

    access_token = create_access_token(
        user_id=user.id, shop_id=None, role=user.role, settings=settings
    )
    csrf_token = new_csrf_token()
    _set_auth_cookies(response, access_token, csrf_token, settings)
    return AuthResponse(user=user_to_out(user, db), csrf_token=csrf_token)


@router.get("/stats", response_model=AdminStatsOut)
def admin_stats(_admin: PlatformAdmin, db: DBSession) -> AdminStatsOut:
    total = db.scalar(select(func.count(Shop.id))) or 0
    trial = db.scalar(select(func.count(Shop.id)).where(Shop.plan == "trial")) or 0
    active = db.scalar(select(func.count(Shop.id)).where(Shop.plan == "active")) or 0
    expired = db.scalar(select(func.count(Shop.id)).where(Shop.plan == "expired")) or 0
    pays = db.scalar(select(func.count(Payment.id))) or 0
    return AdminStatsOut(
        total_shops=total,
        trial_count=trial,
        active_count=active,
        expired_count=expired,
        successful_pays=pays,
        test_revenue_rupees=pays * TEST_CHARGE_RUPEES,
        list_revenue_rupees=pays * LIST_PRICE_RUPEES,
        list_price_rupees=LIST_PRICE_RUPEES,
    )


@router.get("/shops", response_model=AdminShopListOut)
def list_shops(_admin: PlatformAdmin, db: DBSession) -> AdminShopListOut:
    shops = list(db.scalars(select(Shop).order_by(Shop.created_at.desc())).all())
    return AdminShopListOut(items=[_to_out(db, shop) for shop in shops])


@router.post("/shops/{shop_id}/lock", response_model=AdminShopOut)
def lock(shop_id: int, _admin: PlatformAdmin, db: DBSession) -> AdminShopOut:
    shop = _shop_or_404(db, shop_id)
    lock_shop(shop)
    db.commit()
    db.refresh(shop)
    return _to_out(db, shop)


@router.post("/shops/{shop_id}/extend-trial", response_model=AdminShopOut)
def extend(shop_id: int, _admin: PlatformAdmin, db: DBSession) -> AdminShopOut:
    shop = _shop_or_404(db, shop_id)
    extend_trial(shop)
    db.commit()
    db.refresh(shop)
    return _to_out(db, shop)


@router.post("/shops/{shop_id}/mark-active", response_model=AdminShopOut)
def mark_active(shop_id: int, _admin: PlatformAdmin, db: DBSession) -> AdminShopOut:
    shop = _shop_or_404(db, shop_id)
    mark_active_manual(shop)
    db.commit()
    db.refresh(shop)
    return _to_out(db, shop)


@router.delete("/shops/{shop_id}")
def delete_shop(shop_id: int, _admin: PlatformAdmin, db: DBSession) -> dict[str, str]:
    shop = _shop_or_404(db, shop_id)
    name = shop.name
    delete_shop_cascade(db, shop)
    db.commit()
    return {"detail": f"Deleted shop {name}"}
