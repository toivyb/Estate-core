from . import db
from datetime import datetime, date

class RentRecord(db.Model):
    __tablename__ = 'rent_records'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    
    # Financial details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    late_fee = db.Column(db.Numeric(10, 2), default=0)
    other_fees = db.Column(db.Numeric(10, 2), default=0)  # parking, pet fees, etc.
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), default=0)
    amount_outstanding = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Dates
    period_start = db.Column(db.Date, nullable=False)  # Rental period start
    period_end = db.Column(db.Date, nullable=False)    # Rental period end
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.DateTime, nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='unpaid', index=True)  # 'unpaid', 'paid', 'partial', 'overdue'
    late_fee_applied = db.Column(db.Boolean, default=False)
    reminders_sent = db.Column(db.Integer, default=0)
    last_reminder_sent = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Payment method for this rent period
    preferred_payment_method = db.Column(db.String(20), default='card')  # 'card', 'ach', 'check'
    
    def __repr__(self):
        return f'<RentRecord {self.id}: Tenant {self.tenant_id}, ${self.amount}, Due {self.due_date}>'
    
    def serialize(self):
        return {
            "id": self.id,
            "lease_id": self.lease_id,
            "tenant_id": self.tenant_id,
            "property_id": self.property_id,
            "unit_id": self.unit_id,
            "amount": float(self.amount),
            "late_fee": float(self.late_fee),
            "other_fees": float(self.other_fees),
            "total_amount": float(self.total_amount),
            "amount_paid": float(self.amount_paid),
            "amount_outstanding": float(self.amount_outstanding),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "due_date": self.due_date.isoformat(),
            "paid_date": self.paid_date.isoformat() if self.paid_date else None,
            "status": self.status,
            "late_fee_applied": self.late_fee_applied,
            "reminders_sent": self.reminders_sent,
            "last_reminder_sent": self.last_reminder_sent.isoformat() if self.last_reminder_sent else None,
            "created_at": self.created_at.isoformat(),
            "notes": self.notes,
            "preferred_payment_method": self.preferred_payment_method,
            "tenant_name": self.tenant.full_name if self.tenant else None,
            "property_name": self.property.name if self.property else None,
            "unit_number": self.unit.unit_number if self.unit else None
        }
    
    @property
    def is_overdue(self):
        """Check if rent is overdue"""
        return self.status == 'unpaid' and self.due_date < date.today()
    
    @property
    def days_overdue(self):
        """Get number of days overdue (0 if not overdue)"""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days
    
    def calculate_total_amount(self):
        """Calculate total amount including late fees"""
        self.total_amount = self.amount + (self.late_fee or 0)
        return self.total_amount
    
    def mark_paid(self, payment_date=None):
        """Mark rent as paid"""
        self.status = 'paid'
        self.paid_date = payment_date or datetime.utcnow()
    
    def apply_late_fee(self, late_fee_amount):
        """Apply late fee if not already applied"""
        if not self.late_fee_applied:
            self.late_fee = late_fee_amount
            self.late_fee_applied = True
            self.calculate_total_amount()
            return True
        return False