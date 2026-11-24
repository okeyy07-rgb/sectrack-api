from ..extensions import db
from .base import TimestampMixin, utcnow


class Finding(TimestampMixin, db.Model):
    """Temuan: kerentanan X ditemukan di aset Y.

    Ini tabel penghubung many-to-many antara assets dan vulnerabilities,
    tapi punya data sendiri (status perbaikan, catatan, siapa yang melaporkan),
    jadi bukan tabel tempelan."""

    __tablename__ = "findings"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    vulnerability_id = db.Column(
        db.Integer,
        db.ForeignKey("vulnerabilities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reported_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    notes = db.Column(db.Text, nullable=True)
    found_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        # aset yang sama tidak boleh punya temuan ganda untuk kerentanan yang sama
        db.UniqueConstraint("asset_id", "vulnerability_id", name="uq_findings_asset_vulnerability"),
        db.CheckConstraint(
            "status IN ('open', 'in_progress', 'resolved', 'accepted_risk')",
            name="ck_findings_status",
        ),
    )

    asset = db.relationship("Asset", back_populates="findings")
    vulnerability = db.relationship("Vulnerability", back_populates="findings")
    reported_by = db.relationship("User")

    def apply_status(self, new_status):
        """Atur resolved_at otomatis sesuai status."""
        self.status = new_status
        if new_status == "resolved":
            self.resolved_at = self.resolved_at or utcnow()
        else:
            self.resolved_at = None
