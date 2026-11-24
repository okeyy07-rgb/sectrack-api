"""Perintah CLI tambahan: flask init-db, flask seed, flask create-admin."""
import click

from .extensions import db


def register_cli(app):
    @app.cli.command("init-db")
    @click.option("--drop", is_flag=True, help="Hapus semua tabel dulu sebelum dibuat ulang.")
    def init_db(drop):
        """Buat tabel langsung dari model (alternatif cepat selain `flask db upgrade`)."""
        if drop:
            db.drop_all()
        db.create_all()
        click.echo("Tabel database siap.")

    @app.cli.command("seed")
    @click.option("--reset", is_flag=True, help="Kosongkan data lama dulu.")
    def seed(reset):
        """Isi database dengan data simulasi."""
        from .models import User
        from .seed import DEMO_PASSWORD, DEMO_USERS, clear_data, run_seed

        if reset:
            clear_data()
        elif db.session.scalar(db.select(db.func.count(User.id))):
            click.echo("Database sudah berisi data. Pakai `flask seed --reset` untuk mengisi ulang.")
            return

        counts = run_seed()
        click.echo(f"Seed selesai: {counts}")
        click.echo("API key demo:")
        for u in DEMO_USERS:
            click.echo(f"  {u['role']:<9} {u['email']:<24} X-API-Key: {u['api_key']}")
        click.echo(f"Password semua user demo: {DEMO_PASSWORD}")

    @app.cli.command("create-admin")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(name, email, password):
        """Buat akun admin baru dengan API key acak."""
        from .models import User
        from .utils.security import generate_api_key, hash_api_key

        raw_key = generate_api_key()
        user = User(name=name, email=email.lower(), role="admin", api_key_hash=hash_api_key(raw_key))
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin dibuat. API key (simpan baik-baik): {raw_key}")
