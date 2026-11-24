from ..extensions import db
from .base import TimestampMixin, utcnow
from .constants import INCIDENT_DONE_STATUSES


class Incident(TimestampMixin, db.Model):
    """Laporan insiden keamanan (phishing, malware, akses ilegal, dll)."""

    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), nullable=False, index=True)
    severity = db.Column(db.String(10), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="new", index=True)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    reporter_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    assignee_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    occurred_at = db.Column(db.DateTime, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('new', 'investigating', 'contained', 'resolved', 'closed')",
            name="ck_incidents_status",
        ),
        db.CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')", name="ck_incidents_severity"
        ),
    )

    asset = db.relationship("Asset", back_populates="incidents")
    reporter = db.relationship("User", foreign_keys=[reporter_id])
    assignee = db.relationship("User", foreign_keys=[assignee_id])

    def apply_status(self, new_status):
        self.status = new_status
        if new_status in INCIDENT_DONE_STATUSES:
            self.resolved_at = self.resolved_at or utcnow()
        else:
            self.resolved_at = None
