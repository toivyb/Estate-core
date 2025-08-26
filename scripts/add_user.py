# scripts/add_user.py
from app import create_app, db
from app.models import User  # assumes User exported in app.models
from passlib.hash import pbkdf2_sha256

EMAIL = "staff@example.com"
PASSWORD = "Test123!"
ROLE = "user"  # or "admin"

app = create_app()
with app.app_context():
    u = User.query.filter_by(email=EMAIL).first()
    if not u:
        u = User(email=EMAIL, role=ROLE)
        db.session.add(u)
    u.password_hash = pbkdf2_sha256.hash(PASSWORD)
    if hasattr(u, "is_active"):
        u.is_active = True
    db.session.commit()
    print("Upserted:", EMAIL, ROLE)
