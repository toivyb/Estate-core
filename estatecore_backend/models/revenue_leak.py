from estatecore_backend import db
from datetime import datetime

class RevenueLeak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    unit = db.Column(db.String(50))
    issue = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)