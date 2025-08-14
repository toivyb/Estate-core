import os
from datetime import date, timedelta
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from flask import Flask

# Your app + db
from estatecore_backend import create_app
from estatecore_backend.models import db

app: Flask = create_app()

def is_postgres():
    url = os.getenv("DATABASE_URL", "")
    return url.startswith("postgres")

def exec_sql(sql, **params):
    with app.app_context():
        db.session.execute(text(sql), params)
        db.session.commit()

def get_scalar(sql, **params):
    with app.app_context():
        res = db.session.execute(text(sql), params).scalar()
        return res

def ensure_admin():
    # Tries ORM first; falls back to SQL if no model/metadata available
    try:
        from estatecore_backend.models import User, Role  # adjust if your names differ
        with app.app_context():
            role = Role.query.filter_by(name="admin").first()
            if not role:
                role = Role(name="admin")
                db.session.add(role)
                db.session.commit()
            user = User.query.filter_by(email="admin@example.com").first()
            if not user:
                user = User(email="admin@example.com", full_name="System Admin")
                # If you use werkzeug security:
                if hasattr(user, "set_password"):
                    user.set_password("admin123")
                elif hasattr(user, "password"):
                    user.password = "admin123"
                if hasattr(user, "roles"):
                    user.roles.append(role)
                db.session.add(user)
                db.session.commit()
            print("✔ admin@example.com / admin123")
    except Exception as e:
        # Raw SQL fallback (Postgres upsert)
        if is_postgres():
            exec_sql("""
                INSERT INTO roles (name) VALUES ('admin')
                ON CONFLICT (name) DO NOTHING;
            """)
            exec_sql("""
                INSERT INTO users (email, full_name, password)
                VALUES (:email, :name, :pwd)
                ON CONFLICT (email) DO NOTHING;
            """, email="admin@example.com", name="System Admin", pwd="admin123")
            print("✔ admin (raw SQL fallback). Note: password is plaintext unless your app hashes on save.")
        else:
            print(f"⚠ Skipped admin seed (no ORM and not Postgres): {e}")

def seed_core():
    """
    Seeds a minimal set:
    - Property -> Unit -> Tenant -> Lease -> Payment
    - Maintenance ticket
    Works with ORM if your models exist; else tries raw SQL table names commonly used.
    """
    try:
        from estatecore_backend.models import Property, Unit, Tenant, Lease, Payment, MaintenanceRequest
        with app.app_context():
            prop = Property.query.filter_by(name="Sunset Villas").first() or Property(
                name="Sunset Villas", address="123 Palm Ave"
            )
            db.session.add(prop); db.session.flush()

            unit = Unit.query.filter_by(code="A-101").first() or Unit(
                code="A-101", bedrooms=2, bathrooms=1, property_id=prop.id
            )
            db.session.add(unit); db.session.flush()

            tenant = Tenant.query.filter_by(email="tenant1@example.com").first() or Tenant(
                first_name="Taylor", last_name="Jones", email="tenant1@example.com", phone="555-0101"
            )
            db.session.add(tenant); db.session.flush()

            start = date.today().replace(day=1)
            lease = Lease.query.filter_by(unit_id=unit.id, tenant_id=tenant.id).first() or Lease(
                unit_id=unit.id, tenant_id=tenant.id,
                start_date=start, end_date=start + timedelta(days=365),
                rent_amount=1500
            )
            db.session.add(lease); db.session.flush()

            payment = Payment.query.filter_by(lease_id=lease.id).first() or Payment(
                lease_id=lease.id, amount=1500, method="card", status="paid", paid_on=start + timedelta(days=5)
            )
            db.session.add(payment)

            mr = MaintenanceRequest.query.filter_by(unit_id=unit.id).first() or MaintenanceRequest(
                unit_id=unit.id, title="Leaky faucet", description="Kitchen sink dripping", status="open"
            )
            db.session.add(mr)

            db.session.commit()
            print("✔ Core sample data seeded via ORM")
    except Exception as e:
        # Fallback: raw SQL with common table/column names; safe to skip if tables differ
        print(f"ℹ ORM seed skipped ({e}); trying raw SQL fallback…")
        if is_postgres():
            try:
                exec_sql("INSERT INTO properties (name, address) VALUES ('Sunset Villas','123 Palm Ave') ON CONFLICT DO NOTHING;")
                pid = get_scalar("SELECT id FROM properties WHERE name='Sunset Villas' LIMIT 1;")
                if pid:
                    exec_sql("INSERT INTO units (code, bedrooms, bathrooms, property_id) VALUES ('A-101',2,1,:pid) ON CONFLICT DO NOTHING;", pid=pid)
                tid = get_scalar("SELECT id FROM tenants WHERE email='tenant1@example.com' LIMIT 1;")
                if not tid:
                    exec_sql("""INSERT INTO tenants (first_name,last_name,email,phone)
                                VALUES ('Taylor','Jones','tenant1@example.com','555-0101')""")
                print("✔ Core sample data seeded (raw SQL fallback)")
            except IntegrityError:
                print("✔ Core sample data already exists (raw SQL fallback)")
            except Exception as ee:
                print(f"⚠ Raw SQL fallback failed: {ee}")
        else:
            print("⚠ No fallback executed (not Postgres).")

if __name__ == "__main__":
    with app.app_context():
        try:
            ensure_admin()
            seed_core()
            print("✅ Seeding complete")
        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            raise
