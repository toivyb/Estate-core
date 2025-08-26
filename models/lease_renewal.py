from estatecore_backend import db
from datetime import datetime

class LeaseRenewal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    suggested_months = db.Column(db.Integer)
    suggested_rent_increase = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)