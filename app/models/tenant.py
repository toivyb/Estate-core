from .. import db
class Tenant(db.Model):
    __tablename__ = 'tenant'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), index=True)
    unit = db.Column(db.String(64))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    property = db.relationship('Property', back_populates='tenants')
