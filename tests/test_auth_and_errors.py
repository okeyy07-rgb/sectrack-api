from conftest import ADMIN, ANALYST, REPORTER


def assert_error_format(response, status, code):
    """Semua error harus punya bentuk yang sama."""
    assert response.status_code == status
    body = response.get_json()
    assert body["success"] is False
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str)


def test_health_tanpa_login(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "ok"


def test_tanpa_api_key_ditolak_401(client):
    assert_error_format(client.get("/api/v1/assets"), 401, "UNAUTHORIZED")


def test_api_key_salah_ditolak_401(client):
    res = client.get("/api/v1/assets", headers={"X-API-Key": "stk_ngawur"})
    assert_error_format(res, 401, "UNAUTHORIZED")


def test_reporter_tidak_boleh_tambah_aset_403(client):
    res = client.post(
        "/api/v1/assets", json={"name": "srv-x", "asset_type": "server"}, headers=REPORTER
    )
    assert_error_format(res, 403, "FORBIDDEN")


def test_analyst_tidak_boleh_lihat_audit_log_403(client):
    assert_error_format(client.get("/api/v1/audit-logs", headers=ANALYST), 403, "FORBIDDEN")


def test_endpoint_tidak_ada_404_format_json(client):
    assert_error_format(client.get("/api/v1/tidak-ada", headers=ADMIN), 404, "NOT_FOUND")


def test_resource_tidak_ada_404(client):
    assert_error_format(client.get("/api/v1/assets/9999", headers=ADMIN), 404, "NOT_FOUND")


def test_method_tidak_didukung_405(client):
    assert_error_format(client.put("/api/v1/assets", headers=ADMIN, json={}), 405, "METHOD_NOT_ALLOWED")


def test_body_bukan_json_415(client):
    res = client.post("/api/v1/assets", data="name=srv", headers=ADMIN)
    assert_error_format(res, 415, "UNSUPPORTED_MEDIA_TYPE")


def test_security_headers_ada(client):
    res = client.get("/api/v1/health")
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"


def test_password_dan_api_key_tidak_bocor(client):
    res = client.get("/api/v1/users", headers=ADMIN)
    assert res.status_code == 200
    for user in res.get_json()["data"]:
        assert "password_hash" not in user
        assert "api_key_hash" not in user
