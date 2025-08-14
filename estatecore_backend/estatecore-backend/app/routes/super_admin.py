from flask import Blueprint, request, session
from .. import db
from ..models import User, Property, PropertyManager, Tenant

super_admin_bp = Blueprint("super_admin", __name__)

def require_super_admin():
    if session.get("role") != "super_admin":
        return {"error": "forbidden"}, 403
    return None

@super_admin_bp.post("/bootstrap")
def bootstrap_super_admin():
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    exists = User.query.filter_by(role="super_admin").first()
    if exists:
        return {"error": "super_admin_exists"}, 400
    if not email or not password:
        return {"error": "email_and_password_required"}, 400
    u = User(email=email, role="super_admin")
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return {"id": u.id, "email": u.email, "role": u.role}

@super_admin_bp.post("/properties")
def create_property():
    guard = require_super_admin()
    if guard: return guard
    data = request.get_json(force=True)
    name = data.get("name")
    address = data.get("address")
    if not name:
        return {"error": "name_required"}, 400
    p = Property(name=name, address=address or "")
    db.session.add(p)
    db.session.commit()
    return {"id": p.id, "name": p.name, "address": p.address}

@super_admin_bp.get("/properties")
def list_properties():
    guard = require_super_admin()
    if guard: return guard
    props = Property.query.all()
    return {"items": [{"id": p.id, "name": p.name, "address": p.address} for p in props]}

@super_admin_bp.post("/managers")
def create_manager():
    guard = require_super_admin()
    if guard: return guard
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    property_id = data.get("property_id")
    if not all([email, password, property_id]):
        return {"error": "email_password_property_id_required"}, 400
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, role="manager")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
    else:
        user.role = "manager"
        if password:
            user.set_password(password)
    pm = PropertyManager(user_id=user.id, property_id=property_id)
    db.session.add(pm)
    db.session.commit()
    return {"id": user.id, "email": user.email, "role": user.role, "property_id": property_id}

@super_admin_bp.post("/tenants")
def create_tenant():
    guard = require_super_admin()
    if guard: return guard
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    property_id = data.get("property_id")
    unit = data.get("unit", "")
    if not all([email, password, property_id]):
        return {"error": "email_password_property_id_required"}, 400
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, role="tenant")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
    else:
        user.role = "tenant"
        if password:
            user.set_password(password)
    t = Tenant(user_id=user.id, property_id=property_id, unit=unit)
    db.session.add(t)
    db.session.commit()
    return {"id": user.id, "email": user.email, "role": user.role, "property_id": property_id, "unit": unit}