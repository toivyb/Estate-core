from estatecore_backend import db
from datetime import datetime

class CashFlow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    projected_income = db.Column(db.Float)
    projected_expense = db.Column(db.Float)
    projection_date = db.Column(db.Date, default=datetime.utcnow)