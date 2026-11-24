from conftest import ADMIN, ANALYST, REPORTER


# ------------------------------------------------------------------ vulnerabilities
def test_tambah_kerentanan_berhasil(client):
    res = client.post(
        "/api/v1/vulnerabilities",
        json={"cve_id": "cve-2024-3094", "title": "Backdoor pada xz-utils", "severity": "critical", "cvss_score": 10},
        headers=ANALYST,
    )
    assert res.status_code == 201
    assert res.get_json()["data"]["cve_id"] == "CVE-2024-3094"  # dinormalisasi ke huruf besar


def test_severity_tidak_cocok_dengan_cvss_422(client):
    res = client.post(
        "/api/v1/vulnerabilities",
        json={"title": "Contoh salah rating", "severity": "low", "cvss_score": 9.8},
        headers=ANALYST,
    )
    assert res.status_code == 422
    assert "severity" in res.get_json()["error"]["details"]


def test_format_cve_salah_422(client):
    res = client.post(
        "/api/v1/vulnerabilities", json={"cve_id": "CVE-123", "title": "Format salah", "severity": "low"}, headers=ANALYST
    )
    assert res.status_code == 422


def test_filter_kerentanan_min_cvss(client):
    res = client.get("/api/v1/vulnerabilities?min_cvss=9", headers=REPORTER)
    scores = [v["cvss_score"] for v in res.get_json()["data"]]
    assert scores and all(s >= 9 for s in scores)


# ------------------------------------------------------------------ findings
def test_catat_temuan_dan_resolve(client):
    res = client.post("/api/v1/findings", json={"asset_id": 6, "vulnerability_id": 8}, headers=ANALYST)
    assert res.status_code == 201
    finding = res.get_json()["data"]
    assert finding["status"] == "open"
    assert finding["resolved_at"] is None

    res = client.patch(f"/api/v1/findings/{finding['id']}", json={"status": "resolved"}, headers=ANALYST)
    assert res.status_code == 200
    assert res.get_json()["data"]["resolved_at"] is not None  # terisi otomatis


def test_temuan_duplikat_409(client):
    # srv-web-01 (id 1) sudah punya temuan CVE-2021-41773 (id 4) dari seed
    res = client.post("/api/v1/findings", json={"asset_id": 1, "vulnerability_id": 4}, headers=ANALYST)
    assert res.status_code == 409
    assert "existing_finding_id" in res.get_json()["error"]["details"]


def test_temuan_dengan_aset_tidak_ada_422(client):
    res = client.post("/api/v1/findings", json={"asset_id": 999, "vulnerability_id": 1}, headers=ANALYST)
    assert res.status_code == 422


def test_filter_temuan_berdasarkan_severity_dan_status(client):
    res = client.get("/api/v1/findings?severity=critical&status=open", headers=REPORTER)
    data = res.get_json()["data"]
    assert data
    assert all(f["vulnerability"]["severity"] == "critical" and f["status"] == "open" for f in data)


# ------------------------------------------------------------------ incidents
def test_reporter_bisa_lapor_insiden(client):
    res = client.post(
        "/api/v1/incidents",
        json={
            "title": "Wi-Fi lab minta login aneh",
            "description": "Muncul halaman login palsu saat konek ke Wi-Fi lab.",
            "category": "phishing",
            "severity": "medium",
            "occurred_at": "2026-11-20T09:00:00+07:00",
        },
        headers=REPORTER,
    )
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["status"] == "new"
    assert data["reporter"]["name"] == "Sari Staff"
    assert data["occurred_at"].startswith("2026-11-20T02:00:00")  # disimpan dalam UTC


def test_insiden_waktu_di_masa_depan_422(client):
    res = client.post(
        "/api/v1/incidents",
        json={
            "title": "Insiden dari masa depan",
            "description": "Seharusnya ditolak validasi.",
            "category": "other",
            "severity": "low",
            "occurred_at": "2099-01-01T00:00:00",
        },
        headers=REPORTER,
    )
    assert res.status_code == 422
    assert "occurred_at" in res.get_json()["error"]["details"]


def test_reporter_tidak_bisa_set_assignee_403(client):
    res = client.post(
        "/api/v1/incidents",
        json={
            "title": "Coba assign sendiri",
            "description": "Reporter mencoba menentukan assignee.",
            "category": "other",
            "severity": "low",
            "occurred_at": "2026-11-20T09:00:00",
            "assignee_id": 2,
        },
        headers=REPORTER,
    )
    assert res.status_code == 403


def test_assignee_harus_analyst_atau_admin_422(client):
    res = client.patch("/api/v1/incidents/1", json={"assignee_id": 4}, headers=ANALYST)  # id 4 = reporter
    assert res.status_code == 422


def test_update_status_insiden_tercatat_di_audit_log(client):
    res = client.patch("/api/v1/incidents/3", json={"status": "resolved"}, headers=ANALYST)
    assert res.status_code == 200
    assert res.get_json()["data"]["resolved_at"] is not None

    logs = client.get("/api/v1/audit-logs?entity=incident&action=update", headers=ADMIN).get_json()["data"]
    assert logs[0]["entity_id"] == 3
    assert logs[0]["detail"]["status"] == {"from": "new", "to": "resolved"}
    assert logs[0]["user"]["name"] == "Rina Analyst"


def test_filter_insiden_rentang_tanggal_dan_format_salah(client):
    res = client.get("/api/v1/incidents?from=2000-01-01&category=phishing", headers=REPORTER)
    assert res.status_code == 200
    assert all(i["category"] == "phishing" for i in res.get_json()["data"])

    res = client.get("/api/v1/incidents?from=kemarin", headers=REPORTER)
    assert res.status_code == 400


def test_stats_summary(client):
    res = client.get("/api/v1/stats/summary", headers=REPORTER)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["total_assets"] == 8
    assert data["top_risky_assets"][0]["risk_score"] >= data["top_risky_assets"][-1]["risk_score"]
