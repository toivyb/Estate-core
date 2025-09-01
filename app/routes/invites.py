from flask import Blueprint, request, jsonify
from ..models import InviteToken, User
from .. import db

bp = Blueprint("invites", __name__)

@bp.post("/invites/create")
def create_invite():
    data = request.get_json(force=True)
    email = data.get("email")
    role = data.get("role","tenant")
    inv = InviteToken.generate(email=email, role=role, hours=48)
    db.session.add(inv)
    db.session.commit()
    return jsonify({"token": inv.token, "email": inv.email, "role": inv.role, "expires_at": inv.expires_at.isoformat()})

@bp.post("/invites/accept")
def accept_invite():
    data = request.get_json(force=True)
    token = data.get("token")
    password = data.get("password")
    inv = InviteToken.query.filter_by(token=token).first()
    if not inv:
        return jsonify({"msg":"Invalid token"}), 400
    from datetime import datetime
    if inv.expires_at < datetime.utcnow():
        return jsonify({"msg":"Token expired"}), 400
    user = User.query.filter_by(email=inv.email).first()
    if not user:
        user = User(email=inv.email, role=inv.role, is_active=True)
        user.set_password(password)
        db.session.add(user)
    else:
        user.role = inv.role
        user.set_password(password)
    db.session.delete(inv)
    db.session.commit()
    return jsonify({"msg":"Invite accepted", "email": user.email, "role": user.role})
