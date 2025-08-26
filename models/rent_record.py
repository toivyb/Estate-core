from . import db
from datetime import datetime, date

class RentRecord(db.Model):
    __tablename__ = 'rent_records'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)
    property_id = db.Column(db.Integer, nullable=False, index=True) 
    unit = db.Column(db.String(50), nullable=True)
    
    # Financial details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    late_fee = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Dates
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.DateTime, nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='unpaid', index=True)  # 'unpaid', 'paid', 'partial', 'overdue'
    late_fee_applied = db.Column(db.Boolean, default=False)
    reminders_sent = db.Column(db.Integer, default=0)
    
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
            "tenant_id": self.tenant_id,
            "property_id": self.property_id,
            "unit": self.unit,
            "amount": float(self.amount),
            "late_fee": float(self.late_fee),
            "total_amount": float(self.total_amount),
            "due_date": self.due_date.isoformat(),
            "paid_date": self.paid_date.isoformat() if self.paid_date else None,
            "status": self.status,
            "late_fee_applied": self.late_fee_applied,
            "reminders_sent": self.reminders_sent,
            "created_at": self.created_at.isoformat(),
            "notes": self.notes,
            "preferred_payment_method": self.preferred_payment_method
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