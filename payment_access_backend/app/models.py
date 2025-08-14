"""
Database models for the payment‑based access control system.

These models define the structure of the database tables used by the
application.  They cover organisations, locations, users (with roles), invite
tokens, payments/subscriptions, and licence plate recognition events.  The
`Payment` model supports both monthly subscriptions (via `valid_until`) and
per‑use credits (`remaining_uses`).
"""

import uuid
from datetime import datetime
from typing import Optional

from werkzeug.security import generate_password_hash, check_password_hash

from . import db


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    locations = db.relationship("Location", backref="organization", lazy=True)
    users = db.relationship("User", backref="organization", lazy=True)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(128))
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class InviteToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), unique=True, default=gen_uuid, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Payment(db.Model):
    """Represents a payment record or subscription for a licence plate.

    A `Payment` record is considered valid if either:
    - `payment_type` is 'monthly' and `valid_until` is in the future; or
    - `payment_type` is 'per_use' and `remaining_uses` is greater than zero.
    """

    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(32), unique=True, nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)  # 'monthly' or 'per_use'
    valid_until = db.Column(db.DateTime, nullable=True)
    remaining_uses = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self, at_time: Optional[datetime] = None) -> bool:
        """Return True if this payment is currently valid.

        If `payment_type` is 'monthly', the payment is valid until `valid_until`.
        If `payment_type` is 'per_use', validity depends on `remaining_uses`.
        """
        now = at_time or datetime.utcnow()
        if self.payment_type == 'monthly':
            return self.valid_until is not None and self.valid_until >= now
        elif self.payment_type == 'per_use':
            return self.remaining_uses is not None and self.remaining_uses > 0
        return False

    def consume_use(self) -> bool:
        """Decrement a per‑use payment and return True if successful."""
        if self.payment_type != 'per_use':
            return False
        if self.remaining_uses and self.remaining_uses > 0:
            self.remaining_uses -= 1
            return True
        return False


class LPREvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(32), nullable=False)
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime)
    camera = db.Column(db.String(64), nullable=True)
    image_url = db.Column(db.String(256), nullable=True)
    notes = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<LPREvent id={self.id} plate={self.plate}>"
class RentInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    amount_due = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tenant = db.relationship('User', backref='rent_invoices')
    property = db.relationship('Property', backref='rent_invoices')


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('rent_invoice.id'), nullable=True)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    method = db.Column(db.String(50))  # 'card', 'cash', etc.

    tenant = db.relationship('User', backref='payments')
    invoice = db.relationship('RentInvoice', backref='payments')

class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pending')  # Pending, In Progress, Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tenant = db.relationship('User', backref='maintenance_requests')
    property = db.relationship('Property', backref='maintenance_requests')
