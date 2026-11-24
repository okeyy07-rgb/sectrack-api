"""MODEL (M pada MVC): representasi tabel database lewat ORM SQLAlchemy."""
from .asset import Asset
from .audit_log import AuditLog
from .finding import Finding
from .incident import Incident
from .user import User
from .vulnerability import Vulnerability

__all__ = ["User", "Asset", "Vulnerability", "Finding", "Incident", "AuditLog"]
