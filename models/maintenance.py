from datetime import datetime
from . import db


class MaintenanceRequest(db.Model):
    __tablename__ = "maintenance_requests"

    id = db.Column(db.Integer, primary_key=True)
    
    # Request Information
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # plumbing, electrical, hvac, appliance, etc.
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, emergency
    
    # Location Information
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    specific_location = db.Column(db.String(100), nullable=True)  # kitchen, bathroom, etc.
    
    # Requestor Information
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    requested_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    
    # Status and Assignment
    status = db.Column(db.String(32), default="open")  # open, assigned, in_progress, completed, cancelled
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_to_vendor = db.Column(db.String(200), nullable=True)
    
    # Scheduling
    scheduled_date = db.Column(db.DateTime, nullable=True)
    estimated_completion = db.Column(db.DateTime, nullable=True)
    actual_completion = db.Column(db.DateTime, nullable=True)
    
    # Financial
    estimated_cost = db.Column(db.Numeric(10, 2), nullable=True)
    actual_cost = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Access Information
    tenant_can_be_present = db.Column(db.Boolean, default=True)
    special_instructions = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    work_orders = db.relationship('WorkOrder', backref='maintenance_request', lazy=True, cascade='all, delete-orphan')
    photos = db.relationship('MaintenancePhoto', backref='maintenance_request', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<MaintenanceRequest {self.id}: {self.title} - {self.status}>'

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "property_id": self.property_id,
            "unit_id": self.unit_id,
            "specific_location": self.specific_location,
            "tenant_id": self.tenant_id,
            "requested_by_user_id": self.requested_by_user_id,
            "contact_phone": self.contact_phone,
            "status": self.status,
            "assigned_to_user_id": self.assigned_to_user_id,
            "assigned_to_vendor": self.assigned_to_vendor,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "actual_completion": self.actual_completion.isoformat() if self.actual_completion else None,
            "estimated_cost": float(self.estimated_cost) if self.estimated_cost else None,
            "actual_cost": float(self.actual_cost) if self.actual_cost else None,
            "tenant_can_be_present": self.tenant_can_be_present,
            "special_instructions": self.special_instructions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "property_name": self.property.name if self.property else None,
            "unit_number": self.unit.unit_number if self.unit else None,
            "tenant_name": self.tenant.full_name if self.tenant else None
        }
    
    def assign_to_user(self, user_id):
        """Assign maintenance request to a user"""
        self.assigned_to_user_id = user_id
        self.status = 'assigned'
        
    def mark_in_progress(self):
        """Mark maintenance request as in progress"""
        self.status = 'in_progress'
        
    def complete(self, actual_cost=None, completion_notes=None):
        """Mark maintenance request as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        if actual_cost:
            self.actual_cost = actual_cost


class WorkOrder(db.Model):
    __tablename__ = 'work_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    maintenance_request_id = db.Column(db.Integer, db.ForeignKey('maintenance_requests.id'), nullable=False)
    
    # Work Order Details
    work_order_number = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    
    # Assignment and Status
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    vendor_name = db.Column(db.String(200), nullable=True)
    vendor_contact = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    
    # Scheduling and Completion
    scheduled_start = db.Column(db.DateTime, nullable=True)
    scheduled_end = db.Column(db.DateTime, nullable=True)
    actual_start = db.Column(db.DateTime, nullable=True)
    actual_end = db.Column(db.DateTime, nullable=True)
    
    # Financial
    labor_cost = db.Column(db.Numeric(10, 2), nullable=True)
    material_cost = db.Column(db.Numeric(10, 2), nullable=True)
    total_cost = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Completion Details
    completion_notes = db.Column(db.Text, nullable=True)
    warranty_info = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<WorkOrder {self.work_order_number}: {self.status}>'
    
    def serialize(self):
        return {
            'id': self.id,
            'maintenance_request_id': self.maintenance_request_id,
            'work_order_number': self.work_order_number,
            'description': self.description,
            'instructions': self.instructions,
            'assigned_to_user_id': self.assigned_to_user_id,
            'vendor_name': self.vendor_name,
            'vendor_contact': self.vendor_contact,
            'status': self.status,
            'scheduled_start': self.scheduled_start.isoformat() if self.scheduled_start else None,
            'scheduled_end': self.scheduled_end.isoformat() if self.scheduled_end else None,
            'actual_start': self.actual_start.isoformat() if self.actual_start else None,
            'actual_end': self.actual_end.isoformat() if self.actual_end else None,
            'labor_cost': float(self.labor_cost) if self.labor_cost else None,
            'material_cost': float(self.material_cost) if self.material_cost else None,
            'total_cost': float(self.total_cost) if self.total_cost else None,
            'completion_notes': self.completion_notes,
            'warranty_info': self.warranty_info,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class MaintenancePhoto(db.Model):
    __tablename__ = 'maintenance_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    maintenance_request_id = db.Column(db.Integer, db.ForeignKey('maintenance_requests.id'), nullable=False)
    
    # Photo Information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    
    # Photo Metadata
    photo_type = db.Column(db.String(20), default='before')  # before, after, during, damage, completion
    description = db.Column(db.String(500), nullable=True)
    taken_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MaintenancePhoto {self.id}: {self.filename}>'
    
    def serialize(self):
        return {
            'id': self.id,
            'maintenance_request_id': self.maintenance_request_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'photo_type': self.photo_type,
            'description': self.description,
            'taken_by_user_id': self.taken_by_user_id,
            'uploaded_at': self.uploaded_at.isoformat()
        }
