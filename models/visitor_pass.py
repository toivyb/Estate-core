# estatecore_backend/models/visitor_pass.py
import random
import string
from . import db

class VisitorPass(db.Model):
    __tablename__ = "visitor_passes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)

def generate_pin(length=6):
    """Generate a random numeric PIN code."""
    return ''.join(random.choices(string.digits, k=length))
