from .utils import db
from datetime import datetime, timedelta
import secrets

class InviteToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="tenant")
    expires_at = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def generate(email, role="tenant", hours=24):
        return InviteToken(
            token=secrets.token_urlsafe(24),
            email=email,
            role=role,
            expires_at=datetime.utcnow() + timedelta(hours=hours),
        )
