from datetime import date
from flask import Blueprint, request, jsonify, current_app, send_file, abort
from flask_jwt_extended import jwt_required
from .. import db
from ..models import Lease, LeaseTenant, LeaseDocument, Tenant, RentInvoice
from ..utils.proration import prorate_monthly
from ..utils.uploads import save_file
import os

bp = Blueprint("leases", __name__)

def _cents(n): return int(round(float(n)*100))

@bp.post("/leases")
@jwt_required()
def create_lease():
    d = request.get_json() or {}
    lease = Lease(property_id=d["property_id"], start_date=date.fromisoformat(d["start_date"]),
                  end_date=date.fromisoformat(d["end_date"]), rent_cents=_cents(d["rent"]), deposit_cents=_cents(d.get("deposit",0)))
    db.session.add(lease); db.session.flush()
    for tid in d.get("tenant_ids", []):
        db.session.add(LeaseTenant(lease_id=lease.id, tenant_id=tid))
    db.session.commit()
    return jsonify({"id": lease.id}), 201

@bp.get("/leases")
@jwt_required()
def list_leases():
    rows = Lease.query.order_by(Lease.id.desc()).all()
    return jsonify([{"id":x.id,"property_id":x.property_id,"start_date":x.start_date.isoformat(),
                     "end_date":x.end_date.isoformat(),"rent":x.rent_cents} for x in rows])

@bp.post("/leases/<int:lid>/documents")
@jwt_required()
def add_doc(lid):
    if "file" not in request.files: return jsonify({"msg":"file required"}), 400
    f = request.files["file"]
    full = save_file(current_app.config["UPLOAD_ROOT"], "leases", lid, storage=f)
    rel = os.path.relpath(full, current_app.config["UPLOAD_ROOT"]).replace('\\','/')
    doc = LeaseDocument(lease_id=lid, path=rel, original_name=f.filename)
    db.session.add(doc); db.session.commit()
    return jsonify({"id": doc.id, "path": doc.path}), 201

@bp.post("/leases/<int:lid>/proration")
@jwt_required()
def proration(lid):
    d = request.get_json() or {}
    start = date.fromisoformat(d["start"])
    end = date.fromisoformat(d["end"])
    lease = Lease.query.get_or_404(lid)
    amt = prorate_monthly(lease.rent_cents, start, end)
    return jsonify({"amount_cents": amt})
