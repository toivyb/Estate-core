
from datetime import datetime
from .. import db

class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), index=True)
    event = db.Column(db.String(50), nullable=False)  # allow, deny
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    property = db.relationship('Property', back_populates='access_logs')
