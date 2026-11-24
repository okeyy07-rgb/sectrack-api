from conftest import ADMIN, ANALYST


def test_list_aset_dengan_pagination(client):
    res = client.get("/api/v1/assets?page=1&per_page=3", headers=ANALYST)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body["data"]) == 3
    assert body["meta"] == {"page": 1, "per_page": 3, "total": 8, "total_pages": 3}


def test_filter_dan_search_aset(client):
    res = client.get("/api/v1/assets?criticality=critical", headers=ANALYST)
    names = {a["name"] for a in res.get_json()["data"]}
    assert names == {"srv-web-01", "srv-db-01"}

    res = client.get("/api/v1/assets?q=cam", headers=ANALYST)
    assert [a["name"] for a in res.get_json()["data"]] == ["cam-lab-03"]


def test_sorting_aset_descending(client):
    res = client.get("/api/v1/assets?sort=-name&per_page=100", headers=ANALYST)
    names = [a["name"] for a in res.get_json()["data"]]
    assert names == sorted(names, reverse=True)


def test_sort_field_tidak_valid_400(client):
    res = client.get("/api/v1/assets?sort=password", headers=ANALYST)
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_QUERY_PARAM"


def test_crud_aset_berhasil(client):
    payload = {
        "name": "srv-backup-01",
        "asset_type": "server",
        "ip_address": "10.10.1.40",
        "criticality": "high",
        "location": "Ruang Server Lt.2",
    }
    res = client.post("/api/v1/assets", json=payload, headers=ANALYST)
    assert res.status_code == 201
    asset = res.get_json()["data"]
    assert res.headers["Location"] == f"/api/v1/assets/{asset['id']}"
    assert asset["owner"]["name"] == "Rina Analyst"  # default owner = pembuat

    res = client.patch(f"/api/v1/assets/{asset['id']}", json={"criticality": "critical"}, headers=ANALYST)
    assert res.status_code == 200
    assert res.get_json()["data"]["criticality"] == "critical"
    assert res.get_json()["data"]["ip_address"] == "10.10.1.40"  # PATCH tidak menghapus field lain

    res = client.delete(f"/api/v1/assets/{asset['id']}", headers=ADMIN)
    assert res.status_code == 204
    assert client.get(f"/api/v1/assets/{asset['id']}", headers=ADMIN).status_code == 404


def test_put_mengganti_seluruh_data(client):
    res = client.put("/api/v1/assets/6", json={"name": "ws-lab-a12", "asset_type": "workstation"}, headers=ANALYST)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["ip_address"] is None  # field opsional yang tidak dikirim jadi kosong
    assert data["criticality"] == "medium"


def test_validasi_input_aset_422(client):
    res = client.post(
        "/api/v1/assets",
        json={"name": "x", "asset_type": "kulkas", "ip_address": "999.1.1.1"},
        headers=ANALYST,
    )
    assert res.status_code == 422
    details = res.get_json()["error"]["details"]
    assert set(details) == {"name", "asset_type", "ip_address"}


def test_field_tak_dikenal_ditolak(client):
    res = client.post(
        "/api/v1/assets", json={"name": "srv-a", "asset_type": "server", "is_admin": True}, headers=ANALYST
    )
    assert res.status_code == 422
    assert "is_admin" in res.get_json()["error"]["details"]


def test_nama_aset_duplikat_409(client):
    res = client.post("/api/v1/assets", json={"name": "srv-web-01", "asset_type": "server"}, headers=ANALYST)
    assert res.status_code == 409


def test_owner_tidak_ada_422(client):
    res = client.post(
        "/api/v1/assets", json={"name": "srv-z", "asset_type": "server", "owner_id": 999}, headers=ANALYST
    )
    assert res.status_code == 422
    assert "owner_id" in res.get_json()["error"]["details"]


def test_hapus_aset_yang_punya_temuan_409(client):
    res = client.delete("/api/v1/assets/1", headers=ADMIN)  # srv-web-01 punya temuan
    assert res.status_code == 409
    assert res.get_json()["error"]["details"]["findings"] >= 1
