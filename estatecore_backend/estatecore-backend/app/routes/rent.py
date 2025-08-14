
from flask import Blueprint, request, send_file, jsonify
from flask_jwt_extended import jwt_required
from .. import db
from ..models.finance import RentRecord
from ..utils.pdf import build_rent_receipt_pdf
from io import BytesIO
from datetime import date

bp = Blueprint('rent', __name__)

@bp.get('/rent')
@jwt_required()
def list_rent():
    month = request.args.get('month')  # YYYY-MM
    q = RentRecord.query
    if month:
        y, m = map(int, month.split('-'))
        first = date(y, m, 1)
        q = q.filter(RentRecord.month == first)
    items = []
    for r in q.limit(500).all():
        items.append({
            'id': r.id, 'property_id': r.property_id, 'unit_id': r.unit_id, 'tenant_id': r.tenant_id,
            'month': r.month.isoformat(), 'amount_due': float(r.amount_due), 'amount_paid': float(r.amount_paid),
            'status': r.status
        })
    return jsonify(items)

@bp.post('/rent')
@jwt_required()
def create_rent():
    data = request.get_json() or {}
    r = RentRecord(**data)
    db.session.add(r)
    db.session.commit()
    return {'id': r.id}

@bp.post('/rent/<int:rid>/mark-paid')
@jwt_required()
def mark_paid(rid):
    r = RentRecord.query.get_or_404(rid)
    r.amount_paid = r.amount_due
    r.status = 'paid'
    db.session.commit()
    return {'ok': True}

@bp.get('/rent/<int:rid>/receipt.pdf')
@jwt_required()
def rent_receipt_pdf(rid):
    r = RentRecord.query.get_or_404(rid)
    pdf_bytes = build_rent_receipt_pdf(r)
    return send_file(BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name=f"rent_receipt_{r.id}.pdf")
