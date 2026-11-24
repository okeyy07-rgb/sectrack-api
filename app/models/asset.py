from ..extensions import db
from .base import TimestampMixin


class Asset(TimestampMixin, db.Model):
    """Aset TI milik organisasi yang perlu dijaga: server, perangkat jaringan, IoT, dll."""

    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    asset_type = db.Column(db.String(30), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True, index=True)
    location = db.Column(db.String(100), nullable=True)
    criticality = db.Column(db.String(10), nullable=False, default="medium")
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    __table_args__ = (
        db.CheckConstraint(
            "criticality IN ('low', 'medium', 'high', 'critical')", name="ck_assets_criticality"
        ),
    )

    owner = db.relationship("User", back_populates="owned_assets")
    findings = db.relationship("Finding", back_populates="asset", lazy="select")
    incidents = db.relationship("Incident", back_populates="asset", lazy="select")

    def __repr__(self):
        return f"<Asset {self.name}>"
