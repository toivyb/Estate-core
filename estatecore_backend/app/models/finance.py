
from datetime import datetime, date
from .. import db

class RentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id', ondelete='CASCADE'), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id', ondelete='SET NULL'), index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id', ondelete='SET NULL'), index=True)

    month = db.Column(db.Date, nullable=False, default=lambda: date.today().replace(day=1))  # billing period first day
    amount_due = db.Column(db.Numeric(10,2), nullable=False, default=0)
    amount_paid = db.Column(db.Numeric(10,2), nullable=False, default=0)
    due_date = db.Column(db.Date, nullable=False)
    paid_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="unpaid")  # unpaid, partial, paid, late

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    property = db.relationship('Property', back_populates='rent_records')
    unit = db.relationship('Unit', back_populates='rent_records')
    tenant = db.relationship('Tenant', backref='rent_records')
