"""VIEW (V pada MVC) untuk REST API.

Di API tidak ada HTML; "tampilan"-nya adalah representasi JSON.
Schema Marshmallow di sini punya dua tugas:
  1. load()  -> memvalidasi input JSON dari client
  2. dump()  -> mengubah objek model menjadi JSON response (field sensitif tidak ikut)
"""
import ipaddress
from datetime import timedelta, timezone

from . import messages  # noqa: F401  (harus paling awal)
from marshmallow import Schema, ValidationError, fields, post_load, pre_load, validate, validates

from ..models.base import utcnow
from ..models.constants import (
    ASSET_TYPES,
    CRITICALITY_LEVELS,
    FINDING_STATUSES,
    INCIDENT_CATEGORIES,
    INCIDENT_STATUSES,
    ROLES,
    SEVERITY_LEVELS,
)


# ---------------------------------------------------------------- helpers
class StrippedSchema(Schema):
    """Semua string di-trim dulu sebelum divalidasi."""

    @pre_load
    def strip_strings(self, data, **kwargs):
        if isinstance(data, dict):
            return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}
        return data


def validate_ip(value):
    if value is None:
        return
    try:
        ipaddress.ip_address(value)
    except ValueError:
        raise ValidationError("Format IP address tidak valid (contoh: 192.168.10.5).")


def to_naive_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def not_in_future(dt):
    # toleransi 5 menit untuk perbedaan jam client-server
    if dt is not None and to_naive_utc(dt) > utcnow() + timedelta(minutes=5):
        raise ValidationError("Waktu tidak boleh di masa depan.")


# ---------------------------------------------------------------- input schemas
class UserCreateSchema(StrippedSchema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=128))
    role = fields.String(load_default="reporter", validate=validate.OneOf(ROLES))

    @post_load
    def normalize(self, data, **kwargs):
        if "email" in data:
            data["email"] = data["email"].lower()
        return data


class UserUpdateSchema(StrippedSchema):
    name = fields.String(validate=validate.Length(min=2, max=100))
    password = fields.String(load_only=True, validate=validate.Length(min=8, max=128))
    role = fields.String(validate=validate.OneOf(ROLES))
    is_active = fields.Boolean()


class AssetInputSchema(StrippedSchema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    asset_type = fields.String(required=True, validate=validate.OneOf(ASSET_TYPES))
    ip_address = fields.String(allow_none=True, validate=validate_ip)
    location = fields.String(allow_none=True, validate=validate.Length(max=100))
    criticality = fields.String(load_default="medium", validate=validate.OneOf(CRITICALITY_LEVELS))
    description = fields.String(allow_none=True, validate=validate.Length(max=2000))
    owner_id = fields.Integer(strict=True, validate=validate.Range(min=1))


class VulnerabilityInputSchema(StrippedSchema):
    cve_id = fields.String(
        allow_none=True,
        validate=validate.Regexp(
            r"^CVE-\d{4}-\d{4,7}$", error="Format CVE ID harus seperti CVE-2024-12345."
        ),
    )
    title = fields.String(required=True, validate=validate.Length(min=3, max=200))
    description = fields.String(allow_none=True, validate=validate.Length(max=5000))
    severity = fields.String(required=True, validate=validate.OneOf(SEVERITY_LEVELS))
    cvss_score = fields.Float(allow_none=True, validate=validate.Range(min=0, max=10))
    remediation = fields.String(allow_none=True, validate=validate.Length(max=5000))

    @pre_load
    def upper_cve(self, data, **kwargs):
        if isinstance(data, dict) and isinstance(data.get("cve_id"), str):
            data["cve_id"] = data["cve_id"].strip().upper() or None
        return data


class FindingCreateSchema(StrippedSchema):
    asset_id = fields.Integer(required=True, strict=True, validate=validate.Range(min=1))
    vulnerability_id = fields.Integer(required=True, strict=True, validate=validate.Range(min=1))
    status = fields.String(load_default="open", validate=validate.OneOf(FINDING_STATUSES))
    notes = fields.String(allow_none=True, validate=validate.Length(max=2000))
    found_at = fields.DateTime(validate=not_in_future)

    @post_load
    def normalize(self, data, **kwargs):
        if "found_at" in data:
            data["found_at"] = to_naive_utc(data["found_at"])
        return data


class FindingUpdateSchema(StrippedSchema):
    status = fields.String(validate=validate.OneOf(FINDING_STATUSES))
    notes = fields.String(allow_none=True, validate=validate.Length(max=2000))


class IncidentInputSchema(StrippedSchema):
    title = fields.String(required=True, validate=validate.Length(min=5, max=200))
    description = fields.String(required=True, validate=validate.Length(min=10, max=5000))
    category = fields.String(required=True, validate=validate.OneOf(INCIDENT_CATEGORIES))
    severity = fields.String(required=True, validate=validate.OneOf(SEVERITY_LEVELS))
    status = fields.String(load_default="new", validate=validate.OneOf(INCIDENT_STATUSES))
    asset_id = fields.Integer(allow_none=True, strict=True, validate=validate.Range(min=1))
    assignee_id = fields.Integer(allow_none=True, strict=True, validate=validate.Range(min=1))
    occurred_at = fields.DateTime(required=True)

    @validates("occurred_at")
    def check_occurred_at(self, value, **kwargs):
        not_in_future(value)

    @post_load
    def normalize(self, data, **kwargs):
        if "occurred_at" in data:
            data["occurred_at"] = to_naive_utc(data["occurred_at"])
        return data


# ---------------------------------------------------------------- output schemas
class UserBriefSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    role = fields.String()


class UserOutputSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    email = fields.String()
    role = fields.String()
    is_active = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class AssetBriefSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    ip_address = fields.String()
    criticality = fields.String()


class VulnerabilityBriefSchema(Schema):
    id = fields.Integer()
    cve_id = fields.String()
    title = fields.String()
    severity = fields.String()
    cvss_score = fields.Float()


class AssetOutputSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    asset_type = fields.String()
    ip_address = fields.String()
    location = fields.String()
    criticality = fields.String()
    description = fields.String()
    owner = fields.Nested(UserBriefSchema)
    open_findings = fields.Method("count_open_findings")
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    def count_open_findings(self, asset):
        return sum(1 for f in asset.findings if f.status in ("open", "in_progress"))


class VulnerabilityOutputSchema(Schema):
    id = fields.Integer()
    cve_id = fields.String()
    title = fields.String()
    description = fields.String()
    severity = fields.String()
    cvss_score = fields.Float()
    remediation = fields.String()
    affected_assets = fields.Method("count_affected")
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    def count_affected(self, vuln):
        return sum(1 for f in vuln.findings if f.status in ("open", "in_progress"))


class FindingOutputSchema(Schema):
    id = fields.Integer()
    status = fields.String()
    notes = fields.String()
    asset = fields.Nested(AssetBriefSchema)
    vulnerability = fields.Nested(VulnerabilityBriefSchema)
    reported_by = fields.Nested(UserBriefSchema)
    found_at = fields.DateTime()
    resolved_at = fields.DateTime()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class IncidentOutputSchema(Schema):
    id = fields.Integer()
    title = fields.String()
    description = fields.String()
    category = fields.String()
    severity = fields.String()
    status = fields.String()
    asset = fields.Nested(AssetBriefSchema, allow_none=True)
    reporter = fields.Nested(UserBriefSchema)
    assignee = fields.Nested(UserBriefSchema, allow_none=True)
    occurred_at = fields.DateTime()
    resolved_at = fields.DateTime()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class AuditLogOutputSchema(Schema):
    id = fields.Integer()
    action = fields.String()
    entity = fields.String()
    entity_id = fields.Integer()
    detail = fields.Raw()
    ip_address = fields.String()
    user = fields.Nested(UserBriefSchema, allow_none=True)
    created_at = fields.DateTime()
