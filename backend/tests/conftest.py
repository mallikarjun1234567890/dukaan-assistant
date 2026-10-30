"""Test fixtures using an isolated SQLite database."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

TEST_SECRET = "test-jwt-secret-key-must-be-32chars!"
_TMP = Path(tempfile.mkdtemp(prefix="dukaan-test-"))
os.environ["JWT_SECRET"] = TEST_SECRET
# Throwaway file for pytest only. Never the shop Postgres database.
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["HF_TOKEN"] = ""
os.environ["OLLAMA_BASE_URL"] = ""
os.environ["CLOUDINARY_CLOUD_NAME"] = ""
os.environ["CLOUDINARY_API_KEY"] = ""
os.environ["CLOUDINARY_API_SECRET"] = ""
os.environ["RAZORPAY_KEY_ID"] = ""
os.environ["RESEND_API_KEY"] = ""
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["RAZORPAY_KEY_SECRET"] = ""
os.environ["ADMIN_EMAIL"] = "admin@dukaan.local"
os.environ["ADMIN_PASSWORD"] = "Admin@12345"
os.environ["COOKIE_SECURE"] = "false"
os.environ["DEBUG"] = "false"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Product, Shop, User  # noqa: E402
from app.money import rupees_to_paise  # noqa: E402
from app.security import create_access_token, hash_password  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()
    db = SessionLocal()
    try:
        shop_a = Shop(name="Alpha Kirana")
        shop_b = Shop(name="Beta Mart")
        db.add_all([shop_a, shop_b])
        db.flush()
        owner_a = User(
            email="owner.a@test.local",
            password_hash=hash_password("OwnerA@12345"),
            role="shop_owner",
            shop_id=shop_a.id,
        )
        owner_b = User(
            email="owner.b@test.local",
            password_hash=hash_password("OwnerB@12345"),
            role="shop_owner",
            shop_id=shop_b.id,
        )
        admin = User(
            email="admin@dukaan.local",
            password_hash=hash_password("Admin@12345"),
            display_name="Dukaan Admin",
            role="platform_admin",
            shop_id=None,
        )
        db.add_all([owner_a, owner_b, admin])
        db.flush()
        db.add_all(
            [
                Product(
                    shop_id=shop_a.id,
                    name="Rice 5 kg",
                    sku="RICE-5",
                    category="Staples",
                    selling_price_paise=rupees_to_paise("350.00"),
                    purchase_cost_paise=rupees_to_paise("300.00"),
                    stock_quantity=20,
                    minimum_stock=5,
                    supplier_name="Grain Co",
                ),
                Product(
                    shop_id=shop_a.id,
                    name="Cooking Oil 1 L",
                    sku="OIL-1",
                    category="Staples",
                    selling_price_paise=rupees_to_paise("150.00"),
                    purchase_cost_paise=rupees_to_paise("120.00"),
                    stock_quantity=2,
                    minimum_stock=8,
                    supplier_name="Oil Depot",
                ),
                Product(
                    shop_id=shop_b.id,
                    name="Secret Soap",
                    sku="SOAP-1",
                    category="Household",
                    selling_price_paise=rupees_to_paise("40.00"),
                    purchase_cost_paise=rupees_to_paise("25.00"),
                    stock_quantity=10,
                    minimum_stock=3,
                    supplier_name="Other Supplier",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _token_for(email: str) -> str:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        return create_access_token(user_id=user.id, shop_id=user.shop_id, role=user.role)
    finally:
        db.close()


@pytest.fixture
def auth_a() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for('owner.a@test.local')}"}


@pytest.fixture
def auth_b() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for('owner.b@test.local')}"}


@pytest.fixture
def auth_admin() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for('admin@dukaan.local')}"}


@pytest.fixture
def shop_a_products(db):
    shop = db.scalar(select(Shop).where(Shop.name == "Alpha Kirana"))
    products = list(db.scalars(select(Product).where(Product.shop_id == shop.id)).all())
    return {product.sku: product for product in products}
