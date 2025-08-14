from datetime import datetime
from .. import db
class RentStatus:
    PAID = "paid"; PARTIAL = "partial"; UNPAID = "unpaid"
class RentInvoice(db.Model):
    __tablename__ = 'rent_invoice'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    period = db.Column(db.String(7), nullable=False)  # YYYY-MM
    amount_cents = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=RentStatus.UNPAID)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tenant = db.relationship('Tenant', lazy='joined')
    property = db.relationship('Property', lazy='joined')
