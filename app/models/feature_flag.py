from app import db

class FeatureFlag(db.Model):
    __tablename__ = "feature_flag"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
