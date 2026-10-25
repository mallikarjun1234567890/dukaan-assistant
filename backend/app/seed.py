"""Initialize tables and seed the demo shop without wiping existing data.

Run from the backend directory:

    python -m app.seed
"""

from __future__ import annotations

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.models import Product, Shop, User
from app.money import rupees_to_paise
from app.security import hash_password
from app.services.subscription import DEMO_EMAIL, DEMO_SHOP_NAME, ensure_demo_shop_active, migrate_legacy_plans

DEMO_PASSWORD = "Demo@12345"

SAMPLE_PRODUCTS = [
    {
        "name": "Aashirvaad Atta 10 kg",
        "sku": "ATTA-10KG",
        "category": "Staples",
        "selling_price": "520.00",
        "purchase_cost": "460.00",
        "stock_quantity": 24,
        "minimum_stock": 8,
        "supplier_name": "ITC Wholesale",
    },
    {
        "name": "Fortune Sunflower Oil 1 L",
        "sku": "OIL-1L",
        "category": "Staples",
        "selling_price": "148.00",
        "purchase_cost": "129.00",
        "stock_quantity": 3,
        "minimum_stock": 10,
        "supplier_name": "Adani Wilmar Depot",
    },
    {
        "name": "Tata Salt 1 kg",
        "sku": "SALT-1KG",
        "category": "Staples",
        "selling_price": "28.00",
        "purchase_cost": "22.00",
        "stock_quantity": 40,
        "minimum_stock": 12,
        "supplier_name": "Tata Consumer",
    },
    {
        "name": "Maggi Masala Noodles 70 g",
        "sku": "MAGGI-70",
        "category": "Packaged food",
        "selling_price": "14.00",
        "purchase_cost": "11.00",
        "stock_quantity": 6,
        "minimum_stock": 20,
        "supplier_name": "Nestle Distributor",
    },
    {
        "name": "Parle-G Gold 376 g",
        "sku": "PARLE-376",
        "category": "Packaged food",
        "selling_price": "45.00",
        "purchase_cost": "38.00",
        "stock_quantity": 30,
        "minimum_stock": 10,
        "supplier_name": "Parle Biscuits",
    },
    {
        "name": "Amul Taaza Milk 500 ml",
        "sku": "MILK-500",
        "category": "Dairy",
        "selling_price": "28.00",
        "purchase_cost": "25.00",
        "stock_quantity": 4,
        "minimum_stock": 15,
        "supplier_name": "Amul Dairy Route",
    },
    {
        "name": "Red Label Tea 250 g",
        "sku": "TEA-250",
        "category": "Beverages",
        "selling_price": "145.00",
        "purchase_cost": "122.00",
        "stock_quantity": 18,
        "minimum_stock": 6,
        "supplier_name": "HUL Distributor",
    },
    {
        "name": "Classmate Notebook A4 172 pages",
        "sku": "NB-A4-172",
        "category": "Stationery",
        "selling_price": "65.00",
        "purchase_cost": "48.00",
        "stock_quantity": 22,
        "minimum_stock": 8,
        "supplier_name": "ITC Stationery",
    },
    {
        "name": "Reynolds Ball Pens (box of 10)",
        "sku": "PEN-BOX10",
        "category": "Stationery",
        "selling_price": "50.00",
        "purchase_cost": "36.00",
        "stock_quantity": 2,
        "minimum_stock": 8,
        "supplier_name": "Reynolds Wholesale",
    },
    {
        "name": "Surf Excel Easy Wash 1 kg",
        "sku": "SURF-1KG",
        "category": "Household",
        "selling_price": "135.00",
        "purchase_cost": "112.00",
        "stock_quantity": 16,
        "minimum_stock": 6,
        "supplier_name": "HUL Distributor",
    },
]


def seed_platform_admin(db) -> bool:
    settings = get_settings()
    email = settings.admin_email.strip().lower()
    password = settings.admin_password
    if not email or not password:
        return False
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        return False
    db.add(
        User(
            email=email,
            password_hash=hash_password(password),
            display_name="Dukaan Admin",
            role="platform_admin",
            shop_id=None,
        )
    )
    db.commit()
    return True


def bootstrap() -> None:
    db = SessionLocal()
    try:
        migrate_legacy_plans(db)
        ensure_demo_shop_active(db)
        seed_platform_admin(db)
    finally:
        db.close()


def seed() -> None:
    settings = get_settings()
    settings.require_jwt_secret()
    init_db()

    db = SessionLocal()
    try:
        shop = db.scalar(select(Shop).where(Shop.name == DEMO_SHOP_NAME))
        created_shop = False
        if shop is None:
            shop = Shop(name=DEMO_SHOP_NAME, plan="active")
            db.add(shop)
            db.flush()
            created_shop = True
        shop.plan = "active"
        shop.plan_expires_at = None

        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        created_user = False
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                display_name="Sharma",
                role="shop_owner",
                shop_id=shop.id,
            )
            db.add(user)
            created_user = True

        existing_count = db.scalar(
            select(Product.id).where(Product.shop_id == shop.id).limit(1)
        )
        created_products = 0
        if existing_count is None:
            for item in SAMPLE_PRODUCTS:
                db.add(
                    Product(
                        shop_id=shop.id,
                        name=item["name"],
                        sku=item["sku"],
                        category=item["category"],
                        selling_price_paise=rupees_to_paise(item["selling_price"]),
                        purchase_cost_paise=rupees_to_paise(item["purchase_cost"]),
                        stock_quantity=item["stock_quantity"],
                        minimum_stock=item["minimum_stock"],
                        supplier_name=item["supplier_name"],
                    )
                )
                created_products += 1

        db.commit()
        bootstrap()
        print("Database ready.")
        print(f"Shop: {shop.name} (id={shop.id}) {'[created]' if created_shop else '[existing]'}")
        print(
            f"Demo owner: {DEMO_EMAIL} {'[created]' if created_user else '[existing — password not changed]'}"
        )
        if created_user:
            print(f"Demo password: {DEMO_PASSWORD}")
        print(f"Sample products added: {created_products}")
        print("Existing user and product data was not wiped.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
