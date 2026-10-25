def test_low_stock_product_gets_recommendation(client, auth_a):
    created = client.post(
        "/api/products",
        headers=auth_a,
        json={
            "name": "Low Stock Sugar 1 kg",
            "sku": "SUGAR-LOW-1",
            "category": "Staples",
            "selling_price": "50.00",
            "purchase_cost": "40.00",
            "stock_quantity": 1,
            "minimum_stock": 6,
            "supplier_name": "Sugar Depot",
        },
    )
    assert created.status_code == 201
    response = client.get("/api/reorders", headers=auth_a)
    assert response.status_code == 200
    items = response.json()["items"]
    sugar = next(item for item in items if item["sku"] == "SUGAR-LOW-1")
    assert sugar["status"] == "pending"
    assert sugar["suggested_quantity"] == 11
    assert sugar["current_stock"] == 1


def test_approve_and_reject_are_one_time(client, auth_a):
    listed = client.get("/api/reorders", headers=auth_a).json()["items"]
    pending = next(item for item in listed if item["status"] == "pending")
    approved = client.post(f"/api/reorders/{pending['id']}/approve", headers=auth_a)
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    again = client.post(f"/api/reorders/{pending['id']}/approve", headers=auth_a)
    assert again.status_code == 400

    leftover = [item for item in client.get("/api/reorders", headers=auth_a).json()["items"] if item["status"] == "pending"]
    if leftover:
        rejected = client.post(f"/api/reorders/{leftover[0]['id']}/reject", headers=auth_a)
        assert rejected.status_code == 200
        assert rejected.json()["status"] == "rejected"
