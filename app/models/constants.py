"""Daftar nilai yang diizinkan (enum) untuk beberapa kolom.
Disimpan di satu tempat supaya model, validasi, dan dokumentasi konsisten."""

ROLES = ("admin", "analyst", "reporter")

ASSET_TYPES = ("server", "workstation", "network_device", "iot_device", "web_application", "database")
CRITICALITY_LEVELS = ("low", "medium", "high", "critical")

SEVERITY_LEVELS = ("low", "medium", "high", "critical")

FINDING_STATUSES = ("open", "in_progress", "resolved", "accepted_risk")

INCIDENT_CATEGORIES = (
    "malware",
    "phishing",
    "unauthorized_access",
    "brute_force",
    "dos",
    "data_leak",
    "misconfiguration",
    "other",
)
INCIDENT_STATUSES = ("new", "investigating", "contained", "resolved", "closed")
INCIDENT_DONE_STATUSES = ("resolved", "closed")

AUDIT_ACTIONS = ("create", "update", "delete")
