
import argparse
from estatecore_backend import create_app, db
from estatecore_backend.models.user import User, Role

app = create_app()

def seed_admin():
    with app.app_context():
        email = "admin@example.com"
        password = "admin123"
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, full_name="Super Admin")
            user.set_password(password)
            db.session.add(user)
        role = Role.query.filter_by(name='super_admin').first()
        if not role:
            role = Role(name='super_admin')
            db.session.add(role)
            db.session.flush()
        if role not in user.roles:
            user.roles.append(role)
        db.session.commit()
        print(f"Seeded super admin: {email} / {password}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-admin", action="store_true")
    args = parser.parse_args()
    if args.seed_admin:
        seed_admin()
    else:
        app.run(host="0.0.0.0", port=5000, debug=True)
