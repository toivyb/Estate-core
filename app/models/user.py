from .utils import db
from passlib.hash import pbkdf2_sha256 as hasher

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="admin")
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, raw):
        self.password_hash = hasher.hash(raw)

    def check_password(self, raw):
        return hasher.verify(raw, self.password_hash)
