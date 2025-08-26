# app/routes/tenants.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from app import db
from app.models import Tenant  # assumed existing from your migrations
from app.security import roles_required  # if you have this decorator; else remove it

bp = Blueprint("tenants", __name__)

def _obj_to_dict(obj):
    from sqlalchemy.inspection import inspect
    d = {}
    for c in inspect(obj).mapper.column_attrs:
        d[c.key] = getattr(obj, c.key)
    return d

def _allowed_fields():
    candidates = ["name", "email", "phone", "unit", "property_id", "active"]
    return [f for f in candidates if hasattr(Tenant, f)]

@bp.get("/tenants")
@jwt_required()
def list_tenants():
    q = (request.args.get("q") or "").strip()
    active = request.args.get("active")
    limit = max(1, min(int(request.args.get("limit", 50)), 200))
    offset = max(0, int(request.args.get("offset", 0)))

    query = Tenant.query
    if active is not None and hasattr(Tenant, "active"):
        want = str(active).lower() in {"1", "true", "yes", "on"}
        query = query.filter(Tenant.active == want)
    if q:
        like = f"%{q}%"
        ors = []
        for col in ["name", "email", "phone", "unit"]:
            if hasattr(Tenant, col):
                ors.append(getattr(Tenant, col).ilike(like))
        if ors:
            query = query.filter(or_(*ors))

    total = query.count()
    items = query.order_by(getattr(Tenant, "id")).limit(limit).offset(offset).all()
    return jsonify({"total": total, "items": [_obj_to_dict(t) for t in items]}), 200

@bp.post("/tenants")
@jwt_required()
def create_tenant():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "invalid_payload", "hint": "name is required"}), 400

    t = Tenant()
    for f in _allowed_fields():
        if f in data:
            setattr(t, f, data[f])
    if hasattr(Tenant, "active") and getattr(t, "active", None) is None:
        t.active = True

    db.session.add(t)
    db.session.commit()
    return jsonify(_obj_to_dict(t)), 201

@bp.get("/tenants/<int:tenant_id>")
@jwt_required()
def get_tenant(tenant_id):
    t = Tenant.query.get_or_404(tenant_id)
    return jsonify(_obj_to_dict(t)), 200

@bp.patch("/tenants/<int:tenant_id>")
@jwt_required()
def update_tenant(tenant_id):
    data = request.get_json(silent=True) or {}
    t = Tenant.query.get_or_404(tenant_id)
    for f in _allowed_fields():
        if f in data:
            setattr(t, f, data[f])
    db.session.commit()
    return jsonify(_obj_to_dict(t)), 200

@bp.delete("/tenants/<int:tenant_id>")
@jwt_required()
@roles_required("admin")  # remove if you don’t use role guard
def delete_tenant(tenant_id):
    t = Tenant.query.get_or_404(tenant_id)
    if hasattr(Tenant, "active"):
        t.active = False
    else:
        db.session.delete(t)
    db.session.commit()
    return jsonify({"ok": True}), 200
