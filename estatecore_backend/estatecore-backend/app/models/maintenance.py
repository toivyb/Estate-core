
from datetime import datetime
from .. import db

class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id', ondelete='CASCADE'), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id', ondelete='SET NULL'), index=True)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = db.relationship('Property', back_populates='maintenance_requests')
    comments = db.relationship('MaintenanceComment', back_populates='request', cascade='all, delete-orphan')

class MaintenanceComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('maintenance_request.id', ondelete='CASCADE'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    request = db.relationship('MaintenanceRequest', back_populates='comments')
