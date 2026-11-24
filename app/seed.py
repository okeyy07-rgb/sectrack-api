"""Seed data simulasi untuk pengembangan dan demo.

Semua data di sini FIKTIF: aset, IP (blok privat), dan insiden hanya simulasi
lab kampus. CVE yang dipakai adalah CVE publik yang terkenal, hanya sebagai contoh katalog.
"""
from datetime import timedelta

from .extensions import db
from .models import Asset, AuditLog, Finding, Incident, User, Vulnerability
from .models.base import utcnow
from .utils.security import hash_api_key

# API key demo. HANYA untuk lokal/demo. Ganti (rotate-key) kalau dipakai beneran.
DEMO_USERS = [
    {"name": "Admin Lab", "email": "admin@sectrack.local", "role": "admin", "api_key": "stk_demo_admin_key"},
    {"name": "Rina Analyst", "email": "rina@sectrack.local", "role": "analyst", "api_key": "stk_demo_analyst_key"},
    {"name": "Bima Analyst", "email": "bima@sectrack.local", "role": "analyst", "api_key": "stk_demo_analyst2_key"},
    {"name": "Sari Staff", "email": "sari@sectrack.local", "role": "reporter", "api_key": "stk_demo_reporter_key"},
]
DEMO_PASSWORD = "Password123!"


def clear_data():
    for model in (AuditLog, Finding, Incident, Asset, Vulnerability, User):
        db.session.execute(db.delete(model))
    db.session.commit()


def run_seed():
    now = utcnow()
    users = []
    for u in DEMO_USERS:
        user = User(name=u["name"], email=u["email"], role=u["role"], api_key_hash=hash_api_key(u["api_key"]))
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        users.append(user)
    db.session.flush()

    admin, rina, bima, sari = users  # urutan sama dengan DEMO_USERS

    asset_rows = [
        ("srv-web-01", "server", "10.10.1.10", "Ruang Server Lt.2", "critical", "Web server portal akademik (simulasi)", admin),
        ("srv-db-01", "database", "10.10.1.20", "Ruang Server Lt.2", "critical", "Database MySQL data mahasiswa (simulasi)", admin),
        ("app-siakad-sim", "web_application", "10.10.1.10", "Ruang Server Lt.2", "high", "Aplikasi SIAKAD versi simulasi untuk praktikum", rina),
        ("rtr-core-01", "network_device", "10.10.0.1", "Ruang Server Lt.2", "high", "Router inti jaringan lab", bima),
        ("cam-lab-03", "iot_device", "10.10.5.33", "Lab Jaringan 3", "medium", "Kamera IP pengawas lab", bima),
        ("ws-lab-a12", "workstation", "10.10.2.112", "Lab Komputer A", "low", "PC praktikum mahasiswa", rina),
        ("ws-dosen-07", "workstation", "10.10.3.7", "Ruang Dosen", "medium", "Laptop dosen yang terdaftar di jaringan", rina),
        ("srv-file-01", "server", "10.10.1.30", "Ruang Server Lt.2", "high", "File server dokumen internal", admin),
    ]
    assets = {}
    for name, a_type, ip, loc, crit, desc, owner in asset_rows:
        asset = Asset(name=name, asset_type=a_type, ip_address=ip, location=loc, criticality=crit, description=desc, owner=owner)
        db.session.add(asset)
        assets[name] = asset

    vuln_rows = [
        ("CVE-2021-44228", "Log4Shell - RCE pada Apache Log4j 2", "critical", 10.0,
         "Remote code execution lewat lookup JNDI pada pesan log.", "Upgrade Log4j ke 2.17.1 atau lebih baru."),
        ("CVE-2019-0708", "BlueKeep - RCE pada Remote Desktop Services", "critical", 9.8,
         "RCE tanpa autentikasi pada RDP Windows versi lama.", "Pasang patch Microsoft, matikan RDP kalau tidak dipakai, aktifkan NLA."),
        ("CVE-2014-0160", "Heartbleed - kebocoran memori OpenSSL", "high", 7.5,
         "Ekstensi heartbeat TLS bisa membocorkan isi memori server.", "Upgrade OpenSSL lalu ganti sertifikat dan private key."),
        ("CVE-2021-41773", "Path traversal pada Apache HTTP Server 2.4.49", "high", 7.5,
         "Penyerang bisa membaca file di luar document root.", "Upgrade Apache ke 2.4.51 atau lebih baru."),
        ("CVE-2023-44487", "HTTP/2 Rapid Reset DoS", "high", 7.5,
         "Serangan DoS dengan membuka dan membatalkan stream HTTP/2 secara cepat.", "Update web server/reverse proxy ke versi yang sudah di-patch."),
        (None, "Kredensial default pada kamera IP", "high", None,
         "Perangkat masih memakai username/password bawaan pabrik.", "Ganti password, nonaktifkan akun default, pisahkan VLAN IoT."),
        (None, "SSH mengizinkan login root dengan password", "medium", None,
         "PermitRootLogin yes dan PasswordAuthentication yes di sshd_config.", "Pakai key-based auth dan set PermitRootLogin no."),
        (None, "Sertifikat TLS kedaluwarsa", "low", None,
         "Sertifikat HTTPS sudah lewat masa berlaku sehingga browser menampilkan peringatan.", "Perpanjang sertifikat dan pasang auto-renew."),
    ]
    vulns = {}
    for cve, title, sev, cvss, desc, fix in vuln_rows:
        vuln = Vulnerability(cve_id=cve, title=title, severity=sev, cvss_score=cvss, description=desc, remediation=fix)
        db.session.add(vuln)
        vulns[cve or title] = vuln
    db.session.flush()

    finding_rows = [
        ("app-siakad-sim", "CVE-2021-44228", "in_progress", 12, "Library log4j 2.14 ditemukan di folder lib aplikasi.", rina),
        ("srv-web-01", "CVE-2021-41773", "open", 5, "Versi Apache terdeteksi 2.4.49 saat scan internal.", rina),
        ("srv-web-01", "Sertifikat TLS kedaluwarsa", "resolved", 30, "Sudah diperpanjang via certbot.", bima),
        ("ws-dosen-07", "CVE-2019-0708", "open", 3, "RDP terbuka di jaringan internal.", bima),
        ("cam-lab-03", "Kredensial default pada kamera IP", "open", 2, "Login admin/admin masih bisa dipakai.", bima),
        ("srv-file-01", "SSH mengizinkan login root dengan password", "in_progress", 8, None, rina),
        ("srv-db-01", "SSH mengizinkan login root dengan password", "accepted_risk", 20, "Hanya bisa diakses dari jaringan manajemen.", admin),
        ("rtr-core-01", "CVE-2023-44487", "open", 1, "Panel admin router memakai HTTP/2.", bima),
        ("srv-file-01", "CVE-2014-0160", "resolved", 45, "OpenSSL sudah di-upgrade, sertifikat sudah diganti.", rina),
    ]
    for asset_name, vuln_key, status, days_ago, notes, reporter in finding_rows:
        finding = Finding(
            asset=assets[asset_name],
            vulnerability=vulns[vuln_key],
            reported_by=reporter,
            notes=notes,
            found_at=now - timedelta(days=days_ago),
        )
        finding.apply_status(status)
        db.session.add(finding)

    incident_rows = [
        ("Email phishing mengatasnamakan BAAK", "Beberapa mahasiswa menerima email minta login ulang ke link palsu.",
         "phishing", "medium", "investigating", None, sari, rina, 2),
        ("Percobaan brute force SSH ke file server", "Log auth mencatat ribuan percobaan login gagal dari satu IP internal.",
         "brute_force", "high", "contained", "srv-file-01", rina, rina, 6),
        ("Kamera lab bisa diakses tanpa izin", "Tampilan kamera lab 3 bisa dibuka dari jaringan Wi-Fi tamu.",
         "unauthorized_access", "high", "new", "cam-lab-03", sari, None, 1),
        ("Malware di PC praktikum", "Antivirus mendeteksi trojan dari flashdisk mahasiswa.",
         "malware", "medium", "resolved", "ws-lab-a12", sari, bima, 14),
        ("Halaman portal akademik lambat dan sering timeout", "Diduga ada lonjakan request HTTP/2 tidak wajar.",
         "dos", "high", "investigating", "srv-web-01", rina, bima, 3),
        ("File konfigurasi database ter-upload ke repo publik", "File .env berisi kredensial DB simulasi ditemukan di repo praktikum.",
         "data_leak", "critical", "closed", "srv-db-01", admin, rina, 21),
    ]
    for title, desc, cat, sev, status, asset_name, reporter, assignee, days_ago in incident_rows:
        incident = Incident(
            title=title,
            description=desc,
            category=cat,
            severity=sev,
            asset=assets.get(asset_name) if asset_name else None,
            reporter=reporter,
            assignee=assignee,
            occurred_at=now - timedelta(days=days_ago),
        )
        incident.apply_status(status)
        db.session.add(incident)

    db.session.commit()
    return {
        "users": len(DEMO_USERS),
        "assets": len(asset_rows),
        "vulnerabilities": len(vuln_rows),
        "findings": len(finding_rows),
        "incidents": len(incident_rows),
    }
