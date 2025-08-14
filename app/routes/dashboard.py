from flask import Blueprint, jsonify
from ..models import RentRecord
from sqlalchemy.sql import func
from .. import db

bp = Blueprint("dashboard", __name__)

@bp.get("/dashboard/metrics")
def metrics():
    total_due = db.session.query(func.coalesce(func.sum(RentRecord.amount_due),0)).scalar()
    total_paid = db.session.query(func.coalesce(func.sum(RentRecord.amount_paid),0)).scalar()
    net = float(total_paid or 0) - float(total_due or 0)
    return jsonify({"total_due": float(total_due or 0), "total_paid": float(total_paid or 0), "net": net})
