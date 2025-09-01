# app/routes/tenants.py
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from extensions import db
from app.models import Tenant

UPLOAD_FOLDER = 'uploads/lease_documents'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

bp = Blueprint("tenants", __name__)

def _obj_to_dict(obj):
    from sqlalchemy.inspection import inspect
    d = {}
    for c in inspect(obj).mapper.column_attrs:
        value = getattr(obj, c.key)
        # Convert date objects to strings for JSON serialization
        if hasattr(value, 'isoformat'):
            d[c.key] = value.isoformat()
        # Convert Decimal objects to float for JSON serialization
        elif hasattr(value, '__float__'):
            d[c.key] = float(value)
        else:
            d[c.key] = value
    return d

def _allowed_fields():
    candidates = [
        "name", "email", "phone", "address", 
        "emergency_contact_name", "emergency_contact_phone", "emergency_contact_address",
        "lease_start_date", "lease_end_date", "lease_amount", "security_deposit", 
        "lease_document_path"
    ]
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
    # Check if it's multipart form data (for file upload)
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        data = request.form.to_dict()
        file = request.files.get('lease_document')
    else:
        data = request.get_json(silent=True) or {}
        file = None

    # Validate required fields
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "invalid_payload", "hint": "name is required"}), 400
    
    lease_start_date = data.get("lease_start_date")
    lease_end_date = data.get("lease_end_date") 
    lease_amount = data.get("lease_amount")
    security_deposit = data.get("security_deposit")
    
    if not all([lease_start_date, lease_end_date, lease_amount, security_deposit]):
        return jsonify({
            "error": "invalid_payload", 
            "hint": "lease_start_date, lease_end_date, lease_amount, and security_deposit are required"
        }), 400
    
    if not file or not allowed_file(file.filename):
        return jsonify({
            "error": "invalid_payload",
            "hint": "lease_document is required and must be a PDF, DOC, or DOCX file"
        }), 400

    # Create tenant object
    t = Tenant()
    
    # Set basic fields
    for f in _allowed_fields():
        if f in data and f != 'lease_document_path':
            value = data[f]
            # Convert date strings to date objects
            if f in ['lease_start_date', 'lease_end_date']:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        "error": "invalid_date_format", 
                        "hint": f"{f} must be in YYYY-MM-DD format"
                    }), 400
            # Convert numeric strings to appropriate types
            elif f in ['lease_amount', 'security_deposit']:
                try:
                    value = float(value)
                except ValueError:
                    return jsonify({
                        "error": "invalid_number_format",
                        "hint": f"{f} must be a valid number"
                    }), 400
            setattr(t, f, value)

    # Handle file upload
    if file and allowed_file(file.filename):
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file
        file.save(filepath)
        t.lease_document_path = filepath

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
def delete_tenant(tenant_id):
    t = Tenant.query.get_or_404(tenant_id)
    if hasattr(Tenant, "active"):
        t.active = False
    else:
        db.session.delete(t)
    db.session.commit()
    return jsonify({"ok": True}), 200

@bp.get("/tenants/<int:tenant_id>/lease-document")
@jwt_required()
def get_lease_document(tenant_id):
    t = Tenant.query.get_or_404(tenant_id)
    if not t.lease_document_path or not os.path.exists(t.lease_document_path):
        return jsonify({"error": "lease_document_not_found"}), 404
    
    return send_file(t.lease_document_path, as_attachment=True)
