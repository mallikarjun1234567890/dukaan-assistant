from sqlalchemy import select

from app.models import Shop, User


def test_admin_can_list_shops(client, auth_admin):
    response = client.get("/api/admin/shops", headers=auth_admin)
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["items"]}
    assert "Alpha Kirana" in names
    assert "Beta Mart" in names


def test_admin_stats(client, auth_admin):
    response = client.get("/api/admin/stats", headers=auth_admin)
    assert response.status_code == 200
    body = response.json()
    assert body["total_shops"] >= 2
    assert "successful_pays" in body
    assert body["list_price_rupees"] == 499


def test_shop_owner_cannot_call_admin(client, auth_a):
    assert client.get("/api/admin/shops", headers=auth_a).status_code == 403
    assert client.get("/api/admin/stats", headers=auth_a).status_code == 403


def test_admin_cannot_use_shop_routes(client, auth_admin):
    assert client.get("/api/products", headers=auth_admin).status_code == 403
    assert client.get("/api/dashboard", headers=auth_admin).status_code == 403


def test_admin_lock_and_extend(client, auth_admin):
    created = client.post(
        "/api/auth/register",
        json={
            "email": "admin.lock@example.com",
            "password": "AdminLock@12345",
            "shop_name": "Admin Lock Shop",
            "owner_name": "Lockee",
            "phone": "9000011111",
        },
    )
    shop_id = created.json()["user"]["shop_id"]
    client.cookies.clear()
    locked = client.post(f"/api/admin/shops/{shop_id}/lock", headers=auth_admin)
    assert locked.status_code == 200
    assert locked.json()["plan"] == "expired"
    extended = client.post(f"/api/admin/shops/{shop_id}/extend-trial", headers=auth_admin)
    assert extended.status_code == 200
    assert extended.json()["plan"] == "trial"


def test_admin_mark_active(client, auth_admin):
    created = client.post(
        "/api/auth/register",
        json={
            "email": "admin.active@example.com",
            "password": "AdminActive@12345",
            "shop_name": "Admin Active Shop",
            "owner_name": "Activee",
            "phone": "9000022222",
        },
    )
    shop_id = created.json()["user"]["shop_id"]
    client.cookies.clear()
    response = client.post(f"/api/admin/shops/{shop_id}/mark-active", headers=auth_admin)
    assert response.status_code == 200
    assert response.json()["plan"] == "active"


def test_admin_delete_shop(client, auth_admin, db):
    created = client.post(
        "/api/auth/register",
        json={
            "email": "doomed.owner@example.com",
            "password": "Doomed@12345",
            "shop_name": "Doomed Kirana",
            "owner_name": "Doomed",
            "phone": "9000090000",
        },
    )
    assert created.status_code == 201
    shop_id = created.json()["user"]["shop_id"]
    client.cookies.clear()
    deleted = client.delete(f"/api/admin/shops/{shop_id}", headers=auth_admin)
    assert deleted.status_code == 200
    assert db.get(Shop, shop_id) is None
    assert db.scalar(select(User).where(User.email == "doomed.owner@example.com")) is None
    assert db.scalar(select(Shop).where(Shop.name == "Alpha Kirana")) is not None


def test_admin_login_rejects_shop_owner(client):
    response = client.post(
        "/api/admin/login",
        json={"email": "owner.a@test.local", "password": "OwnerA@12345"},
    )
    assert response.status_code == 401


def test_admin_login_success(client):
    response = client.post(
        "/api/admin/login",
        json={"email": "admin@dukaan.local", "password": "Admin@12345"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "platform_admin"
    assert response.json()["user"]["shop_id"] is None
