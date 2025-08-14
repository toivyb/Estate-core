from . import db

class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, nullable=False)
    tenant_id = db.Column(db.Integer, nullable=True)  # null if created by admin
    description = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default='open')  # open, in_progress, closed
    assigned_to = db.Column(db.String, nullable=True)  # vendor/staff
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())
    priority = db.Column(db.String, default='normal')  # normal, urgent
    ai_risk_score = db.Column(db.Float, default=0)  # AI stub

    def serialize(self):
        return {
            "id": self.id,
            "property_id": self.property_id,
            "tenant_id": self.tenant_id,
            "description": self.description,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.updated_at else None,
            "priority": self.priority,
            "ai_risk_score": self.ai_risk_score,
        }
