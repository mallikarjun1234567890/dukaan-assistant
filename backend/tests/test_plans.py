from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models import Product, Shop, User
from app.security import create_access_token
from app.services.subscription import SHOP_LOCKED_DETAIL, ensure_demo_shop_active


def _register(client, email: str, shop_name: str, phone: str = "9811111111"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "TrialShop@12345",
            "shop_name": shop_name,
            "owner_name": "Trial Owner",
            "phone": phone,
        },
    )
    assert response.status_code == 201
    return response


def _expire(db, shop_id: int, past_grace: bool = False) -> Shop:
    shop = db.get(Shop, shop_id)
    assert shop is not None
    now = datetime.now(timezone.utc)
    shop.plan = "expired"
    shop.trial_started_at = now - timedelta(days=40)
    shop.trial_ends_at = now - timedelta(days=10)
    shop.grace_ends_at = now - timedelta(days=1) if past_grace else now + timedelta(days=5)
    shop.plan_expires_at = None
    shop.paid_at = None
    db.commit()
    db.refresh(shop)
    return shop


def _auth_for_email(db, email: str) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == email))
    assert user is not None
    token = create_access_token(user_id=user.id, shop_id=user.shop_id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def test_register_starts_trial(client):
    response = _register(client, "trial.owner@example.com", "Trial Kirana")
    assert response.json()["user"]["plan"] == "trial"
    assert response.json()["user"]["shop_locked"] is False
    shop = client.get("/api/shop").json()
    assert shop["plan"] == "trial"
    assert shop["phone"] == "9811111111"
    assert shop["trial_ends_at"]


def test_upload_failure_does_not_undo_register(client):
    created = _register(client, "photo.owner@example.com", "Photo Kirana", "9822222222")
    shop_id = created.json()["user"]["shop_id"]
    upload = client.post(
        "/api/uploads",
        headers={"X-CSRF-Token": client.cookies.get("csrf_token", "")},
        files={"file": ("tiny.png", b"not-an-image", "image/png")},
        data={"kind": "shop_logo"},
    )
    assert upload.status_code in {400, 503}
    shop = client.get("/api/shop")
    assert shop.status_code == 200
    assert shop.json()["shop_id"] == shop_id


def test_expired_shop_cannot_use_products_invoices_ai(client, db):
    created = _register(client, "locked.owner@example.com", "Locked Kirana")
    shop_id = created.json()["user"]["shop_id"]
    _expire(db, shop_id)
    client.cookies.clear()
    headers = _auth_for_email(db, "locked.owner@example.com")
    products = client.get("/api/products", headers=headers)
    assert products.status_code == 403
    assert products.json()["detail"] == SHOP_LOCKED_DETAIL
    assert client.get("/api/invoices", headers=headers).status_code == 403
    assert client.post("/api/ai/chat", headers=headers, json={"message": "What is low stock?"}).status_code == 403
    assert client.get("/api/dashboard", headers=headers).status_code == 403


def test_expired_shop_can_read_settings_and_verify_billing(client, db, monkeypatch):
    import hashlib
    import hmac

    from app.config import get_settings

    created = _register(client, "paywall.owner@example.com", "Paywall Kirana")
    shop_id = created.json()["user"]["shop_id"]
    _expire(db, shop_id)
    client.cookies.clear()
    headers = _auth_for_email(db, "paywall.owner@example.com")
    settings = client.get("/api/shop", headers=headers)
    assert settings.status_code == 200
    assert settings.json()["shop_locked"] is True

    app_settings = get_settings()
    monkeypatch.setattr(app_settings, "razorpay_key_id", "rzp_test_dummy")
    monkeypatch.setattr(app_settings, "razorpay_key_secret", "rzp_test_secret")
    order_id = "order_lock_1"
    payment_id = "pay_lock_1"
    signature = hmac.new(
        b"rzp_test_secret",
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    verify = client.post(
        "/api/billing/verify",
        headers=headers,
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )
    assert verify.status_code == 200
    assert verify.json()["plan"] == "active"
    assert client.get("/api/products", headers=headers).status_code == 200


def test_demo_shop_stays_active(db):
    from app.security import hash_password
    from app.services.subscription import DEMO_EMAIL, DEMO_SHOP_NAME

    shop = db.scalar(select(Shop).where(Shop.name == DEMO_SHOP_NAME))
    if shop is None:
        shop = Shop(name=DEMO_SHOP_NAME, plan="free")
        db.add(shop)
        db.flush()
        db.add(
            User(
                email=DEMO_EMAIL,
                password_hash=hash_password("Demo@12345"),
                role="shop_owner",
                shop_id=shop.id,
            )
        )
        db.commit()
    shop.plan = "free"
    db.commit()
    ensure_demo_shop_active(db)
    db.expire_all()
    shop = db.scalar(select(Shop).where(Shop.name == DEMO_SHOP_NAME))
    assert shop.plan == "active"
    assert shop.plan_expires_at is None


def test_grace_delete_on_request_removes_only_that_shop(client, db):
    created = _register(client, "gone.owner@example.com", "Gone Kirana")
    shop_id = created.json()["user"]["shop_id"]
    _expire(db, shop_id, past_grace=True)
    headers = _auth_for_email(db, "gone.owner@example.com")
    response = client.get("/api/shop", headers=headers)
    assert response.status_code == 401
    db.expire_all()
    assert db.get(Shop, shop_id) is None
    assert db.scalar(select(User).where(User.email == "gone.owner@example.com")) is None
    assert db.scalar(select(Shop).where(Shop.name == "Alpha Kirana")) is not None
    assert db.scalar(select(Product).where(Product.sku == "RICE-5")) is not None
