from estatecore_backend import db

class AISummary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100))
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
