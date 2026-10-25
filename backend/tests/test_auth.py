from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings
from app.security import JWT_ALGORITHM


def test_register_creates_isolated_shop(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "new.owner@example.com",
            "password": "NewShop@12345",
            "shop_name": "Patel General Store",
            "owner_name": "Rina Patel",
            "phone": "9876543210",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "new.owner@example.com"
    assert body["user"]["shop_name"] == "Patel General Store"
    assert body["user"]["shop_id"] != 1
    assert body["user"]["plan"] == "trial"
    shop = client.get("/api/shop")
    assert shop.status_code == 200
    assert shop.json()["phone"] == "9876543210"
    assert shop.json()["plan"] == "trial"


def test_register_sends_welcome_email(client, monkeypatch):
    from app.config import get_settings
    from app.services import email_service

    sent: list[dict] = []
    monkeypatch.setattr(get_settings(), "resend_api_key", "re_test")
    monkeypatch.setattr(email_service, "send_email", lambda **kwargs: sent.append(kwargs))

    response = client.post(
        "/api/auth/register",
        json={
            "email": "welcome.owner@example.com",
            "password": "Welcome@12345",
            "shop_name": "Welcome Kirana",
            "owner_name": "Asha",
            "phone": "9000000001",
        },
    )
    assert response.status_code == 201
    assert len(sent) == 1
    assert sent[0]["to"] == "welcome.owner@example.com"
    assert "Welcome Kirana" in sent[0]["subject"]


def test_register_still_works_if_email_fails(client, monkeypatch):
    from app.config import get_settings
    from app.services import email_service
    from app.services.email_service import EmailError

    monkeypatch.setattr(get_settings(), "resend_api_key", "re_test")

    def boom(**_kwargs):
        raise EmailError("Resend down")

    monkeypatch.setattr(email_service, "send_email", boom)
    response = client.post(
        "/api/auth/register",
        json={
            "email": "mailfail.owner@example.com",
            "password": "Welcome@12345",
            "shop_name": "Mail Fail Shop",
            "owner_name": "Mail Fail",
            "phone": "9000000002",
        },
    )
    assert response.status_code == 201


def test_register_rejects_duplicate_email(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "owner.a@test.local",
            "password": "Another@12345",
            "shop_name": "Copy Shop",
            "owner_name": "Copy Owner",
            "phone": "9000000003",
        },
    )
    assert response.status_code == 409


def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "owner.a@test.local", "password": "OwnerA@12345"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "owner.a@test.local"
    assert body["user"]["shop_name"] == "Alpha Kirana"
    assert "access_token" in response.cookies
    assert "csrf_token" in response.cookies
    assert body["csrf_token"]


def test_login_invalid_password(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "owner.a@test.local", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_protected_without_token(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 401


def test_invalid_jwt(client):
    response = client.get("/api/dashboard", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_forgot_password_requires_resend_key(client):
    response = client.post("/api/auth/forgot-password", json={"email": "owner.a@test.local"})
    assert response.status_code == 503
    assert "RESEND_API_KEY" in response.json()["detail"]


def test_reset_password_rejects_bad_token(client):
    response = client.post(
        "/api/auth/reset-password",
        json={"token": "not-a-real-reset-token-value", "password": "BrandNew@12345"},
    )
    assert response.status_code == 400


def test_reset_password_updates_login(client, db):
    from app.models import User
    from app.services.password_reset import issue_reset_token
    from sqlalchemy import select

    created = client.post(
        "/api/auth/register",
        json={
            "email": "reset.owner@example.com",
            "password": "OldShop@12345",
            "shop_name": "Reset Test Shop",
            "owner_name": "Reset Owner",
            "phone": "9000000004",
        },
    )
    assert created.status_code == 201
    user = db.scalar(select(User).where(User.email == "reset.owner@example.com"))
    token = issue_reset_token(db, user)
    response = client.post(
        "/api/auth/reset-password",
        json={"token": token, "password": "BrandNew@12345"},
    )
    assert response.status_code == 200
    old = client.post("/api/auth/login", json={"email": "reset.owner@example.com", "password": "OldShop@12345"})
    assert old.status_code == 401
    fresh = client.post("/api/auth/login", json={"email": "reset.owner@example.com", "password": "BrandNew@12345"})
    assert fresh.status_code == 200


def test_expired_jwt(client):
    settings = get_settings()
    payload = {
        "sub": "1",
        "shop_id": 1,
        "role": "shop_owner",
        "exp": int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)
    response = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()
