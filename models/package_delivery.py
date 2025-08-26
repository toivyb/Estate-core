from estatecore_backend import db
from datetime import datetime

class PackageDelivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    delivered_by = db.Column(db.String)
    picked_up_by = db.Column(db.String)
    status = db.Column(db.String, default="Delivered")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    picked_up_at = db.Column(db.DateTime, nullable=True)