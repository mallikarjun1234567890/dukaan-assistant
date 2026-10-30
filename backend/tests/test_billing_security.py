import hashlib
import hmac
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.models import BillingOrder, Payment, Shop, User
from app.security import create_access_token
from app.services.subscription import SHOP_LOCKED_DETAIL, as_utc


SECRET = "rzp_test_secret"


def _register(client, email: str, shop_name: str, preference: str | None = None, phone: str = "9811100001"):
    payload = {
        "email": email,
        "password": "TrialShop@12345",
        "shop_name": shop_name,
        "owner_name": "Owner",
        "phone": phone,
    }
    if preference is not None:
        payload["plan_preference"] = preference
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response


def _sign(order_id: str, payment_id: str) -> str:
    return hmac.new(SECRET.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()


def _enable_billing(monkeypatch):
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "razorpay_key_id", "rzp_test_dummy")
    monkeypatch.setattr(settings, "razorpay_key_secret", SECRET)
    monkeypatch.setattr(settings, "razorpay_mode", "test")
    monkeypatch.setattr(settings, "billing_test_amount_paise", 100)
    monkeypatch.setattr(settings, "billing_list_amount_paise", 49900)
    return settings


def _insert_order(db, shop_id: int, order_id: str, amount: int = 100, environment: str = "test"):
    row = BillingOrder(
        shop_id=shop_id,
        razorpay_order_id=order_id,
        amount_paise=amount,
        currency="INR",
        environment=environment,
        status="created",
    )
    db.add(row)
    db.commit()
    return row


def _mock_captured(monkeypatch, order_id: str, amount: int = 100, status: str = "captured", currency: str = "INR"):
    monkeypatch.setattr(
        "app.services.billing_service.fetch_razorpay_payment",
        lambda _settings, _pid: {
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "status": status,
        },
    )


def _auth_header(client, db, email: str) -> dict[str, str]:
    client.cookies.clear()
    user = db.scalar(select(User).where(User.email == email))
    assert user is not None
    token = create_access_token(user_id=user.id, shop_id=user.shop_id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def _post_verify(client, db, email: str, payload: dict):
    return client.post("/api/billing/verify", headers=_auth_header(client, db, email), json=payload)


def test_register_trial_preference_starts_trial(client, db):
    created = _register(client, "pref.trial@example.com", "Pref Trial Shop", "trial")
    body = created.json()["user"]
    assert body["plan"] == "trial"
    assert body["checkout_preference"] == "trial"
    assert body["shop_locked"] is False
    shop = db.get(Shop, body["shop_id"])
    assert shop.trial_ends_at is not None
    remaining = as_utc(shop.trial_ends_at) - datetime.now(timezone.utc)
    assert timedelta(days=29) < remaining < timedelta(days=31)
    assert client.get("/api/products").status_code == 200


def test_register_monthly_preference_still_trial(client, db):
    created = _register(client, "pref.monthly@example.com", "Pref Monthly Shop", "monthly")
    body = created.json()["user"]
    assert body["plan"] == "trial"
    assert body["checkout_preference"] == "monthly"
    shop = db.get(Shop, body["shop_id"])
    assert shop.paid_at is None
    assert client.get("/api/products").status_code == 200


def test_register_omits_preference_defaults_trial(client):
    created = _register(client, "pref.default@example.com", "Pref Default Shop")
    assert created.json()["user"]["checkout_preference"] == "trial"
    assert created.json()["user"]["plan"] == "trial"


def test_duplicate_register_does_not_create_second_shop(client, db):
    _register(client, "dup.owner@example.com", "Dup Shop One", "monthly")
    again = client.post(
        "/api/auth/register",
        json={
            "email": "dup.owner@example.com",
            "password": "TrialShop@12345",
            "shop_name": "Dup Shop Two",
            "owner_name": "Owner",
            "phone": "9811100099",
            "plan_preference": "trial",
        },
    )
    assert again.status_code == 409
    shops = list(db.scalars(select(Shop).where(Shop.name.in_(["Dup Shop One", "Dup Shop Two"]))).all())
    assert len(shops) == 1
    assert shops[0].name == "Dup Shop One"


def test_skip_checkout_keeps_trial(client, db):
    created = _register(client, "skip.pay@example.com", "Skip Pay Shop", "monthly")
    shop_id = created.json()["user"]["shop_id"]
    shop = db.get(Shop, shop_id)
    ends = shop.trial_ends_at
    assert client.get("/api/products").status_code == 200
    db.refresh(shop)
    assert shop.plan == "trial"
    assert shop.trial_ends_at == ends
    assert db.scalar(select(func.count(Payment.id)).where(Payment.shop_id == shop_id)) == 0


def test_trial_clock_expiry_blocks_products_allows_billing(client, db):
    created = _register(client, "clock.owner@example.com", "Clock Shop")
    shop_id = created.json()["user"]["shop_id"]
    shop = db.get(Shop, shop_id)
    shop.trial_ends_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    headers = _auth_header(client, db, "clock.owner@example.com")
    products = client.get("/api/products", headers=headers)
    assert products.status_code == 403
    assert products.json()["detail"] == SHOP_LOCKED_DETAIL
    billing = client.get("/api/billing/config", headers=headers)
    assert billing.status_code == 200
    assert client.get("/api/shop", headers=headers).status_code == 200


def test_order_requires_auth(client):
    assert client.post("/api/billing/order").status_code == 401


def test_order_uses_server_amount(client, db, monkeypatch):
    created = _register(client, "order.amt@example.com", "Order Amt Shop", "monthly")
    _enable_billing(monkeypatch)

    class FakeOrders:
        def create(self, payload):
            assert payload["amount"] == 100
            assert payload["currency"] == "INR"
            return {"id": "order_amt_1", "amount": payload["amount"], "currency": "INR"}

    class FakeClient:
        def __init__(self, _auth=None):
            self.order = FakeOrders()

    monkeypatch.setattr("app.services.billing_service._client", lambda _settings: FakeClient())
    headers = _auth_header(client, db, "order.amt@example.com")
    response = client.post("/api/billing/order", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["amount"] == 100
    assert body["currency"] == "INR"
    assert body["environment"] == "test"
    shop_id = created.json()["user"]["shop_id"]
    stored = db.scalar(select(BillingOrder).where(BillingOrder.razorpay_order_id == "order_amt_1"))
    assert stored is not None
    assert stored.shop_id == shop_id
    assert stored.amount_paise == 100


def test_shop_cannot_verify_another_shops_order(client, db, monkeypatch):
    first = _register(client, "iso.a@example.com", "Iso A Shop")
    shop_a = first.json()["user"]["shop_id"]
    client.cookies.clear()
    second = _register(client, "iso.b@example.com", "Iso B Shop")
    _enable_billing(monkeypatch)
    _insert_order(db, shop_a, "order_iso_a")
    _mock_captured(monkeypatch, "order_iso_a")
    headers = _auth_header(client, db, "iso.b@example.com")
    response = client.post(
        "/api/billing/verify",
        headers=headers,
        json={
            "razorpay_order_id": "order_iso_a",
            "razorpay_payment_id": "pay_iso_a",
            "razorpay_signature": _sign("order_iso_a", "pay_iso_a"),
        },
    )
    assert response.status_code == 400
    shop = db.get(Shop, second.json()["user"]["shop_id"])
    assert shop.plan == "trial"


def test_valid_captured_payment_activates_paid(client, db, monkeypatch):
    created = _register(client, "ok.pay@example.com", "Ok Pay Shop", "monthly")
    shop_id = created.json()["user"]["shop_id"]
    trial_end = db.get(Shop, shop_id).trial_ends_at
    _enable_billing(monkeypatch)
    _insert_order(db, shop_id, "order_ok_1")
    _mock_captured(monkeypatch, "order_ok_1")
    headers = _auth_header(client, db, "ok.pay@example.com")
    response = client.post(
        "/api/billing/verify",
        headers=headers,
        json={
            "razorpay_order_id": "order_ok_1",
            "razorpay_payment_id": "pay_ok_1",
            "razorpay_signature": _sign("order_ok_1", "pay_ok_1"),
        },
    )
    assert response.status_code == 200
    assert response.json()["plan"] == "active"
    db.expire_all()
    shop = db.get(Shop, shop_id)
    assert shop.plan == "active"
    assert shop.trial_ends_at == trial_end
    assert shop.paid_at is not None
    assert client.get("/api/products", headers=headers).status_code == 200


def test_invalid_signature_rejected(client, db, monkeypatch):
    created = _register(client, "bad.sig@example.com", "Bad Sig Shop")
    shop_id = created.json()["user"]["shop_id"]
    _enable_billing(monkeypatch)
    _insert_order(db, shop_id, "order_sig_1")
    _mock_captured(monkeypatch, "order_sig_1")
    response = _post_verify(
        client,
        db,
        "bad.sig@example.com",
        {
            "razorpay_order_id": "order_sig_1",
            "razorpay_payment_id": "pay_sig_1",
            "razorpay_signature": "not-a-valid-signature",
        },
    )
    assert response.status_code == 400
    assert db.get(Shop, shop_id).plan == "trial"


def test_wrong_amount_and_currency_rejected(client, db, monkeypatch):
    created = _register(client, "bad.amt@example.com", "Bad Amt Shop")
    shop_id = created.json()["user"]["shop_id"]
    _enable_billing(monkeypatch)
    _insert_order(db, shop_id, "order_amt_bad")
    _mock_captured(monkeypatch, "order_amt_bad", amount=49900)
    wrong_amount = _post_verify(
        client,
        db,
        "bad.amt@example.com",
        {
            "razorpay_order_id": "order_amt_bad",
            "razorpay_payment_id": "pay_amt_bad",
            "razorpay_signature": _sign("order_amt_bad", "pay_amt_bad"),
        },
    )
    assert wrong_amount.status_code == 400
    _insert_order(db, shop_id, "order_cur_bad")
    _mock_captured(monkeypatch, "order_cur_bad", currency="USD")
    wrong_currency = _post_verify(
        client,
        db,
        "bad.amt@example.com",
        {
            "razorpay_order_id": "order_cur_bad",
            "razorpay_payment_id": "pay_cur_bad",
            "razorpay_signature": _sign("order_cur_bad", "pay_cur_bad"),
        },
    )
    assert wrong_currency.status_code == 400
    assert db.get(Shop, shop_id).plan == "trial"


def test_uncaptured_and_failed_payments_rejected(client, db, monkeypatch):
    created = _register(client, "fail.pay@example.com", "Fail Pay Shop")
    shop_id = created.json()["user"]["shop_id"]
    _enable_billing(monkeypatch)
    _insert_order(db, shop_id, "order_fail_1")
    _mock_captured(monkeypatch, "order_fail_1", status="failed")
    failed = _post_verify(
        client,
        db,
        "fail.pay@example.com",
        {
            "razorpay_order_id": "order_fail_1",
            "razorpay_payment_id": "pay_fail_1",
            "razorpay_signature": _sign("order_fail_1", "pay_fail_1"),
        },
    )
    assert failed.status_code == 400
    _insert_order(db, shop_id, "order_pend_1")
    _mock_captured(monkeypatch, "order_pend_1", status="authorized")
    pending = _post_verify(
        client,
        db,
        "fail.pay@example.com",
        {
            "razorpay_order_id": "order_pend_1",
            "razorpay_payment_id": "pay_pend_1",
            "razorpay_signature": _sign("order_pend_1", "pay_pend_1"),
        },
    )
    assert pending.status_code == 400
    assert db.get(Shop, shop_id).plan == "trial"


def test_razorpay_lookup_failure_does_not_activate(client, db, monkeypatch):
    from app.services.billing_service import BillingError

    created = _register(client, "rzp.down@example.com", "Rzp Down Shop")
    shop_id = created.json()["user"]["shop_id"]
    _enable_billing(monkeypatch)
    _insert_order(db, shop_id, "order_down_1")

    def _boom(_settings, _pid):
        raise BillingError("Payment could not be verified with Razorpay", status_code=503)

    monkeypatch.setattr("app.services.billing_service.fetch_razorpay_payment", _boom)
    response = _post_verify(
        client,
        db,
        "rzp.down@example.com",
        {
            "razorpay_order_id": "order_down_1",
            "razorpay_payment_id": "pay_down_1",
            "razorpay_signature": _sign("order_down_1", "pay_down_1"),
        },
    )
    assert response.status_code == 503
    assert db.get(Shop, shop_id).plan == "trial"


def test_payment_for_other_order_rejected(client, db, monkeypatch):
    created = _register(client, "mismatch.ord@example.com", "Mismatch Order Shop")
    shop_id = created.json()["user"]["shop_id"]
    _enable_billing(monkeypatch)
    _insert_order(db, shop_id, "order_m1")
    _mock_captured(monkeypatch, "order_other")
    response = _post_verify(
        client,
        db,
        "mismatch.ord@example.com",
        {
            "razorpay_order_id": "order_m1",
            "razorpay_payment_id": "pay_m1",
            "razorpay_signature": _sign("order_m1", "pay_m1"),
        },
    )
    assert response.status_code == 400
    assert db.get(Shop, shop_id).plan == "trial"


def test_duplicate_verify_is_idempotent(client, db, monkeypatch):
    from app.services import email_service

    created = _register(client, "dup.pay@example.com", "Dup Pay Shop")
    shop_id = created.json()["user"]["shop_id"]
    _enable_billing(monkeypatch)
    settings = _enable_billing(monkeypatch)
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    sent: list[dict] = []
    monkeypatch.setattr(email_service, "send_email", lambda **kwargs: sent.append(kwargs))
    _insert_order(db, shop_id, "order_dup_1")
    _mock_captured(monkeypatch, "order_dup_1")
    payload = {
        "razorpay_order_id": "order_dup_1",
        "razorpay_payment_id": "pay_dup_1",
        "razorpay_signature": _sign("order_dup_1", "pay_dup_1"),
    }
    first = _post_verify(client, db, "dup.pay@example.com", payload)
    assert first.status_code == 200
    db.expire_all()
    expires = db.get(Shop, shop_id).plan_expires_at
    second = _post_verify(client, db, "dup.pay@example.com", payload)
    assert second.status_code == 200
    assert second.json()["plan"] == "active"
    db.expire_all()
    shop = db.get(Shop, shop_id)
    assert shop.plan_expires_at == expires
    assert db.scalar(select(func.count(Payment.id)).where(Payment.shop_id == shop_id)) == 1
    assert len(sent) == 1


def test_concurrent_verify_does_not_duplicate_payment(client, db, monkeypatch):
    created = _register(client, "race.pay@example.com", "Race Pay Shop")
    shop_id = created.json()["user"]["shop_id"]
    _enable_billing(monkeypatch)
    _insert_order(db, shop_id, "order_race_1")
    _mock_captured(monkeypatch, "order_race_1")
    payload = {
        "razorpay_order_id": "order_race_1",
        "razorpay_payment_id": "pay_race_1",
        "razorpay_signature": _sign("order_race_1", "pay_race_1"),
    }

    headers = _auth_header(client, db, "race.pay@example.com")

    def _post():
        return client.post("/api/billing/verify", headers=headers, json=payload).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = list(pool.map(lambda _i: _post(), range(2)))
    assert codes.count(200) >= 1
    db.expire_all()
    assert db.scalar(select(func.count(Payment.id)).where(Payment.razorpay_payment_id == "pay_race_1")) == 1
    assert db.get(Shop, shop_id).plan == "active"


def test_payment_id_cannot_be_reused_on_another_shop(client, db, monkeypatch):
    first = _register(client, "reuse.a@example.com", "Reuse A")
    shop_a = first.json()["user"]["shop_id"]
    _enable_billing(monkeypatch)
    _insert_order(db, shop_a, "order_reuse_a")
    _mock_captured(monkeypatch, "order_reuse_a")
    paid = _post_verify(
        client,
        db,
        "reuse.a@example.com",
        {
            "razorpay_order_id": "order_reuse_a",
            "razorpay_payment_id": "pay_reuse_1",
            "razorpay_signature": _sign("order_reuse_a", "pay_reuse_1"),
        },
    )
    assert paid.status_code == 200
    second = _register(client, "reuse.b@example.com", "Reuse B")
    shop_b = second.json()["user"]["shop_id"]
    _insert_order(db, shop_b, "order_reuse_b")
    _mock_captured(monkeypatch, "order_reuse_b")
    reused = _post_verify(
        client,
        db,
        "reuse.b@example.com",
        {
            "razorpay_order_id": "order_reuse_b",
            "razorpay_payment_id": "pay_reuse_1",
            "razorpay_signature": _sign("order_reuse_b", "pay_reuse_1"),
        },
    )
    assert reused.status_code == 400
    assert db.get(Shop, shop_b).plan == "trial"


def test_admin_lock_blocks_and_unlock_restores_trial(client, db, auth_admin):
    created = _register(client, "lockme.owner@example.com", "Lock Me Shop")
    shop_id = created.json()["user"]["shop_id"]
    headers = _auth_header(client, db, "lockme.owner@example.com")
    locked = client.post(f"/api/admin/shops/{shop_id}/lock", headers=auth_admin)
    assert locked.json()["access_state"] == "admin_locked"
    assert client.get("/api/products", headers=headers).status_code == 403
    unlocked = client.post(f"/api/admin/shops/{shop_id}/unlock", headers=auth_admin)
    assert unlocked.json()["admin_locked"] is False
    assert unlocked.json()["plan"] == "trial"
    assert unlocked.json()["access_state"] == "trial_active"
    assert client.get("/api/products", headers=headers).status_code == 200


def test_admin_extend_after_expiry_restores_access(client, db, auth_admin):
    created = _register(client, "extend.owner@example.com", "Extend Shop")
    shop_id = created.json()["user"]["shop_id"]
    shop = db.get(Shop, shop_id)
    shop.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    headers = _auth_header(client, db, "extend.owner@example.com")
    assert client.get("/api/products", headers=headers).status_code == 403
    extended = client.post(f"/api/admin/shops/{shop_id}/extend-trial", headers=auth_admin)
    assert extended.status_code == 200
    assert extended.json()["plan"] == "trial"
    assert client.get("/api/products", headers=headers).status_code == 200


def test_test_payments_are_not_live_revenue(client, db, auth_admin, monkeypatch):
    created = _register(client, "rev.owner@example.com", "Rev Shop")
    shop_id = created.json()["user"]["shop_id"]
    _enable_billing(monkeypatch)
    _insert_order(db, shop_id, "order_rev_1")
    _mock_captured(monkeypatch, "order_rev_1")
    paid = _post_verify(
        client,
        db,
        "rev.owner@example.com",
        {
            "razorpay_order_id": "order_rev_1",
            "razorpay_payment_id": "pay_rev_1",
            "razorpay_signature": _sign("order_rev_1", "pay_rev_1"),
        },
    )
    assert paid.status_code == 200
    stats = client.get("/api/admin/stats", headers=auth_admin).json()
    assert stats["test_revenue_rupees"] >= 1
    assert stats["live_revenue_rupees"] == 0
    assert stats["list_revenue_rupees"] == 0
    assert stats["list_price_rupees"] == 499
