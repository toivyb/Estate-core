from app import create_app, db
from sqlalchemy import select
EMAIL="toivybraun@gmail.com"
PASS ="Unique3315!"

app = create_app()
print("SECRET_KEY set?:", bool(app.config.get("SECRET_KEY")))
print("JWT_SECRET_KEY set?:", bool(app.config.get("JWT_SECRET_KEY")))
try:
    import flask_jwt_extended as fjwt
    print("flask_jwt_extended present?:", True)
except Exception as e:
    print("flask_jwt_extended present?:", False, repr(e))

with app.app_context():
    # User row + password check
    from app.models import User
    from passlib.hash import pbkdf2_sha256
    u = db.session.execute(select(User).where(User.email==EMAIL)).scalar_one_or_none()
    print("user exists?:", bool(u))
    if u:
        print("is_active?:", getattr(u, "is_active", True))
        try:
            ok = pbkdf2_sha256.verify(PASS, u.password_hash)
            print("password_ok?:", ok)
        except Exception as e:
            print("password_ok?: ERROR", repr(e))

        # Try creating a JWT the way Flask-JWT-Extended expects
        try:
            from flask_jwt_extended import create_access_token
            tok = create_access_token(identity=str(u.id))
            print("jwt_ok?:", True, "sample:", tok[:32], "...")
        except Exception as e:
            print("jwt_ok?:", False, repr(e))
