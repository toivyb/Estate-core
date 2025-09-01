from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from .. import db
from ..models import RentInvoice, Payment, WorkOrder

bp = Blueprint("reporting", __name__)

@bp.get("/reporting/rent-summary")
@jwt_required()
def rent_summary():
    month = request.args.get("month")
    q = db.session.query(func.sum(RentInvoice.amount_cents))
    if month: q = q.filter(RentInvoice.period==month)
    total = q.scalar() or 0
    paid = db.session.query(func.sum(Payment.amount_cents)).scalar() or 0
    return jsonify({"period": month, "total_cents": int(total), "paid_cents": int(paid)})

@bp.get("/reporting/workorder-status")
@jwt_required()
def wo_status():
    rows = db.session.query(WorkOrder.status, func.count(WorkOrder.id)).group_by(WorkOrder.status).all()
    return jsonify({k:v for k,v in rows})
