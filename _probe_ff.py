from app import create_app
from sqlalchemy import text
app = create_app()
with app.app_context():
    from app.models import FeatureFlag
    from app import db
    # check alembic head and table access
    v = db.session.execute(text("select version_num from alembic_version")).scalar()
    c = db.session.query(FeatureFlag).count()
    print("alembic_version:", v, "feature_flag count:", c)
