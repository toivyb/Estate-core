
from datetime import datetime, timedelta
from .. import db
from flask import current_app
import secrets

class InviteToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    role_name = db.Column(db.String(50), nullable=False)  # property_manager/property_admin/tenant
    property_id = db.Column(db.Integer, db.ForeignKey('property.id', ondelete='CASCADE'), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate(email, role_name, property_id, hours=None):
        token = secrets.token_hex(16)
        ttl = hours or int(current_app.config.get("INVITE_TOKEN_TTL_HOURS", 72))
        return InviteToken(
            token=token,
            email=email,
            role_name=role_name,
            property_id=property_id,
            expires_at=datetime.utcnow() + timedelta(hours=ttl)
        )
