from .utils import db

class FeatureFlag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=False)
