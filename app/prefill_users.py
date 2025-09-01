from estatecore_backend import create_app
from estatecore_backend.models import db, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    demo_users = [
        {"name": "Admin User", "email": "admin@demo.com", "password": "admin123", "role": "super_admin"},
        {"name": "Manager User", "email": "manager@demo.com", "password": "manager123", "role": "property_manager"},
        {"name": "Tenant User", "email": "tenant@demo.com", "password": "tenant123", "role": "tenant"},
    ]

    for user_data in demo_users:
        existing = User.query.filter_by(email=user_data["email"]).first()
        if not existing:
            user = User(
                name=user_data["name"],
                email=user_data["email"],
                password=generate_password_hash(user_data["password"]),
                role=user_data["role"]
            )
            db.session.add(user)

    db.session.commit()
    print("Users prefilled successfully.")
