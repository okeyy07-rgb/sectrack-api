"""Ringkasan kondisi keamanan untuk dashboard (dipakai juga sebagai bahan rencana UAS)."""
from flask import Blueprint

from ..extensions import db
from ..models import Asset, Finding, Incident, Vulnerability
from ..utils.security import require_auth
from ..views import success

bp = Blueprint("stats", __name__, url_prefix="/api/v1/stats")

ACTIVE_FINDING = ("open", "in_progress")
SEVERITY_WEIGHT = {"critical": 10, "high": 6, "medium": 3, "low": 1}


@bp.get("/summary")
@require_auth()
def summary():
    open_by_severity = dict(
        db.session.execute(
            db.select(Vulnerability.severity, db.func.count(Finding.id))
            .join(Finding.vulnerability)
            .where(Finding.status.in_(ACTIVE_FINDING))
            .group_by(Vulnerability.severity)
        ).all()
    )
    incidents_by_status = dict(
        db.session.execute(
            db.select(Incident.status, db.func.count(Incident.id)).group_by(Incident.status)
        ).all()
    )

    # skor risiko sederhana per aset = jumlah bobot severity temuan yang masih aktif
    rows = db.session.execute(
        db.select(Asset.id, Asset.name, Asset.criticality, Vulnerability.severity)
        .join(Finding, Finding.asset_id == Asset.id)
        .join(Vulnerability, Vulnerability.id == Finding.vulnerability_id)
        .where(Finding.status.in_(ACTIVE_FINDING))
    ).all()
    scores = {}
    for asset_id, name, criticality, severity in rows:
        entry = scores.setdefault(
            asset_id, {"id": asset_id, "name": name, "criticality": criticality, "risk_score": 0, "active_findings": 0}
        )
        entry["risk_score"] += SEVERITY_WEIGHT[severity]
        entry["active_findings"] += 1
    top_risky = sorted(scores.values(), key=lambda e: e["risk_score"], reverse=True)[:5]

    return success(
        {
            "total_assets": db.session.scalar(db.select(db.func.count(Asset.id))),
            "total_vulnerabilities": db.session.scalar(db.select(db.func.count(Vulnerability.id))),
            "active_findings_by_severity": {s: open_by_severity.get(s, 0) for s in SEVERITY_WEIGHT},
            "incidents_by_status": incidents_by_status,
            "top_risky_assets": top_risky,
        }
    )
