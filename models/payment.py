from . import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    rent_record_id = db.Column(db.Integer, db.ForeignKey('rent_records.id'), nullable=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # 'card', 'ach', 'cash', 'check'
    
    # Status tracking  
    status = db.Column(db.String(20), default='pending', index=True)  # 'pending', 'completed', 'failed', 'refunded'
    
    # External payment processor data
    stripe_payment_intent_id = db.Column(db.String(80), nullable=True, index=True)
    stripe_charge_id = db.Column(db.String(80), nullable=True, index=True)
    transaction_id = db.Column(db.String(100), nullable=True)  # For other payment processors
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Additional details
    description = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    receipt_url = db.Column(db.String(500), nullable=True)
    
    # Relationship to rent record
    rent_record = db.relationship('RentRecord', backref='payments', lazy=True)
    
    def __repr__(self):
        return f'<Payment {self.id}: ${self.amount} - {self.status}>'
    
    def serialize(self):
        return {
            "id": self.id,
            "rent_record_id": self.rent_record_id,
            "tenant_id": self.tenant_id,
            "amount": float(self.amount),
            "payment_method": self.payment_method,
            "status": self.status,
            "stripe_payment_intent_id": self.stripe_payment_intent_id,
            "transaction_id": self.transaction_id,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "description": self.description,
            "notes": self.notes,
            "receipt_url": self.receipt_url
        }
    
    def mark_completed(self):
        """Mark payment as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        # Update associated rent record if exists
        if self.rent_record:
            self.rent_record.mark_paid(self.completed_at)
    
    def mark_failed(self, reason=None):
        """Mark payment as failed"""
        self.status = 'failed'
        if reason:
            self.notes = reason