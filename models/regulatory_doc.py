from estatecore_backend import db
from datetime import datetime

class RegulatoryDoc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    doc_type = db.Column(db.String(100))
    expires_on = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)