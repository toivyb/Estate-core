from estatecore_backend import db
from datetime import datetime

class IncidentReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)