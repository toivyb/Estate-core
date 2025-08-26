from app import create_app, db
from app.models import User
from passlib.hash import pbkdf2_sha256

EMAIL = "toivybraun@gmail.com"
PASSWORD = "Unique3315!"

app = create_app()
with app.app_context():
    u = User.query.filter_by(email=EMAIL).first()
    if not u:
        raise SystemExit("User not found")
    print("Before:", (u.password_hash or "")[:30])
    u.password_hash = pbkdf2_sha256.hash(PASSWORD)
    # make sure login checks won't block you
    if hasattr(u, "is_active"):
        u.is_active = True
    db.session.commit()
    print("After:", u.password_hash[:30])
    # sanity: verify now
    print("Verify:", pbkdf2_sha256.verify(PASSWORD, u.password_hash))
