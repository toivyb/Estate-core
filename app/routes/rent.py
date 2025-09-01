from flask import Blueprint, request, jsonify
from ..models import RentRecord
from .. import db

bp = Blueprint("rent", __name__)

@bp.post("/rent/record")
def create_rent_record():
    data = request.get_json(force=True)
    rr = RentRecord(
        tenant_id=data.get("tenant_id"),
        month=data.get("month"),
        amount_due=data.get("amount_due", 0),
        amount_paid=data.get("amount_paid", 0),
    )
    db.session.add(rr)
    db.session.commit()
    return jsonify({"id": rr.id})
