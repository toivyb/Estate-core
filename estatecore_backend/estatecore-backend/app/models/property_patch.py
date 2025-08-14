# app/models/property_patch.py
# Reference snippet: add to your real app/models/property.py

from estatecore_backend import db

class Property(db.Model):
    __tablename__ = 'property'  # adjust if your project uses a different name
    id = db.Column(db.Integer, primary_key=True)

    # ADD THIS RELATIONSHIP:
    tenants = db.relationship(
        'Tenant',
        back_populates='property',
        cascade="all, delete-orphan"
    )
