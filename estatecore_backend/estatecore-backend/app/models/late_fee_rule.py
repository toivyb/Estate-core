from .. import db
class LateFeeRule(db.Model):
    __tablename__ = 'late_fee_rule'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    grace_days = db.Column(db.Integer, default=5)
    flat_fee_cents = db.Column(db.Integer, default=0)
    percent = db.Column(db.Float, default=0.0)
