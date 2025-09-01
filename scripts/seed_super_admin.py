# scripts/seed_super_admin.py
# Seed a super admin by using the model already registered on the app's metadata.
from estatecore_backend import app, db

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin123!"  # change after first login

def _get_user_class():
    """
    Find the User ORM class already registered with SQLAlchemy, avoiding imports
    that could re-declare the table.
    Works with Flask-SQLAlchemy 2.x (_decl_class_registry) and 3.x (registry._class_registry).
    """
    # Flask-SQLAlchemy 3.x path
    reg = getattr(db.Model, "registry", None)
    if reg is not None:
        regmap = getattr(reg, "_class_registry", None)
        if regmap and "User" in regmap:
            cls = regmap["User"]
            # In some versions entries can be weakrefs
            try:
                from weakref import ReferenceType
                if isinstance(cls, ReferenceType):
                    cls = cls()
            except Exception:
                pass
            return cls

    # Flask-SQLAlchemy 2.x path
    decl = getattr(db.Model, "_decl_class_registry", None)
    if decl and "User" in decl:
        cls = decl["User"]
        try:
            from weakref import ReferenceType
            if isinstance(cls, ReferenceType):
                cls = cls()
        except Exception:
            pass
        return cls

    return None

with app.app_context():
    User = _get_user_class()
    if User is None:
        raise RuntimeError(
            "Could not locate the already-registered User model. "
            "Avoid importing models directly to prevent duplicate table definitions."
        )

    # Lookup by email
    existing = db.session.query(User).filter_by(email=ADMIN_EMAIL).first()
    if existing:
        print(f"Super admin already exists: {ADMIN_EMAIL}")
    else:
        u = User(email=ADMIN_EMAIL, role="super_admin")
        # Prefer model's password helper if present
        if hasattr(u, "set_password"):
            u.set_password(ADMIN_PASSWORD)
        elif hasattr(User, "password_hash"):
            # Fallback: store plain (not recommended) if your model hashes on setter only.
            # Replace this with your project's hashing util if needed.
            setattr(u, "password_hash", ADMIN_PASSWORD)
        else:
            raise RuntimeError(
                "No set_password() or password_hash field on User; "
                "update seed script to use your project's password utility."
            )

        db.session.add(u)
        db.session.commit()
        print(f"Super admin created: {ADMIN_EMAIL}")
