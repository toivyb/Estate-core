import uuid
from estatecore_backend import db
from datetime import datetime, timedelta

class InviteToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))

    def is_valid(self):
        return datetime.utcnow() < self.expires_at
