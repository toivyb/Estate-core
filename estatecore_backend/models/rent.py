from . import db

class Rent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False)
    property_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_on = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String, default='unpaid')
    late_fee = db.Column(db.Float, default=0)
    reminders_sent = db.Column(db.Integer, default=0)

    def serialize(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "property_id": self.property_id,
            "amount": self.amount,
            "due_date": self.due_date.isoformat(),
            "paid_on": self.paid_on.isoformat() if self.paid_on else None,
            "status": self.status,
            "late_fee": self.late_fee,
        }
