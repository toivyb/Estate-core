import click
from flask.cli import with_appcontext
from . import db
from .models.user import User, UserRole  # fixed import

@click.command("create-superadmin")
@click.argument("email")
@click.argument("password")
@with_appcontext
def create_superadmin(email, password):
    email = email.strip().lower()
    u = User.query.filter_by(email=email).first()
    if u:
        click.echo(f"User already exists: {email}")
        return
    u = User(email=email, role=UserRole.super_admin)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    click.echo(f"Created super admin: {email} (id={u.id})")

def register_commands(app):
    app.cli.add_command(create_superadmin)
