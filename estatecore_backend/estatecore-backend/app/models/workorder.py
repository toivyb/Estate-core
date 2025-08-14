from datetime import datetime
from .. import db
PRIORITIES = ("low","normal","high","urgent")
STATUSES = ("open","in_progress","needs_info","on_hold","completed","canceled")

class Vendor(db.Model):
    __tablename__ = 'vendor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(255))
    services = db.Column(db.String(255))

class WorkOrder(db.Model):
    __tablename__ = 'work_order'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, nullable=False)
    tenant_id = db.Column(db.Integer)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(16), nullable=False, default='normal')
    status = db.Column(db.String(16), nullable=False, default='open')
    assignee = db.Column(db.String(255))
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))
    due_date = db.Column(db.Date)
    cost_cents = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = db.relationship('Vendor')
    comments = db.relationship('WorkOrderComment', back_populates='workorder', cascade="all, delete-orphan")
    attachments = db.relationship('WorkOrderAttachment', back_populates='workorder', cascade="all, delete-orphan")

class WorkOrderComment(db.Model):
    __tablename__ = 'work_order_comment'
    id = db.Column(db.Integer, primary_key=True)
    workorder_id = db.Column(db.Integer, db.ForeignKey('work_order.id'), nullable=False)
    author_id = db.Column(db.Integer)
    body = db.Column(db.Text, nullable=False)
    visibility = db.Column(db.String(32), default="internal")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    workorder = db.relationship('WorkOrder', back_populates='comments')

class WorkOrderAttachment(db.Model):
    __tablename__ = 'work_order_attachment'
    id = db.Column(db.Integer, primary_key=True)
    workorder_id = db.Column(db.Integer, db.ForeignKey('work_order.id'), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    original_name = db.Column(db.String(255))
    size = db.Column(db.Integer)
    mime = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    workorder = db.relationship('WorkOrder', back_populates='attachments')
