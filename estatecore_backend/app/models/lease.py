from datetime import datetime, date
from .. import db

class Lease(db.Model):
    __tablename__ = 'lease'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    rent_cents = db.Column(db.Integer, nullable=False)
    deposit_cents = db.Column(db.Integer, default=0)
    frequency = db.Column(db.String(10), default="monthly")  # monthly only supported
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LeaseTenant(db.Model):
    __tablename__ = 'lease_tenant'
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('lease.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)

class LeaseDocument(db.Model):
    __tablename__ = 'lease_document'
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('lease.id'), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    original_name = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
