from flask import Blueprint, request, jsonify, current_app, send_file, abort
from flask_jwt_extended import jwt_required, get_jwt
from .. import db
from ..models import WorkOrder, WorkOrderComment, WorkOrderAttachment, Vendor
from ..utils.uploads import save_file
import os, datetime

bp = Blueprint('workorders', __name__)

@bp.post('/vendors')
@jwt_required()
def create_vendor():
    d = request.get_json() or {}
    v = Vendor(name=d["name"], contact=d.get("contact"), services=d.get("services"))
    db.session.add(v); db.session.commit()
    return jsonify({"id": v.id}), 201

@bp.get('/vendors')
@jwt_required()
def list_vendors():
    rows = Vendor.query.order_by(Vendor.name).all()
    return jsonify([{"id":x.id,"name":x.name,"contact":x.contact,"services":x.services} for x in rows])

@bp.post('/workorders')
@jwt_required()
def create_workorder():
    claims = get_jwt()
    d = request.get_json() or {}
    wo = WorkOrder(property_id=d["property_id"], tenant_id=d.get("tenant_id"), title=d["title"],
                   description=d.get("description"), priority=d.get("priority","normal"),
                   status="open", assignee=d.get("assignee"), vendor_id=d.get("vendor_id"),
                   due_date=(datetime.date.fromisoformat(d["due_date"]) if d.get("due_date") else None),
                   cost_cents=int(float(d.get("cost",0))*100), created_by=claims.get("sub") or claims.get("id"))
    db.session.add(wo); db.session.commit()
    return jsonify({"id": wo.id}), 201

@bp.get('/workorders')
@jwt_required()
def list_workorders():
    q = WorkOrder.query
    for key in ("status","priority","property_id","assignee"):
        val = request.args.get(key)
        if val: q = q.filter(getattr(WorkOrder, key)==val)
    rows = q.order_by(WorkOrder.id.desc()).all()
    return jsonify([{"id":x.id,"title":x.title,"status":x.status,"priority":x.priority,"assignee":x.assignee,
                     "property_id":x.property_id,"tenant_id":x.tenant_id,
                     "due_date":(x.due_date.isoformat() if x.due_date else None)} for x in rows])

@bp.get('/workorders/<int:wo_id>')
@jwt_required()
def get_workorder(wo_id):
    x = WorkOrder.query.get_or_404(wo_id)
    return jsonify({"id":x.id,"title":x.title,"description":x.description,"status":x.status,"priority":x.priority,
                    "assignee":x.assignee,"vendor_id":x.vendor_id,"property_id":x.property_id,"tenant_id":x.tenant_id,
                    "due_date":(x.due_date.isoformat() if x.due_date else None),"cost_cents":x.cost_cents,
                    "comments":[{"id":c.id,"body":c.body,"visibility":c.visibility,"created_at":c.created_at.isoformat()} for c in x.comments],
                    "attachments":[{"id":a.id,"name":a.original_name,"size":a.size,"mime":a.mime} for a in x.attachments]})

@bp.patch('/workorders/<int:wo_id>')
@jwt_required()
def patch_workorder(wo_id):
    x = WorkOrder.query.get_or_404(wo_id)
    d = request.get_json() or {}
    for k in ["title","description","priority","status","assignee","vendor_id"]:
        if k in d: setattr(x, k, d[k])
    if "due_date" in d:
        x.due_date = (datetime.date.fromisoformat(d["due_date"]) if d["due_date"] else None)
    if "cost" in d:
        x.cost_cents = int(float(d["cost"])*100)
    db.session.commit(); return jsonify({"ok": True})

@bp.post('/workorders/<int:wo_id>/comments')
@jwt_required()
def add_comment(wo_id):
    claims = get_jwt()
    x = WorkOrder.query.get_or_404(wo_id)
    d = request.get_json() or {}
    c = WorkOrderComment(workorder_id=x.id, author_id=claims.get("sub") or claims.get("id"),
                         body=d["body"], visibility=d.get("visibility","internal"))
    db.session.add(c); db.session.commit()
    return jsonify({"id": c.id}), 201

@bp.post('/workorders/<int:wo_id>/attachments')
@jwt_required()
def add_attachment(wo_id):
    x = WorkOrder.query.get_or_404(wo_id)
    if "file" not in request.files: return jsonify({"msg":"file required"}), 400
    f = request.files["file"]
    full = save_file(current_app.config["UPLOAD_ROOT"], "workorders", x.id, storage=f)
    rel = os.path.relpath(full, current_app.config["UPLOAD_ROOT"]).replace('\\','/')
    from ..models import WorkOrderAttachment
    a = WorkOrderAttachment(workorder_id=x.id, path=rel, original_name=f.filename, size=os.path.getsize(full), mime=f.mimetype)
    db.session.add(a); db.session.commit()
    return jsonify({"id": a.id, "path": a.path}), 201
