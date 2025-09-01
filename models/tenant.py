from . import db
from datetime import datetime


class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Personal Information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone_primary = db.Column(db.String(20), nullable=True)
    phone_secondary = db.Column(db.String(20), nullable=True)
    
    # Address Information
    mailing_address = db.Column(db.String(512), nullable=True)
    mailing_city = db.Column(db.String(100), nullable=True)
    mailing_state = db.Column(db.String(50), nullable=True)
    mailing_zip = db.Column(db.String(20), nullable=True)
    
    # Emergency Contact
    emergency_contact_name = db.Column(db.String(200), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    emergency_contact_relationship = db.Column(db.String(50), nullable=True)
    
    # Employment Information
    employer_name = db.Column(db.String(200), nullable=True)
    employer_phone = db.Column(db.String(20), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    monthly_income = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Tenant Status
    status = db.Column(db.String(20), default='active')  # active, inactive, former, applicant
    move_in_date = db.Column(db.Date, nullable=True)
    move_out_date = db.Column(db.Date, nullable=True)
    
    # Financial Information
    credit_score = db.Column(db.Integer, nullable=True)
    security_deposit_paid = db.Column(db.Numeric(10, 2), default=0)
    pet_deposit_paid = db.Column(db.Numeric(10, 2), default=0)
    
    # Preferences and Notes
    preferred_payment_method = db.Column(db.String(20), default='card')  # card, ach, check, cash
    communication_preference = db.Column(db.String(20), default='email')  # email, sms, phone, mail
    has_pets = db.Column(db.Boolean, default=False)
    pet_details = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    leases = db.relationship('Lease', secondary='lease_tenants', back_populates='tenants', lazy='dynamic')
    rent_records = db.relationship('RentRecord', backref='tenant', lazy=True)
    payments = db.relationship('Payment', backref='tenant', lazy=True)
    maintenance_requests = db.relationship('MaintenanceRequest', backref='tenant', lazy=True)
    
    def __repr__(self):
        return f'<Tenant {self.id}: {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def current_lease(self):
        """Get the current active lease for this tenant"""
        return self.leases.filter_by(status='active').first()
    
    @property
    def current_unit(self):
        """Get the current unit this tenant is in"""
        current_lease = self.current_lease
        return current_lease.unit if current_lease else None
    
    def serialize(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone_primary': self.phone_primary,
            'phone_secondary': self.phone_secondary,
            'mailing_address': self.mailing_address,
            'mailing_city': self.mailing_city,
            'mailing_state': self.mailing_state,
            'mailing_zip': self.mailing_zip,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relationship': self.emergency_contact_relationship,
            'employer_name': self.employer_name,
            'employer_phone': self.employer_phone,
            'job_title': self.job_title,
            'monthly_income': float(self.monthly_income) if self.monthly_income else None,
            'status': self.status,
            'move_in_date': self.move_in_date.isoformat() if self.move_in_date else None,
            'move_out_date': self.move_out_date.isoformat() if self.move_out_date else None,
            'credit_score': self.credit_score,
            'security_deposit_paid': float(self.security_deposit_paid),
            'pet_deposit_paid': float(self.pet_deposit_paid),
            'preferred_payment_method': self.preferred_payment_method,
            'communication_preference': self.communication_preference,
            'has_pets': self.has_pets,
            'pet_details': self.pet_details,
            'created_at': self.created_at.isoformat(),
            'notes': self.notes,
            'current_lease_id': self.current_lease.id if self.current_lease else None,
            'current_unit_id': self.current_unit.id if self.current_unit else None
        }
    
    def get_payment_history(self, limit=10):
        """Get recent payment history for this tenant"""
        return Payment.query.filter_by(tenant_id=self.id)\
            .order_by(Payment.created_at.desc())\
            .limit(limit).all()
    
    def get_outstanding_rent(self):
        """Get total outstanding rent for this tenant"""
        outstanding_records = RentRecord.query.filter_by(
            tenant_id=self.id,
            status='unpaid'
        ).all()
        return sum(record.total_amount for record in outstanding_records)