from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from .. import db
from ..models import MessageThread, Message, MessageParticipant

bp = Blueprint("messages", __name__)

@bp.post("/messages/threads")
@jwt_required()
def create_thread():
    d = request.get_json() or {}
    t = MessageThread(subject=d["subject"])
    db.session.add(t); db.session.flush()
    for uid in d.get("participants", []):
        db.session.add(MessageParticipant(thread_id=t.id, user_id=uid))
    db.session.commit()
    return jsonify({"id": t.id}), 201

@bp.post("/messages/threads/<int:tid>/messages")
@jwt_required()
def post_message(tid):
    claims = get_jwt()
    d = request.get_json() or {}
    m = Message(thread_id=tid, author_id=claims.get("sub") or claims.get("id"), body=d["body"])
    db.session.add(m); db.session.commit()
    return jsonify({"id": m.id}), 201

@bp.get("/messages/threads/<int:tid>")
@jwt_required()
def get_thread(tid):
    msgs = Message.query.filter_by(thread_id=tid).order_by(Message.id.asc()).all()
    return jsonify([{"id":x.id,"body":x.body,"author_id":x.author_id,"created_at":x.created_at.isoformat()} for x in msgs])
