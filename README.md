# SecTrack API

REST API sederhana (MVP) untuk membantu admin lab/jaringan kampus **mencatat aset TI, katalog kerentanan, temuan kerentanan per aset, laporan insiden keamanan, dan jejak audit**. Dibuat untuk UTS Pemrograman Web Lanjut (TK070).

**Demo online:** https://nazhwa.pythonanywhere.com (Swagger UI: https://nazhwa.pythonanywhere.com/docs, health check: `/api/v1/health`). Pakai salah satu API key demo (lihat daftar user demo di bawah) lewat tombol *Authorize*.

> Semua data di project ini **simulasi**. Tidak ada scanning atau pengujian ke sistem pihak lain.

## Fitur utama

- CRUD **Assets**, **Vulnerabilities**, **Findings**, **Incidents**, dan **Users**
- **Audit log** otomatis untuk setiap create/update/delete (read-only lewat API)
- **Search, filter, sorting, dan pagination** di semua endpoint list (`?q=`, `?status=`, `?sort=-created_at`, `?page=&per_page=`)
- **Autentikasi API key** (`X-API-Key`) + **otorisasi berbasis role** (admin, analyst, reporter)
- **Validasi input** (Marshmallow) dan **format error yang konsisten**
- Aturan integritas data: foreign key, unique, check constraint, larangan hapus data yang masih direferensikan
- Endpoint **ringkasan dashboard** (`/api/v1/stats/summary`) dengan skor risiko per aset
- Dokumentasi **OpenAPI 3** + **Swagger UI** (`/docs`) + **Postman collection**
- **43 automated test** (pytest)

## Tech stack

| Bagian | Yang dipakai |
|---|---|
| Framework | Python 3.10+ / Flask 3 |
| ORM | SQLAlchemy 2 lewat Flask-SQLAlchemy |
| Migration | Flask-Migrate (Alembic) |
| Validasi & serialisasi | Marshmallow 4 |
| Database | SQLite (lokal), bisa diganti MySQL/MariaDB lewat `DATABASE_URL` |
| Testing | pytest |

## Struktur folder (MVC)

```
sectrack-api/
├── app/
│   ├── __init__.py          # application factory (create_app)
│   ├── config.py            # konfigurasi dari environment
│   ├── extensions.py        # objek db & migrate, pragma foreign key SQLite
│   ├── models/              # M = Model (tabel database lewat ORM)
│   ├── views/               # V = View (schema JSON: validasi input & format output)
│   ├── controllers/         # C = Controller (blueprint/route + logika bisnis)
│   ├── utils/               # error handler, keamanan, helper query, audit log
│   ├── seed.py              # data simulasi
│   └── cli.py               # perintah flask init-db / seed / create-admin
├── migrations/              # file migration Alembic
├── tests/                   # automated test (pytest)
├── docs/                    # ERD, OpenAPI spec, Postman collection
├── wsgi.py                  # entry point
└── requirements.txt
```

Alurnya: **request → controller → (validasi di view/schema) → model/ORM → database → view/schema → JSON response**.

## Instalasi

Butuh Python 3.10 atau lebih baru.

```bash
git clone https://github.com/okeyy07-rgb/sectrack-api.git
cd sectrack-api

python -m venv venv
# Windows (CMD / PowerShell)
venv\Scripts\activate
# macOS / Linux / Git Bash
source venv/bin/activate

pip install -r requirements.txt
```

## Konfigurasi

Salin `.env.example` menjadi `.env`, lalu sesuaikan:

```bash
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```

| Variabel | Keterangan | Default |
|---|---|---|
| `SECRET_KEY` | kunci rahasia Flask | `dev-only-ganti-di-production` |
| `DATABASE_URL` | URL database SQLAlchemy | `sqlite:///instance/sectrack.db` |
| `FLASK_ENV_NAME` | `development` / `production` / `testing` | `development` |

Contoh MySQL: `DATABASE_URL=mysql+pymysql://user:password@localhost/sectrack` (tambahkan `pip install pymysql`).

## Membuat database dan seed data

```bash
flask db upgrade      # jalankan migration (membuat 6 tabel)
flask seed            # isi data simulasi
```

Alternatif cepat tanpa migration: `flask init-db`. Untuk mengulang data dari awal: `flask seed --reset`.

Setelah seed, ada 4 user demo (password semuanya `Password123!`):

| Role | Email | X-API-Key |
|---|---|---|
| admin | admin@sectrack.local | `stk_demo_admin_key` |
| analyst | rina@sectrack.local | `stk_demo_analyst_key` |
| analyst | bima@sectrack.local | `stk_demo_analyst2_key` |
| reporter | sari@sectrack.local | `stk_demo_reporter_key` |

> API key demo ini sengaja dibuat mudah diingat untuk keperluan demo. Kalau dipakai beneran, ganti lewat `POST /api/v1/users/{id}/rotate-key`.

## Menjalankan aplikasi

```bash
flask run
```

Buka:
- http://127.0.0.1:5000/ : info API
- http://127.0.0.1:5000/docs : Swagger UI (bisa langsung mencoba endpoint)
- http://127.0.0.1:5000/api/v1/health : health check

## Menjalankan test

```bash
pytest
```

Test memakai database SQLite in-memory yang dibuat ulang dan di-seed untuk setiap test, jadi tidak mengganggu database lokal. Hasil saat ini: **43 passed**.

## Hak akses per role

| Resource | GET | POST | PUT/PATCH | DELETE |
|---|---|---|---|---|
| assets, vulnerabilities | semua role | admin, analyst | admin, analyst | admin |
| findings | semua role | admin, analyst | admin, analyst (PATCH) | admin |
| incidents | semua role | **semua role** (reporter hanya laporan baru) | admin, analyst | admin |
| users | admin (`/users/me` semua role) | admin | admin (PATCH) | admin |
| audit-logs | admin | - | - | - |
| stats/summary | semua role | - | - | - |

## Daftar endpoint

Semua endpoint (kecuali `/`, `/docs`, `/openapi.yaml`, `/api/v1/health`) wajib header `X-API-Key`.

| Method | Endpoint | Keterangan |
|---|---|---|
| GET | `/api/v1/health` | health check |
| GET | `/api/v1/users/me` | profil sesuai API key |
| GET, POST | `/api/v1/users` | list / buat user |
| GET, PATCH, DELETE | `/api/v1/users/{id}` | detail / ubah / hapus user |
| POST | `/api/v1/users/{id}/rotate-key` | ganti API key |
| GET, POST | `/api/v1/assets` | list / tambah aset |
| GET, PUT, PATCH, DELETE | `/api/v1/assets/{id}` | detail / ganti / ubah / hapus aset |
| GET, POST | `/api/v1/vulnerabilities` | list / tambah kerentanan |
| GET, PUT, PATCH, DELETE | `/api/v1/vulnerabilities/{id}` | detail / ganti / ubah / hapus |
| GET, POST | `/api/v1/findings` | list / catat temuan |
| GET, PATCH, DELETE | `/api/v1/findings/{id}` | detail / ubah status / hapus |
| GET, POST | `/api/v1/incidents` | list / lapor insiden |
| GET, PUT, PATCH, DELETE | `/api/v1/incidents/{id}` | detail / ganti / ubah / hapus |
| GET | `/api/v1/audit-logs`, `/api/v1/audit-logs/{id}` | audit log |
| GET | `/api/v1/stats/summary` | ringkasan dashboard |

### Parameter query untuk list

| Parameter | Contoh | Berlaku di |
|---|---|---|
| `q` | `?q=srv` | users, assets, vulnerabilities, incidents |
| filter enum | `?criticality=critical`, `?status=open`, `?category=phishing`, `?severity=high` | sesuai resource |
| filter id | `?asset_id=1`, `?assignee_id=2` | findings, incidents, assets (`owner_id`) |
| `min_cvss` | `?min_cvss=7` | vulnerabilities |
| `from`, `to` | `?from=2026-11-01&to=2026-11-30` | incidents (tanggal kejadian) |
| `sort` | `?sort=name` (naik), `?sort=-created_at` (turun) | semua list, field dibatasi whitelist |
| `page`, `per_page` | `?page=2&per_page=20` (maks 100) | semua list |

## Format response

Sukses:

```json
{ "success": true, "message": "opsional", "data": { }, "meta": { "page": 1, "per_page": 10, "total": 8, "total_pages": 1 } }
```

Error (selalu bentuk yang sama):

```json
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "Data yang dikirim tidak valid.", "details": { } } }
```

| Status | Code | Kapan |
|---|---|---|
| 200 | - | GET/PUT/PATCH berhasil |
| 201 | - | POST berhasil (ada header `Location`) |
| 204 | - | DELETE berhasil |
| 400 | `BAD_REQUEST` / `INVALID_QUERY_PARAM` | body bukan JSON object, parameter query salah |
| 401 | `UNAUTHORIZED` | API key kosong/salah/akun nonaktif |
| 403 | `FORBIDDEN` | role tidak punya akses |
| 404 | `NOT_FOUND` | data/endpoint tidak ada |
| 405 | `METHOD_NOT_ALLOWED` | method tidak didukung |
| 409 | `CONFLICT` | duplikat, atau data masih dipakai tabel lain |
| 413 | `PAYLOAD_TOO_LARGE` | body > 1 MB |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | Content-Type bukan JSON |
| 422 | `VALIDATION_ERROR` | isi data tidak lolos validasi |
| 500 | `INTERNAL_ERROR` | error tak terduga (detail hanya di log server) |

## Contoh request dan response

Contoh di bawah pakai `curl` (Git Bash/macOS/Linux). Di Windows lebih enak pakai Postman: import `docs/SecTrack.postman_collection.json`.

**1. List aset critical, urut nama, 2 per halaman**

```bash
curl -H "X-API-Key: stk_demo_reporter_key" "http://127.0.0.1:5000/api/v1/assets?criticality=critical&sort=name&per_page=2"
```

```json
{
  "success": true,
  "data": [
    { "id": 2, "name": "srv-db-01", "asset_type": "database", "ip_address": "10.10.1.20",
      "location": "Ruang Server Lt.2", "criticality": "critical",
      "description": "Database MySQL data mahasiswa (simulasi)",
      "owner": { "id": 1, "name": "Admin Lab", "role": "admin" }, "open_findings": 0,
      "created_at": "2026-11-24T04:14:50.799955", "updated_at": "2026-11-24T04:14:50.799956" },
    { "id": 1, "name": "srv-web-01", "...": "..." }
  ],
  "meta": { "page": 1, "per_page": 2, "total": 2, "total_pages": 1 }
}
```

**2. Tambah aset (201 Created)**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/assets \
  -H "X-API-Key: stk_demo_analyst_key" -H "Content-Type: application/json" \
  -d '{"name":"srv-backup-01","asset_type":"server","ip_address":"10.10.1.40","location":"Ruang Server Lt.2","criticality":"high"}'
```

```json
{
  "success": true,
  "message": "Aset berhasil ditambahkan.",
  "data": { "id": 9, "name": "srv-backup-01", "asset_type": "server", "ip_address": "10.10.1.40",
            "location": "Ruang Server Lt.2", "criticality": "high", "description": null,
            "owner": { "id": 2, "name": "Rina Analyst", "role": "analyst" }, "open_findings": 0,
            "created_at": "...", "updated_at": "..." }
}
```

**3. Validasi gagal (422)**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/assets \
  -H "X-API-Key: stk_demo_analyst_key" -H "Content-Type: application/json" \
  -d '{"name":"x","asset_type":"kulkas","ip_address":"999.1.1.1"}'
```

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Data yang dikirim tidak valid.",
    "details": {
      "name": ["Panjang harus 2 sampai 100 karakter."],
      "asset_type": ["Harus salah satu dari: server, workstation, network_device, iot_device, web_application, database."],
      "ip_address": ["Format IP address tidak valid (contoh: 192.168.10.5)."]
    }
  }
}
```

**4. Temuan duplikat (409)**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/findings \
  -H "X-API-Key: stk_demo_analyst_key" -H "Content-Type: application/json" \
  -d '{"asset_id":1,"vulnerability_id":4}'
```

```json
{ "success": false, "error": { "code": "CONFLICT",
  "message": "Kerentanan ini sudah tercatat di aset tersebut. Update temuan yang lama saja.",
  "details": { "existing_finding_id": 2 } } }
```

**5. Reporter melapor insiden (waktu WIB otomatis disimpan sebagai UTC)**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/incidents \
  -H "X-API-Key: stk_demo_reporter_key" -H "Content-Type: application/json" \
  -d '{"title":"Wi-Fi lab minta login aneh","description":"Muncul halaman login palsu saat konek ke Wi-Fi lab.","category":"phishing","severity":"medium","occurred_at":"2026-11-20T09:00:00+07:00"}'
```

```json
{ "success": true, "message": "Insiden dilaporkan.",
  "data": { "id": 7, "title": "Wi-Fi lab minta login aneh", "category": "phishing", "severity": "medium",
            "status": "new", "asset": null, "reporter": { "id": 4, "name": "Sari Staff", "role": "reporter" },
            "assignee": null, "occurred_at": "2026-11-20T02:00:00", "resolved_at": null, "...": "..." } }
```

**6. Tanpa API key (401) dan role tidak cukup (403)**

```json
{ "success": false, "error": { "code": "UNAUTHORIZED", "message": "Header X-API-Key wajib diisi." } }
```

```json
{ "success": false, "error": { "code": "FORBIDDEN", "message": "Role kamu tidak punya akses ke aksi ini.",
  "details": { "required_roles": ["admin", "analyst"], "your_role": "reporter" } } }
```

**7. Hapus aset yang masih punya temuan (409)**

```json
{ "success": false, "error": { "code": "CONFLICT",
  "message": "Aset masih punya temuan atau insiden, jadi tidak bisa dihapus.",
  "details": { "findings": 2, "incidents": 1 } } }
```

## Dokumentasi tambahan

- ERD: [`docs/ERD.png`](docs/ERD.png)
- OpenAPI 3: [`docs/openapi.yaml`](docs/openapi.yaml) (juga disajikan di `/openapi.yaml` dan `/docs`)
- Postman: [`docs/SecTrack.postman_collection.json`](docs/SecTrack.postman_collection.json). Variabel `baseUrl` dan API key sudah diisi. Jalankan `flask seed --reset` dulu supaya id di contoh cocok.

## Deploy demo (PythonAnywhere, gratis)

Versi yang sedang berjalan: https://nazhwa.pythonanywhere.com. Langkah yang dipakai:

1. Daftar di https://www.pythonanywhere.com, buka **Consoles → Bash**.
2. `git clone https://github.com/okeyy07-rgb/sectrack-api.git && cd sectrack-api`
3. `python3.13 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
4. Buat file `.env` berisi `FLASK_APP=wsgi.py`, `FLASK_ENV_NAME=production`, dan `SECRET_KEY` acak
   (misalnya dari `python -c "import secrets; print(secrets.token_hex(32))"`).
5. `flask db upgrade && flask seed`
6. Tab **Web → Add a new web app → Manual configuration (Python 3.13)**.
7. Isi **Virtualenv** dengan `/home/<username>/sectrack-api/venv`.
8. Edit file **WSGI configuration**, ganti isinya dengan:
   ```python
   import sys, os
   path = "/home/<username>/sectrack-api"
   if path not in sys.path:
       sys.path.insert(0, path)
   os.chdir(path)
   from dotenv import load_dotenv
   load_dotenv(os.path.join(path, ".env"))
   from wsgi import app as application
   ```
9. Klik **Reload**. API bisa diakses di `https://<username>.pythonanywhere.com/api/v1/health`.

Alternatif lain: Render/Railway dengan start command `gunicorn wsgi:app`.

## Referensi

- Dokumentasi Flask: https://flask.palletsprojects.com/
- Flask-SQLAlchemy: https://flask-sqlalchemy.readthedocs.io/
- SQLAlchemy 2.x: https://docs.sqlalchemy.org/en/20/
- Flask-Migrate / Alembic: https://flask-migrate.readthedocs.io/
- Marshmallow: https://marshmallow.readthedocs.io/
- pytest: https://docs.pytest.org/
- OpenAPI Specification 3.0.3: https://spec.openapis.org/oas/v3.0.3
- OWASP API Security Top 10 (2023): https://owasp.org/API-Security/
- Rating severity CVSS v3.x (FIRST): https://www.first.org/cvss/
- Data CVE contoh di seed: https://nvd.nist.gov/

## Penggunaan bantuan AI

Project ini dikerjakan dengan bantuan AI (Claude, Anthropic) untuk menyusun kode awal, test, dan draf dokumentasi. Seluruh hasilnya sudah dijalankan dan diuji (`pytest`), lalu dipelajari supaya bisa dijelaskan saat demo.

## Rencana pengembangan (UAS)

Lihat bagian "Rencana UAS" di lembar jawaban. Ringkasnya: login + JWT (access/refresh token), rate limiting, dashboard frontend dengan grafik, notifikasi alert untuk temuan critical, import hasil scan internal (format JSON/CSV), dan deployment dengan MySQL.
