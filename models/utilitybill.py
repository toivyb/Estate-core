from estatecore_backend.app.extensions import db

class UtilityBill(db.Model):
    __tablename__ = "utility_bill"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # e.g., "electric", "water", "gas"
    amount = db.Column(db.Float, nullable=False)
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
