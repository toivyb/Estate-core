# scripts/make_admin.py
from app import create_app, db
from app.models import User
from passlib.hash import pbkdf2_sha256

EMAIL = "toivybraun@gmail.com"
PASSWORD = "ChangeMeStrong!"

app = create_app()
with app.app_context():
    u = User.query.filter_by(email=EMAIL).first()
    if not u:
        u = User(email=EMAIL, role="admin")
        db.session.add(u)
    u.role = "admin"
    u.password_hash = pbkdf2_sha256.hash(PASSWORD)
    if hasattr(u, "is_active"):
        u.is_active = True
    db.session.commit()
    print("Admin ensured:", EMAIL)
