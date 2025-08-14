from datetime import datetime
from .. import db

class MessageThread(db.Model):
    __tablename__ = 'message_thread'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MessageParticipant(db.Model):
    __tablename__ = 'message_participant'
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('message_thread.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(20), default="member")  # member|admin

class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('message_thread.id'), nullable=False)
    author_id = db.Column(db.Integer, nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
