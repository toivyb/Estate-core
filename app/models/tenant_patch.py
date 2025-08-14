# app/models/tenant_patch.py
# Reference snippet: add to your real app/models/tenant.py

from estatecore_backend import db

class Tenant(db.Model):
    __tablename__ = 'tenant'  # adjust if your project uses a different name
    id = db.Column(db.Integer, primary_key=True)

    # Ensure you have this foreign key column:
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))

    # ADD THIS RELATIONSHIP:
    property = db.relationship(
        'Property',
        back_populates='tenants'
    )
