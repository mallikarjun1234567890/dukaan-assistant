TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def test_upload_without_cloudinary(client, auth_a):
    response = client.post(
        "/api/uploads",
        headers=auth_a,
        files={"file": ("tiny.png", TINY_PNG, "image/png")},
        data={"kind": "shop_logo"},
    )
    assert response.status_code == 503
    assert "Cloudinary" in response.json()["detail"]


def test_product_upload_requires_product_id(client, auth_a):
    response = client.post(
        "/api/uploads",
        headers=auth_a,
        files={"file": ("tiny.png", TINY_PNG, "image/png")},
        data={"kind": "product"},
    )
    assert response.status_code == 400


def test_upload_rejects_unknown_kind(client, auth_a):
    response = client.post(
        "/api/uploads",
        headers=auth_a,
        files={"file": ("tiny.png", TINY_PNG, "image/png")},
        data={"kind": "employee"},
    )
    assert response.status_code == 400


def test_billing_is_optional(client, auth_a):
    config = client.get("/api/billing/config", headers=auth_a)
    assert config.status_code == 200
    body = config.json()
    assert body["enabled"] is False
    assert body["plan"] == "trial"
    order = client.post("/api/billing/order", headers=auth_a)
    assert order.status_code == 503
    assert "Razorpay" in order.json()["detail"]


def test_billing_requires_auth(client):
    response = client.get("/api/billing/config")
    assert response.status_code == 401


def test_billing_verify_sends_receipt(client, auth_a, monkeypatch):
    import hashlib
    import hmac

    from app.config import get_settings
    from app.services import email_service

    settings = get_settings()
    monkeypatch.setattr(settings, "razorpay_key_id", "rzp_test_dummy")
    monkeypatch.setattr(settings, "razorpay_key_secret", "rzp_test_secret")
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    sent: list[dict] = []
    monkeypatch.setattr(email_service, "send_email", lambda **kwargs: sent.append(kwargs))

    order_id = "order_test_1"
    payment_id = "pay_test_1"
    signature = hmac.new(
        b"rzp_test_secret",
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    response = client.post(
        "/api/billing/verify",
        headers=auth_a,
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )
    assert response.status_code == 200
    assert response.json()["plan"] == "active"
    assert len(sent) == 1
    assert "subscription" in sent[0]["subject"].lower()
    assert "Alpha Kirana" in sent[0]["html"]
