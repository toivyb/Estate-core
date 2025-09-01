# scripts/seed_user_passlib.py
from app import create_app, db
from app.models import User
from passlib.hash import pbkdf2_sha256

EMAIL = "toivybraun@gmail.com"
PASSWORD = "Unique3315!"

app = create_app()
with app.app_context():
    u = User.query.filter_by(email=EMAIL).first()
    if not u:
        u = User(email=EMAIL, role="admin")
        db.session.add(u)
    u.password_hash = pbkdf2_sha256.hash(PASSWORD)
    if hasattr(u, "is_active"):
        u.is_active = True
    db.session.commit()
    print("Seeded / updated:", EMAIL)