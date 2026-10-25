from sqlalchemy import select

from app.models import Product


def _product(db, sku: str) -> Product:
    product = db.scalar(select(Product).where(Product.sku == sku))
    assert product is not None
    return product


def test_invoice_totals_and_stock_deduction(client, auth_a, db):
    rice = _product(db, "RICE-5")
    starting = rice.stock_quantity
    response = client.post(
        "/api/invoices",
        headers=auth_a,
        json={
            "idempotency_key": "invoice-key-unique-001",
            "items": [{"product_id": rice.id, "quantity": 2}],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["subtotal"] == "700.00"
    assert body["total"] == "700.00"
    assert body["items"][0]["product_name"] == "Rice 5 kg"

    db.expire_all()
    rice = _product(db, "RICE-5")
    assert rice.stock_quantity == starting - 2


def test_insufficient_stock_rejected(client, auth_a, db):
    oil = _product(db, "OIL-1")
    starting = oil.stock_quantity
    response = client.post(
        "/api/invoices",
        headers=auth_a,
        json={
            "idempotency_key": "invoice-key-insufficient-002",
            "items": [{"product_id": oil.id, "quantity": starting + 5}],
        },
    )
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]
    db.expire_all()
    oil = _product(db, "OIL-1")
    assert oil.stock_quantity == starting


def test_atomic_stock_deduction_rolls_back(client, auth_a, db):
    rice = _product(db, "RICE-5")
    oil = _product(db, "OIL-1")
    rice_start = rice.stock_quantity
    oil_start = oil.stock_quantity
    response = client.post(
        "/api/invoices",
        headers=auth_a,
        json={
            "idempotency_key": "invoice-key-atomic-003",
            "items": [
                {"product_id": rice.id, "quantity": 1},
                {"product_id": oil.id, "quantity": oil_start + 1},
            ],
        },
    )
    assert response.status_code == 400
    db.expire_all()
    rice = _product(db, "RICE-5")
    oil = _product(db, "OIL-1")
    assert rice.stock_quantity == rice_start
    assert oil.stock_quantity == oil_start


def test_duplicate_invoice_does_not_deduct_twice(client, auth_a, db):
    rice = _product(db, "RICE-5")
    starting = rice.stock_quantity
    payload = {
        "idempotency_key": "invoice-key-duplicate-004",
        "items": [{"product_id": rice.id, "quantity": 1}],
    }
    first = client.post("/api/invoices", headers=auth_a, json=payload)
    second = client.post("/api/invoices", headers=auth_a, json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    db.expire_all()
    rice = _product(db, "RICE-5")
    assert rice.stock_quantity == starting - 1
