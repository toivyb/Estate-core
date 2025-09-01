from datetime import datetime
from .. import db

class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"))
    status = db.Column(db.String(50), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
