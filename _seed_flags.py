from app import create_app, db
from app.models import FeatureFlag
app = create_app()
with app.app_context():
    defaults = {"beta_dashboard": False, "maintenance_mode": False}
    for k, v in defaults.items():
        row = FeatureFlag.query.filter_by(key=k).first()
        if not row:
            db.session.add(FeatureFlag(key=k, enabled=v))
    db.session.commit()
    print("seeded flags")
