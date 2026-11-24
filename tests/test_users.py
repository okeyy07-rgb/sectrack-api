from conftest import ADMIN


def test_buat_user_dan_pakai_api_key_baru(client):
    res = client.post(
        "/api/v1/users",
        json={"name": "Dimas Baru", "email": "Dimas@SecTrack.local", "password": "rahasia123", "role": "analyst"},
        headers=ADMIN,
    )
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["email"] == "dimas@sectrack.local"
    assert "password" not in data

    res = client.get("/api/v1/users/me", headers={"X-API-Key": data["api_key"]})
    assert res.status_code == 200
    assert res.get_json()["data"]["role"] == "analyst"


def test_email_duplikat_409(client):
    res = client.post(
        "/api/v1/users",
        json={"name": "Admin Lagi", "email": "admin@sectrack.local", "password": "rahasia123"},
        headers=ADMIN,
    )
    assert res.status_code == 409


def test_password_terlalu_pendek_422(client):
    res = client.post(
        "/api/v1/users", json={"name": "Pendek", "email": "p@sectrack.local", "password": "123"}, headers=ADMIN
    )
    assert res.status_code == 422
    assert "password" in res.get_json()["error"]["details"]


def test_rotate_key_membuat_key_lama_tidak_berlaku(client):
    res = client.post("/api/v1/users/4/rotate-key", headers=ADMIN)
    assert res.status_code == 200
    new_key = res.get_json()["data"]["api_key"]
    assert client.get("/api/v1/users/me", headers={"X-API-Key": "stk_demo_reporter_key"}).status_code == 401
    assert client.get("/api/v1/users/me", headers={"X-API-Key": new_key}).status_code == 200


def test_user_nonaktif_tidak_bisa_akses(client):
    client.patch("/api/v1/users/4", json={"is_active": False}, headers=ADMIN)
    assert client.get("/api/v1/users/me", headers={"X-API-Key": "stk_demo_reporter_key"}).status_code == 401


def test_hapus_user_yang_masih_punya_data_409(client):
    res = client.delete("/api/v1/users/2", headers=ADMIN)
    assert res.status_code == 409
