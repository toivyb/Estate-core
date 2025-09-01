from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}  # ensure Postgres schema is explicit

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Basic Information
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Authentication
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    role = db.Column(db.String(50), nullable=False, default="user")
    
    # Security and Audit Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    password_changed_at = db.Column(db.DateTime, nullable=True)
    
    # Profile Information
    avatar_url = db.Column(db.String(500), nullable=True)
    timezone = db.Column(db.String(50), default='UTC')
    
    # Permissions and Settings
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    
    # Two-Factor Authentication (for future implementation)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)
    
    # Account Status
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    password_reset_token = db.Column(db.String(255), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)

    def set_password(self, password: str) -> None:
        """Hashes and stores the user's password."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        self.password_changed_at = datetime.utcnow()

    def check_password(self, password: str) -> bool:
        """Checks a password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self) -> str:
        """Returns the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in ['super_admin', 'admin']
    
    def can_access_property(self, property_id: int) -> bool:
        """Check if user can access a specific property (for future implementation)."""
        # For now, all active users can access all properties
        # This can be extended with property-specific permissions
        return self.is_active
    
    def serialize(self, include_sensitive=False):
        """Serialize user data for JSON response."""
        data = {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "avatar_url": self.avatar_url,
            "timezone": self.timezone,
            "email_notifications": self.email_notifications,
            "sms_notifications": self.sms_notifications,
            "two_factor_enabled": self.two_factor_enabled,
            "email_verified": self.email_verified
        }
        
        if include_sensitive:
            data.update({
                "last_login_ip": self.last_login_ip,
                "password_changed_at": self.password_changed_at.isoformat() if self.password_changed_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None
            })
        
        return data

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
