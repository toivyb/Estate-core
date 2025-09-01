import os
from getpass import getpass

def run(seed_email, seed_password, role):
    from estatecore_backend import create_app, db
    from estatecore_backend.models import User
    app = create_app()
    with app.app_context():
        u = User.query.filter_by(email=seed_email).first()
        if u:
            u.set_password(seed_password)
            u.role = role
            u.is_active = True
        else:
            u = User(email=seed_email, role=role, is_active=True)
            u.set_password(seed_password)
            db.session.add(u)
        db.session.commit()
        print(f"Seeded/updated: {seed_email} ({role})")

if __name__ == "__main__":
    email = os.environ.get("SEED_ADMIN_EMAIL","admin@example.com")
    pw = os.environ.get("SEED_ADMIN_PASSWORD") or getpass("Password for super admin: ")
    role = os.environ.get("SEED_ADMIN_ROLE","super_admin")
    run(email, pw, role)
