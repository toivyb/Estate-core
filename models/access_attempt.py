from estatecore_backend import db
from datetime import datetime

class AccessAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    gate_name = db.Column(db.String(100))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    result = db.Column(db.String(10))  # "Granted" or "Denied"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.String(255), nullable=True)