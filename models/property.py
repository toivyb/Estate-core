from . import db
from datetime import datetime


class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(512), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    property_type = db.Column(db.String(50), default='residential')  # residential, commercial, mixed
    
    # Property details
    total_units = db.Column(db.Integer, default=1)
    bedrooms = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Numeric(3, 1), nullable=True)
    square_feet = db.Column(db.Integer, nullable=True)
    year_built = db.Column(db.Integer, nullable=True)
    
    # Financial information
    purchase_price = db.Column(db.Numeric(12, 2), nullable=True)
    current_market_value = db.Column(db.Numeric(12, 2), nullable=True)
    monthly_mortgage = db.Column(db.Numeric(10, 2), nullable=True)
    monthly_insurance = db.Column(db.Numeric(10, 2), nullable=True)
    monthly_taxes = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Status and metadata
    status = db.Column(db.String(20), default='active')  # active, inactive, sold
    acquisition_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    units = db.relationship('Unit', backref='property', lazy=True, cascade='all, delete-orphan')
    leases = db.relationship('Lease', backref='property', lazy=True)
    maintenance_requests = db.relationship('MaintenanceRequest', backref='property', lazy=True)
    
    def __repr__(self):
        return f'<Property {self.id}: {self.name}>'
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'property_type': self.property_type,
            'total_units': self.total_units,
            'bedrooms': self.bedrooms,
            'bathrooms': float(self.bathrooms) if self.bathrooms else None,
            'square_feet': self.square_feet,
            'year_built': self.year_built,
            'purchase_price': float(self.purchase_price) if self.purchase_price else None,
            'current_market_value': float(self.current_market_value) if self.current_market_value else None,
            'monthly_mortgage': float(self.monthly_mortgage) if self.monthly_mortgage else None,
            'monthly_insurance': float(self.monthly_insurance) if self.monthly_insurance else None,
            'monthly_taxes': float(self.monthly_taxes) if self.monthly_taxes else None,
            'status': self.status,
            'acquisition_date': self.acquisition_date.isoformat() if self.acquisition_date else None,
            'created_at': self.created_at.isoformat(),
            'notes': self.notes,
            'unit_count': len(self.units)
        }


class Unit(db.Model):
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    unit_number = db.Column(db.String(50), nullable=False)
    
    # Unit details
    bedrooms = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Numeric(3, 1), nullable=True)
    square_feet = db.Column(db.Integer, nullable=True)
    rent_amount = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Unit status
    status = db.Column(db.String(20), default='available')  # available, occupied, maintenance, unavailable
    is_rentable = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    leases = db.relationship('Lease', backref='unit', lazy=True)
    maintenance_requests = db.relationship('MaintenanceRequest', backref='unit', lazy=True)
    
    # Unique constraint for property_id and unit_number
    __table_args__ = (db.UniqueConstraint('property_id', 'unit_number'),)
    
    def __repr__(self):
        return f'<Unit {self.id}: {self.unit_number} at Property {self.property_id}>'
    
    def serialize(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'unit_number': self.unit_number,
            'bedrooms': self.bedrooms,
            'bathrooms': float(self.bathrooms) if self.bathrooms else None,
            'square_feet': self.square_feet,
            'rent_amount': float(self.rent_amount) if self.rent_amount else None,
            'status': self.status,
            'is_rentable': self.is_rentable,
            'created_at': self.created_at.isoformat(),
            'notes': self.notes
        }
    
    @property
    def current_tenant(self):
        """Get the current tenant for this unit"""
        active_lease = Lease.query.filter_by(
            unit_id=self.id, 
            status='active'
        ).first()
        return active_lease.tenant if active_lease else None