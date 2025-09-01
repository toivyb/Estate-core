from estatecore_backend import db
from datetime import datetime

class AssetHealth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    score = db.Column(db.Float)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)