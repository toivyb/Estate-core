
from estatecore_backend import db
from datetime import datetime

class TrainingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(64), unique=True, nullable=False)
    last_trained = db.Column(db.DateTime, default=datetime.utcnow)
    is_enabled = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<TrainingLog {self.model_name}>"
