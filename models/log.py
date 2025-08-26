from . import db

class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    door_id = db.Column(db.String, nullable=False)
    event_type = db.Column(db.String, nullable=False)  # entry, exit, denied, visitor_entry
    reason = db.Column(db.String, nullable=True)  # For denied events
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    visitor_pass_id = db.Column(db.Integer, nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "door_id": self.door_id,
            "event_type": self.event_type,
            "reason": self.reason,
            "timestamp": str(self.timestamp),
            "visitor_pass_id": self.visitor_pass_id,
        }
