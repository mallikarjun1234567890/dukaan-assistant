from sqlalchemy import select

from app.models import Product


def test_cannot_read_other_shop_product(client, auth_a, db):
    other = db.scalar(select(Product).where(Product.sku == "SOAP-1"))
    response = client.get(f"/api/products/{other.id}", headers=auth_a)
    assert response.status_code == 404


def test_cannot_invoice_other_shop_product(client, auth_a, db):
    other = db.scalar(select(Product).where(Product.sku == "SOAP-1"))
    response = client.post(
        "/api/invoices",
        headers=auth_a,
        json={
            "idempotency_key": "invoice-key-cross-shop-005",
            "items": [{"product_id": other.id, "quantity": 1}],
        },
    )
    assert response.status_code == 404
    db.expire_all()
    other = db.scalar(select(Product).where(Product.sku == "SOAP-1"))
    assert other.stock_quantity == 10


def test_product_list_is_shop_scoped(client, auth_a, auth_b):
    a_items = client.get("/api/products", headers=auth_a).json()["items"]
    b_items = client.get("/api/products", headers=auth_b).json()["items"]
    assert all(item["sku"] != "SOAP-1" for item in a_items)
    assert all(item["sku"] != "RICE-5" for item in b_items)
