def test_create_product_and_list(client, auth_a):
    response = client.post(
        "/api/products",
        headers=auth_a,
        json={
            "name": "Toor Dal 1 kg",
            "sku": "DAL-1KG",
            "category": "Staples",
            "selling_price": "160.50",
            "purchase_cost": "140.00",
            "stock_quantity": 12,
            "minimum_stock": 4,
            "supplier_name": "Pulse Traders",
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["selling_price"] == "160.50"
    assert created["is_low_stock"] is False

    listed = client.get("/api/products", headers=auth_a)
    assert listed.status_code == 200
    skus = [item["sku"] for item in listed.json()["items"]]
    assert "DAL-1KG" in skus


def test_product_validation_rejects_negative_price(client, auth_a):
    response = client.post(
        "/api/products",
        headers=auth_a,
        json={
            "name": "Bad Price",
            "sku": "BAD-PRICE",
            "category": "Staples",
            "selling_price": "-10.00",
            "purchase_cost": "5.00",
            "stock_quantity": 1,
            "minimum_stock": 1,
            "supplier_name": "X",
        },
    )
    assert response.status_code == 422


def test_product_requires_name(client, auth_a):
    response = client.post(
        "/api/products",
        headers=auth_a,
        json={
            "name": "   ",
            "sku": "NO-NAME",
            "category": "Staples",
            "selling_price": "10.00",
            "purchase_cost": "5.00",
            "stock_quantity": 1,
            "minimum_stock": 1,
        },
    )
    assert response.status_code == 422


def test_duplicate_sku_rejected(client, auth_a):
    payload = {
        "name": "Duplicate",
        "sku": "RICE-5",
        "category": "Staples",
        "selling_price": "10.00",
        "purchase_cost": "5.00",
        "stock_quantity": 1,
        "minimum_stock": 1,
        "supplier_name": "X",
    }
    response = client.post("/api/products", headers=auth_a, json=payload)
    assert response.status_code == 409
