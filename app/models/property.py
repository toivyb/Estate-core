from datetime import datetime
from .. import db

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"))
    unit = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
