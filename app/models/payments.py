from datetime import datetime
from .. import db

class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    rent_invoice_id = db.Column(db.Integer, db.ForeignKey('rent_invoice.id'), nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    method = db.Column(db.String(50))                       # 'card' | 'us_bank_account'
    reference = db.Column(db.String(120))                   # legacy/local ref
    status = db.Column(db.String(40), default='pending')    # 'pending' | 'succeeded' | 'failed' | 'refunded'
    stripe_payment_intent_id = db.Column(db.String(80), index=True)
    stripe_charge_id = db.Column(db.String(80), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoice = db.relationship('RentInvoice', backref='payments')
