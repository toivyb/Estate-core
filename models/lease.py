from . import db
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class Lease(db.Model):
    __tablename__ = 'leases'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    
    # Lease Terms
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    lease_term_months = db.Column(db.Integer, nullable=False)
    
    # Financial Terms
    monthly_rent = db.Column(db.Numeric(10, 2), nullable=False)
    security_deposit = db.Column(db.Numeric(10, 2), default=0)
    pet_deposit = db.Column(db.Numeric(10, 2), default=0)
    late_fee_amount = db.Column(db.Numeric(10, 2), default=50)
    late_fee_grace_days = db.Column(db.Integer, default=5)
    
    # Lease Details
    lease_type = db.Column(db.String(20), default='fixed')  # fixed, month_to_month
    payment_due_day = db.Column(db.Integer, default=1)  # Day of month rent is due
    auto_renew = db.Column(db.Boolean, default=False)
    renewal_notice_days = db.Column(db.Integer, default=60)
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, active, expired, terminated, renewed
    signed_date = db.Column(db.Date, nullable=True)
    termination_date = db.Column(db.Date, nullable=True)
    termination_reason = db.Column(db.String(200), nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    tenants = db.relationship('Tenant', secondary='lease_tenants', back_populates='leases')
    rent_records = db.relationship('RentRecord', backref='lease', lazy=True)
    documents = db.relationship('LeaseDocument', backref='lease', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Lease {self.id}: {self.start_date} to {self.end_date}>'
    
    def serialize(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'unit_id': self.unit_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'lease_term_months': self.lease_term_months,
            'monthly_rent': float(self.monthly_rent),
            'security_deposit': float(self.security_deposit),
            'pet_deposit': float(self.pet_deposit),
            'late_fee_amount': float(self.late_fee_amount),
            'late_fee_grace_days': self.late_fee_grace_days,
            'lease_type': self.lease_type,
            'payment_due_day': self.payment_due_day,
            'auto_renew': self.auto_renew,
            'renewal_notice_days': self.renewal_notice_days,
            'status': self.status,
            'signed_date': self.signed_date.isoformat() if self.signed_date else None,
            'termination_date': self.termination_date.isoformat() if self.termination_date else None,
            'termination_reason': self.termination_reason,
            'created_at': self.created_at.isoformat(),
            'notes': self.notes,
            'tenant_names': [tenant.full_name for tenant in self.tenants],
            'property_name': self.property.name if self.property else None,
            'unit_number': self.unit.unit_number if self.unit else None
        }
    
    @property
    def is_active(self):
        """Check if lease is currently active"""
        return (self.status == 'active' and 
                self.start_date <= date.today() <= self.end_date)
    
    @property
    def is_expired(self):
        """Check if lease has expired"""
        return date.today() > self.end_date
    
    @property
    def days_until_expiration(self):
        """Get number of days until lease expires"""
        if self.is_expired:
            return 0
        return (self.end_date - date.today()).days
    
    @property
    def primary_tenant(self):
        """Get the primary tenant (first tenant added to lease)"""
        return self.tenants[0] if self.tenants else None
    
    def activate(self):
        """Activate the lease and update unit status"""
        self.status = 'active'
        if self.unit:
            self.unit.status = 'occupied'
    
    def terminate(self, termination_date=None, reason=None):
        """Terminate the lease"""
        self.status = 'terminated'
        self.termination_date = termination_date or date.today()
        self.termination_reason = reason
        if self.unit:
            self.unit.status = 'available'
    
    def generate_rent_records(self, months_ahead=12):
        """Generate rent records for this lease"""
        from .rent_record import RentRecord
        
        # Start from lease start date or current date, whichever is later
        start_date = max(self.start_date, date.today().replace(day=1))
        records_created = []
        
        for i in range(months_ahead):
            due_date = start_date + relativedelta(months=i)
            due_date = due_date.replace(day=self.payment_due_day)
            
            # Don't create records past lease end date
            if due_date > self.end_date:
                break
            
            # Check if record already exists
            existing_record = RentRecord.query.filter_by(
                lease_id=self.id,
                due_date=due_date
            ).first()
            
            if not existing_record:
                rent_record = RentRecord(
                    lease_id=self.id,
                    tenant_id=self.primary_tenant.id if self.primary_tenant else None,
                    property_id=self.property_id,
                    unit_id=self.unit_id,
                    amount=self.monthly_rent,
                    due_date=due_date,
                    status='unpaid'
                )
                db.session.add(rent_record)
                records_created.append(rent_record)
        
        db.session.commit()
        return records_created


# Association table for many-to-many relationship between Lease and Tenant
lease_tenants = db.Table('lease_tenants',
    db.Column('lease_id', db.Integer, db.ForeignKey('leases.id'), primary_key=True),
    db.Column('tenant_id', db.Integer, db.ForeignKey('tenants.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)


class LeaseDocument(db.Model):
    __tablename__ = 'lease_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'), nullable=False)
    
    # Document Information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    
    # Document Type and Metadata
    document_type = db.Column(db.String(50), default='lease')  # lease, addendum, amendment, notice
    description = db.Column(db.String(500), nullable=True)
    is_signed = db.Column(db.Boolean, default=False)
    signed_date = db.Column(db.Date, nullable=True)
    
    # Upload Information
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def __repr__(self):
        return f'<LeaseDocument {self.id}: {self.filename}>'
    
    def serialize(self):
        return {
            'id': self.id,
            'lease_id': self.lease_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'document_type': self.document_type,
            'description': self.description,
            'is_signed': self.is_signed,
            'signed_date': self.signed_date.isoformat() if self.signed_date else None,
            'uploaded_at': self.uploaded_at.isoformat()
        }