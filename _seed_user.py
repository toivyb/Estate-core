from app import create_app, db
from sqlalchemy import select
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # import your User model (adjust if path differs)
    try:
        from app.models import User
    except Exception:
        from models import User  # fallback

    email = "toivybraun@gmail.com"
    password = "Unique3315!"

    u = db.session.execute(select(User).where(User.email==email)).scalar_one_or_none()
    if not u:
        if hasattr(User, "password_hash"):
            u = User(email=email, role="admin", password_hash=generate_password_hash(password))
        elif hasattr(User, "password"):
            u = User(email=email, role="admin", password=password)
        else:
            raise SystemExit("User model missing password[_hash] field")
        db.session.add(u)
        db.session.commit()
        print("seeded user:", email)
    else:
        print("user exists:", email)
