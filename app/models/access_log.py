from estatecore_backend import db
from datetime import datetime

class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gate_name = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    result = db.Column(db.String(50))  # e.g. "granted" or "denied"

    user = db.relationship('User', backref='access_logs')
