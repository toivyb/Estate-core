from estatecore_backend.extensions import db
from datetime import datetime

class LPREvent(db.Model):
    __tablename__ = 'lpr_events'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    plate = db.Column(db.String(20), nullable=False)
    camera = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<LPREvent {self.plate} at {self.timestamp}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
            'plate': self.plate,
            'camera': self.camera,
            'confidence': self.confidence,
            'image_url': self.image_url,
            'notes': self.notes
        }