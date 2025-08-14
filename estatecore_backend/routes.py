from flask import Blueprint, request, jsonify, send_file
from .extensions import db
from estatecore_backend.models import User, RentRecord, AccessLog, InviteToken, MaintenanceRequest
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from io import BytesIO
from reportlab.pdfgen import canvas
from flask_jwt_extended import jwt_required, get_jwt_identity
import uuid
import csv
import json
from datetime import datetime, date

api_bp = Blueprint("api", __name__)

# ---- Access Check ----
@api_bp.route("/access/check", methods=["POST"])
def access_check():
    data = request.get_json() or {}
    plate = data.get("plate")

    now = datetime.utcnow()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    if not plate:
        log = AccessLog(time=timestamp, user="UNKNOWN", door="GATE", status="denied - no plate")
        db.session.add(log)
        db.session.commit()
        return jsonify({"access": "denied", "reason": "Plate missing"}), 400

    user = User.query.filter_by(plate=plate).first()
    if not user:
        log = AccessLog(time=timestamp, user=plate, door="GATE", status="denied - unknown plate")
        db.session.add(log)
        db.session.commit()
        return jsonify({"access": "denied", "reason": "Unknown plate"}), 404

    rent = RentRecord.query.filter_by(name=user.name, status="Paid").first()

    if rent:
        log = AccessLog(time=timestamp, user=user.name, door="GATE", status="granted")
        db.session.add(log)
        db.session.commit()

        # 🔁 Optional relay trigger
        # import requests
        # requests.post("http://your-relay-device/unlock")

        return jsonify({"access": "granted", "user_id": user.id})
    else:
        log = AccessLog(time=timestamp, user=user.name, door="GATE", status="denied - unpaid rent")
        db.session.add(log)
        db.session.commit()
        return jsonify({"access": "denied", "reason": "Unpaid rent"})

# ---- Simulate Access Log ----
@api_bp.route("/access-logs/simulate", methods=["POST"])
@jwt_required()
def simulate_log():
    data = request.get_json() or {}
    log = AccessLog(
        time=data.get("time", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        user=data.get("user", "SimUser"),
        door=data.get("door", "SimDoor"),
        status=data.get("status", "SimStatus")
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"msg": "Log simulated"})

# ---- View Access Logs ----
@api_bp.route("/access-logs", methods=["GET"])
@jwt_required()
def access_logs():
    logs = AccessLog.query.order_by(AccessLog.id.desc()).limit(20).all()
    return jsonify([{
        "time": l.time,
        "user": l.user,
        "door": l.door,
        "status": l.status
    } for l in logs])
@api_bp.route("/relay/unlock", methods=["POST"])
@jwt_required()
def manual_unlock():
    # Stubbed logic - replace with real relay call
    print("Manual unlock triggered.")
    return jsonify({"msg": "Relay unlock triggered"}), 200

@api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"msg": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify(access_token=access_token)

@api_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    })