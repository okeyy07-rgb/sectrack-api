"""CONTROLLER (C pada MVC): menerima request, memanggil validasi (view/schema),
menjalankan logika bisnis, berinteraksi dengan model, lalu mengembalikan response."""


def register_blueprints(app):
    from .asset_controller import bp as assets_bp
    from .audit_controller import bp as audit_bp
    from .finding_controller import bp as findings_bp
    from .incident_controller import bp as incidents_bp
    from .main_controller import bp as main_bp
    from .stats_controller import bp as stats_bp
    from .user_controller import bp as users_bp
    from .vulnerability_controller import bp as vulnerabilities_bp

    for blueprint in (
        main_bp,
        users_bp,
        assets_bp,
        vulnerabilities_bp,
        findings_bp,
        incidents_bp,
        audit_bp,
        stats_bp,
    ):
        app.register_blueprint(blueprint)
