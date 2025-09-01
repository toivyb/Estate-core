# scripts/seed_flags.py
from app import create_app, db
from app.models import FeatureFlag  # assumes exported
DEFAULT_FLAGS = {"smoke_flag": True}

app = create_app()
with app.app_context():
    for k, v in DEFAULT_FLAGS.items():
        ff = FeatureFlag.query.filter_by(key=k).first()
        if not ff:
            ff = FeatureFlag(key=k, enabled=bool(v))
            db.session.add(ff)
        else:
            ff.enabled = bool(v)
    db.session.commit()
    print("Seeded feature flags:", list(DEFAULT_FLAGS.keys()))
