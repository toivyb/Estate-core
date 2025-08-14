from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, timedelta
import csv, io, json

from ..models import db
from ..models.rent import Rent
from ..utils.pdf import generate_rent_receipt
from ..utils.email import send_rent_reminder
from ..utils.sms import send_rent_reminder_sms

rent_bp = Blueprint("rent", __name__)

@rent_bp.route("/api/rent/bulk_upload", methods=["POST"])
def bulk_upload_rent():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    ext = file.filename.rsplit(".", 1)[-1].lower()

    if ext == "csv":
        reader = csv.DictReader(io.StringIO(file.read().decode()))
        for row in reader:
            rent = Rent(
                tenant_id=int(row["tenant_id"]),
                property_id=int(row["property_id"]),
                amount=float(row["amount"]),
                due_date=datetime.strptime(row["due_date"], "%Y-%m-%d").date(),
                status=row.get("status", "unpaid"),
            )
            db.session.add(rent)
        db.session.commit()

    elif ext == "json":
        data = json.load(file)
        for entry in data:
            rent = Rent(
                tenant_id=int(entry["tenant_id"]),
                property_id=int(entry["property_id"]),
                amount=float(entry["amount"]),
                due_date=datetime.strptime(entry["due_date"], "%Y-%m-%d").date(),
                status=entry.get("status", "unpaid"),
            )
            db.session.add(rent)
        db.session.commit()
    else:
        return jsonify({"error": "Invalid file format"}), 400

    return jsonify({"status": "success"})

@rent_bp.route("/api/rent/mark_paid/<int:rent_id>", methods=["POST"])
def mark_paid(rent_id):
    rent = Rent.query.get(rent_id)
    if not rent:
        return jsonify({"error": "Not found"}), 404
    rent.status = "paid"
    rent.paid_on = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "success"})

@rent_bp.route("/api/rent/mark_unpaid/<int:rent_id>", methods=["POST"])
def mark_unpaid(rent_id):
    rent = Rent.query.get(rent_id)
    if not rent:
        return jsonify({"error": "Not found"}), 404
    rent.status = "unpaid"
    rent.paid_on = None
    db.session.commit()
    return jsonify({"status": "success"})

@rent_bp.route("/api/rent/reminders/send", methods=["POST"])
def send_reminders():
    rents = Rent.query.filter_by(status="unpaid").all()
    for rent in rents:
        send_rent_reminder(rent)
        send_rent_reminder_sms(rent)
        rent.reminders_sent = (rent.reminders_sent or 0) + 1
    db.session.commit()
    return jsonify({"status": "sent"})

@rent_bp.route("/api/rent/pdf/<int:rent_id>", methods=["GET"])
def rent_pdf(rent_id):
    rent = Rent.query.get(rent_id)
    if not rent:
        return jsonify({"error": "Not found"}), 404
    pdf_path = generate_rent_receipt(rent)
    return send_file(pdf_path, as_attachment=True)

@rent_bp.route("/api/rent", methods=["GET"])
def list_rents():
    query = Rent.query
    month = request.args.get("month")
    tenant_id = request.args.get("tenant_id")
    status = request.args.get("status")
    property_id = request.args.get("property_id")

    if month:
        m = datetime.strptime(month, "%Y-%m")
        next_month = (m.replace(day=28) + timedelta(days=4)).replace(day=1)
        query = query.filter(Rent.due_date >= m, Rent.due_date < next_month)
    if tenant_id:
        query = query.filter_by(tenant_id=int(tenant_id))
    if status:
        query = query.filter_by(status=status)
    if property_id:
        query = query.filter_by(property_id=int(property_id))

    results = query.all()
    return jsonify(rents=[r.serialize() for r in results])
