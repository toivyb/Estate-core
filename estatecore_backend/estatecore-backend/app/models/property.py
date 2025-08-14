
from datetime import datetime
from .. import db

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    units = db.relationship('Unit', back_populates='property', cascade='all, delete-orphan')
    managers = db.relationship('PropertyManager', back_populates='property', cascade='all, delete-orphan')
    tenants = db.relationship('Tenant', back_populates='property', cascade='all, delete-orphan')
    access_logs = db.relationship('AccessLog', back_populates='property', cascade='all, delete-orphan')
    maintenance_requests = db.relationship('MaintenanceRequest', back_populates='property', cascade='all, delete-orphan')
    rent_records = db.relationship('RentRecord', back_populates='property', cascade='all, delete-orphan')

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., "Apt 3B"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    property = db.relationship('Property', back_populates='units')
    tenants = db.relationship('Tenant', back_populates='unit', cascade='all, delete-orphan')
    rent_records = db.relationship('RentRecord', back_populates='unit', cascade='all, delete-orphan')

class PropertyManager(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id', ondelete='CASCADE'), nullable=False, index=True)
    is_admin = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='managed_properties')
    property = db.relationship('Property', back_populates='managers')

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), index=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id', ondelete='CASCADE'), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id', ondelete='SET NULL'), index=True)
    move_in = db.Column(db.Date)
    move_out = db.Column(db.Date)

    property = db.relationship('Property', back_populates='tenants')
    unit = db.relationship('Unit', back_populates='tenants')
