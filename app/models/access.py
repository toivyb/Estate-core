from datetime import datetime
from .. import db

class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), nullable=False)
    door = db.Column(db.String(100))
    status = db.Column(db.String(20), default="granted")
    ts = db.Column(db.DateTime, default=datetime.utcnow)
