from .utils import db
from datetime import datetime

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    unit = db.Column(db.String(64))
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"))

class RentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"))
    month = db.Column(db.String(7), nullable=False) # YYYY-MM
    amount_due = db.Column(db.Numeric(10,2), default=0)
    amount_paid = db.Column(db.Numeric(10,2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
