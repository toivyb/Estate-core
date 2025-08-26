from estatecore_backend import db
from datetime import datetime

class EvictionRisk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    risk_score = db.Column(db.Float)
    risk_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)