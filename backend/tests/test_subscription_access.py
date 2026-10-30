from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.models import Payment, Shop
from app.services.subscription import (
    SHOP_LOCKED_DETAIL,
    PLAN_MONTH_DAYS,
    TRIAL_DAYS,
    activate_paid,
    as_utc,
    shop_access_state,
    shop_has_access,
)

from tests.test_billing_security import (
    _auth_header,
    _enable_billing,
    _insert_order,
    _mock_captured,
    _post_verify,
    _register,
    _sign,
)


NOW = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)


def test_access_function_does_not_or_together_trial_and_paid_dates():
    expired_paid = Shop(
        plan="active",
        admin_locked=False,
        trial_ends_at=NOW + timedelta(days=20),
        plan_expires_at=NOW - timedelta(minutes=1),
    )
    assert shop_has_access(expired_paid, NOW) is False
    assert shop_access_state(expired_paid, NOW) == "paid_expired"

    paid_after_trial_clock = Shop(
        plan="active",
        admin_locked=False,
        trial_ends_at=NOW - timedelta(days=1),
        plan_expires_at=NOW + timedelta(days=20),
    )
    assert shop_has_access(paid_after_trial_clock, NOW) is True
    assert shop_access_state(paid_after_trial_clock, NOW) == "paid_active"

    expired_plan = Shop(
        plan="expired",
        admin_locked=False,
        paid_at=NOW - timedelta(days=31),
        trial_ends_at=NOW + timedelta(days=10),
        plan_expires_at=NOW - timedelta(days=1),
    )
    assert shop_has_access(expired_plan, NOW) is False
    assert shop_access_state(expired_plan, NOW) == "paid_expired"


def test_activate_paid_keeps_trial_dates_and_sets_paid_window():
    shop = Shop(plan="trial", trial_started_at=NOW, trial_ends_at=NOW + timedelta(days=TRIAL_DAYS))
    trial_end = shop.trial_ends_at
    activate_paid(shop, NOW)
    assert shop.plan == "active"
    assert shop.trial_ends_at == trial_end
    assert shop.plan_expires_at == NOW + timedelta(days=PLAN_MONTH_DAYS)
    assert shop_has_access(shop, NOW) is True
    assert shop_has_access(shop, NOW + timedelta(days=31)) is False


def test_paid_shop_stays_usable_after_original_trial_date(client, db, monkeypatch):
    created = _register(client, "paid.pasttrial@example.com", "Paid Past Trial")
    shop_id = created.json()["user"]["shop_id"]
    _enable_billing(monkeypatch)
    _insert_order(db, shop_id, "order_past_trial")
    _mock_captured(monkeypatch, "order_past_trial")
    paid = _post_verify(
        client,
        db,
        "paid.pasttrial@example.com",
        {
            "razorpay_order_id": "order_past_trial",
            "razorpay_payment_id": "pay_past_trial",
            "razorpay_signature": _sign("order_past_trial", "pay_past_trial"),
        },
    )
    assert paid.status_code == 200
    shop = db.get(Shop, shop_id)
    shop.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=2)
    db.commit()
    headers = _auth_header(client, db, "paid.pasttrial@example.com")
    products = client.get("/api/products", headers=headers)
    assert products.status_code == 200
    me = client.get("/api/auth/me", headers=headers).json()
    assert me["plan"] == "active"
    assert me["shop_locked"] is False
    assert me["plan_expires_at"]


def test_expired_paid_does_not_fall_back_to_remaining_trial(client, db):
    created = _register(client, "paid.expired@example.com", "Paid Expired Shop")
    shop_id = created.json()["user"]["shop_id"]
    shop = db.get(Shop, shop_id)
    now = datetime.now(timezone.utc)
    shop.plan = "active"
    shop.paid_at = now - timedelta(days=31)
    shop.plan_expires_at = now - timedelta(minutes=5)
    shop.trial_ends_at = now + timedelta(days=20)
    shop.admin_locked = False
    db.commit()
    headers = _auth_header(client, db, "paid.expired@example.com")
    products = client.get("/api/products", headers=headers)
    assert products.status_code == 403
    assert products.json()["detail"] == SHOP_LOCKED_DETAIL
    billing = client.get("/api/billing/config", headers=headers)
    assert billing.status_code == 200
    me = client.get("/api/auth/me", headers=headers).json()
    assert me["plan"] == "expired"
    assert me["shop_locked"] is True
    db.expire_all()
    shop = db.get(Shop, shop_id)
    assert shop.plan == "expired"
    assert as_utc(shop.trial_ends_at) > now


def test_unlock_does_not_grant_paid_access(client, db, auth_admin):
    created = _register(client, "unlock.paid@example.com", "Unlock Paid Shop")
    shop_id = created.json()["user"]["shop_id"]
    shop = db.get(Shop, shop_id)
    now = datetime.now(timezone.utc)
    shop.plan = "active"
    shop.paid_at = now - timedelta(days=31)
    shop.plan_expires_at = now - timedelta(minutes=5)
    shop.admin_locked = True
    db.commit()
    client.cookies.clear()
    unlocked = client.post(f"/api/admin/shops/{shop_id}/unlock", headers=auth_admin)
    assert unlocked.status_code == 200
    assert unlocked.json()["admin_locked"] is False
    assert unlocked.json()["plan"] == "active"
    headers = _auth_header(client, db, "unlock.paid@example.com")
    assert client.get("/api/products", headers=headers).status_code == 403
    me = client.get("/api/auth/me", headers=headers).json()
    assert me["plan"] == "expired"
    assert me["shop_locked"] is True


def test_duplicate_verify_does_not_extend_paid_window(client, db, monkeypatch):
    created = _register(client, "dup.window@example.com", "Dup Window Shop")
    shop_id = created.json()["user"]["shop_id"]
    _enable_billing(monkeypatch)
    _insert_order(db, shop_id, "order_dup_window")
    _mock_captured(monkeypatch, "order_dup_window")
    payload = {
        "razorpay_order_id": "order_dup_window",
        "razorpay_payment_id": "pay_dup_window",
        "razorpay_signature": _sign("order_dup_window", "pay_dup_window"),
    }
    first = _post_verify(client, db, "dup.window@example.com", payload)
    assert first.status_code == 200
    db.expire_all()
    shop = db.get(Shop, shop_id)
    expires = shop.plan_expires_at
    second = _post_verify(client, db, "dup.window@example.com", payload)
    assert second.status_code == 200
    db.expire_all()
    shop = db.get(Shop, shop_id)
    assert shop.plan_expires_at == expires
    assert db.scalar(select(func.count(Payment.id)).where(Payment.shop_id == shop_id)) == 1
