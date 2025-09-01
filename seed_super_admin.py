from estatecore_backend import create_app, db
from estatecore_backend.models import User

try:
    from werkzeug.security import generate_password_hash
    hasher = lambda p: generate_password_hash(p)
except Exception:
    import bcrypt
    hasher = lambda p: bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()

EMAIL = "toivybraun@gmail.com"
PASSWORD = "Unique3315!"

app = create_app()
with app.app_context():
    u = User.query.filter_by(email=EMAIL).first()
    if not u:
        u = User(email=EMAIL, role="super_admin", is_active=True)
        db.session.add(u)
    if hasattr(u, "set_password"):
        u.set_password(PASSWORD)
    elif hasattr(u, "password_hash"):
        u.password_hash = hasher(PASSWORD)
    elif hasattr(u, "password"):
        u.password = hasher(PASSWORD)
    else:
        raise RuntimeError("User model has no password field/method I recognize.")
    db.session.commit()
    print("Superadmin upserted:", u.id, u.email)
