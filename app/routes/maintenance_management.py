from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_, func, desc
from datetime import datetime, date
from werkzeug.utils import secure_filename
import os
from .. import db
from ..models import MaintenanceRequest, WorkOrder, MaintenancePhoto, Property, Unit, Tenant, User
from ..security.rbac import require_role

bp = Blueprint("maintenance", __name__)

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads/maintenance_photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.get("/maintenance-requests")
@jwt_required()
def list_maintenance_requests():
    """Get maintenance requests with filtering options"""
    # Query parameters
    status = request.args.get("status")
    property_id = request.args.get("property_id", type=int)
    unit_id = request.args.get("unit_id", type=int)
    tenant_id = request.args.get("tenant_id", type=int)
    category = request.args.get("category")
    priority = request.args.get("priority")
    assigned_to = request.args.get("assigned_to", type=int)
    q = request.args.get("q", "").strip()
    limit = max(1, min(int(request.args.get("limit", 50)), 200))
    offset = max(0, int(request.args.get("offset", 0)))
    
    # Build query
    query = MaintenanceRequest.query
    
    # Apply filters
    if status:
        query = query.filter(MaintenanceRequest.status == status)
    
    if property_id:
        query = query.filter(MaintenanceRequest.property_id == property_id)
    
    if unit_id:
        query = query.filter(MaintenanceRequest.unit_id == unit_id)
    
    if tenant_id:
        query = query.filter(MaintenanceRequest.tenant_id == tenant_id)
    
    if category:
        query = query.filter(MaintenanceRequest.category == category)
    
    if priority:
        query = query.filter(MaintenanceRequest.priority == priority)
    
    if assigned_to:
        query = query.filter(MaintenanceRequest.assigned_to_user_id == assigned_to)
    
    # Search in title, description, and specific location
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            MaintenanceRequest.title.ilike(like),
            MaintenanceRequest.description.ilike(like),
            MaintenanceRequest.specific_location.ilike(like)
        ))
    
    # Get total count and paginated results
    total = query.count()
    requests = query.order_by(desc(MaintenanceRequest.created_at)).limit(limit).offset(offset).all()
    
    return jsonify({
        "total": total,
        "maintenance_requests": [req.serialize() for req in requests]
    }), 200


@bp.post("/maintenance-requests")
@jwt_required()
def create_maintenance_request():
    """Create a new maintenance request"""
    data = request.get_json(silent=True) or {}
    
    # Validate required fields
    required_fields = ['title', 'category', 'property_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "error": "validation_error",
                "message": f"{field} is required"
            }), 400
    
    try:
        # Validate property and unit
        property_obj = Property.query.get(data['property_id'])
        if not property_obj:
            return jsonify({
                "error": "validation_error",
                "message": "Invalid property"
            }), 400
        
        unit = None
        if data.get('unit_id'):
            unit = Unit.query.get(data['unit_id'])
            if not unit or unit.property_id != property_obj.id:
                return jsonify({
                    "error": "validation_error",
                    "message": "Invalid unit or unit doesn't belong to property"
                }), 400
        
        # Validate tenant if provided
        tenant = None
        if data.get('tenant_id'):
            tenant = Tenant.query.get(data['tenant_id'])
            if not tenant:
                return jsonify({
                    "error": "validation_error",
                    "message": "Invalid tenant"
                }), 400
        
        # Get current user ID
        current_user_id = int(get_jwt_identity())
        
        # Create maintenance request
        maintenance_request = MaintenanceRequest(
            title=data['title'],
            description=data.get('description'),
            category=data['category'],
            priority=data.get('priority', 'medium'),
            property_id=data['property_id'],
            unit_id=data.get('unit_id'),
            specific_location=data.get('specific_location'),
            tenant_id=data.get('tenant_id'),
            requested_by_user_id=current_user_id,
            contact_phone=data.get('contact_phone'),
            status='open',
            estimated_cost=data.get('estimated_cost'),
            tenant_can_be_present=data.get('tenant_can_be_present', True),
            special_instructions=data.get('special_instructions')
        )
        
        # Set scheduling if provided
        if data.get('scheduled_date'):
            maintenance_request.scheduled_date = datetime.strptime(
                data['scheduled_date'], '%Y-%m-%d %H:%M:%S'
            )
        
        if data.get('estimated_completion'):
            maintenance_request.estimated_completion = datetime.strptime(
                data['estimated_completion'], '%Y-%m-%d %H:%M:%S'
            )
        
        db.session.add(maintenance_request)
        db.session.commit()
        
        return jsonify(maintenance_request.serialize()), 201
        
    except ValueError as e:
        return jsonify({
            "error": "validation_error",
            "message": "Invalid date format. Use YYYY-MM-DD HH:MM:SS"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "creation_failed",
            "message": str(e)
        }), 500


@bp.get("/maintenance-requests/<int:request_id>")
@jwt_required()
def get_maintenance_request(request_id):
    """Get maintenance request details"""
    maintenance_request = MaintenanceRequest.query.get_or_404(request_id)
    
    # Get related data
    work_orders = WorkOrder.query.filter_by(maintenance_request_id=request_id).all()
    photos = MaintenancePhoto.query.filter_by(maintenance_request_id=request_id).all()
    
    response = maintenance_request.serialize()
    response.update({
        'work_orders': [wo.serialize() for wo in work_orders],
        'photos': [photo.serialize() for photo in photos]
    })
    
    return jsonify(response), 200


@bp.patch("/maintenance-requests/<int:request_id>")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def update_maintenance_request(request_id):
    """Update maintenance request"""
    maintenance_request = MaintenanceRequest.query.get_or_404(request_id)
    data = request.get_json(silent=True) or {}
    
    try:
        # Update allowed fields
        updatable_fields = [
            'title', 'description', 'category', 'priority', 'specific_location',
            'contact_phone', 'estimated_cost', 'actual_cost', 'tenant_can_be_present',
            'special_instructions', 'assigned_to_vendor'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(maintenance_request, field, data[field])
        
        # Handle date fields
        if 'scheduled_date' in data and data['scheduled_date']:
            maintenance_request.scheduled_date = datetime.strptime(
                data['scheduled_date'], '%Y-%m-%d %H:%M:%S'
            )
        
        if 'estimated_completion' in data and data['estimated_completion']:
            maintenance_request.estimated_completion = datetime.strptime(
                data['estimated_completion'], '%Y-%m-%d %H:%M:%S'
            )
        
        # Handle assignment
        if 'assigned_to_user_id' in data:
            if data['assigned_to_user_id']:
                user = User.query.get(data['assigned_to_user_id'])
                if not user:
                    return jsonify({
                        "error": "validation_error",
                        "message": "Invalid user for assignment"
                    }), 400
                maintenance_request.assign_to_user(data['assigned_to_user_id'])
            else:
                maintenance_request.assigned_to_user_id = None
                maintenance_request.status = 'open'
        
        db.session.commit()
        return jsonify(maintenance_request.serialize()), 200
        
    except ValueError as e:
        return jsonify({
            "error": "validation_error",
            "message": "Invalid date format. Use YYYY-MM-DD HH:MM:SS"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "update_failed",
            "message": str(e)
        }), 500


@bp.post("/maintenance-requests/<int:request_id>/assign")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def assign_maintenance_request(request_id):
    """Assign maintenance request to a user"""
    maintenance_request = MaintenanceRequest.query.get_or_404(request_id)
    data = request.get_json(silent=True) or {}
    
    if not data.get('user_id'):
        return jsonify({
            "error": "validation_error",
            "message": "user_id is required"
        }), 400
    
    try:
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({
                "error": "validation_error",
                "message": "Invalid user"
            }), 400
        
        maintenance_request.assign_to_user(data['user_id'])
        db.session.commit()
        
        return jsonify({
            "message": "Maintenance request assigned successfully",
            "maintenance_request": maintenance_request.serialize()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "assignment_failed",
            "message": str(e)
        }), 500


@bp.post("/maintenance-requests/<int:request_id>/start")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def start_maintenance_request(request_id):
    """Mark maintenance request as in progress"""
    maintenance_request = MaintenanceRequest.query.get_or_404(request_id)
    
    if maintenance_request.status not in ['open', 'assigned']:
        return jsonify({
            "error": "invalid_status",
            "message": "Can only start open or assigned maintenance requests"
        }), 400
    
    try:
        maintenance_request.mark_in_progress()
        db.session.commit()
        
        return jsonify({
            "message": "Maintenance request started successfully",
            "maintenance_request": maintenance_request.serialize()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "start_failed",
            "message": str(e)
        }), 500


@bp.post("/maintenance-requests/<int:request_id>/complete")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def complete_maintenance_request(request_id):
    """Mark maintenance request as completed"""
    maintenance_request = MaintenanceRequest.query.get_or_404(request_id)
    data = request.get_json(silent=True) or {}
    
    if maintenance_request.status not in ['in_progress', 'assigned']:
        return jsonify({
            "error": "invalid_status",
            "message": "Can only complete in-progress or assigned maintenance requests"
        }), 400
    
    try:
        actual_cost = data.get('actual_cost')
        completion_notes = data.get('completion_notes')
        
        maintenance_request.complete(actual_cost, completion_notes)
        
        if completion_notes:
            maintenance_request.notes = completion_notes
        
        db.session.commit()
        
        return jsonify({
            "message": "Maintenance request completed successfully",
            "maintenance_request": maintenance_request.serialize()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "completion_failed",
            "message": str(e)
        }), 500


@bp.post("/maintenance-requests/<int:request_id>/photos")
@jwt_required()
def upload_maintenance_photo(request_id):
    """Upload photo for maintenance request"""
    maintenance_request = MaintenanceRequest.query.get_or_404(request_id)
    
    if 'photo' not in request.files:
        return jsonify({
            "error": "validation_error",
            "message": "No photo file provided"
        }), 400
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({
            "error": "validation_error",
            "message": "No file selected"
        }), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            "error": "validation_error",
            "message": "File type not allowed. Allowed types: png, jpg, jpeg, gif, pdf"
        }), 400
    
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{request_id}_{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file
        file.save(filepath)
        
        # Create photo record
        photo = MaintenancePhoto(
            maintenance_request_id=request_id,
            filename=filename,
            original_filename=file.filename,
            file_path=filepath,
            file_size=os.path.getsize(filepath),
            photo_type=request.form.get('photo_type', 'before'),
            description=request.form.get('description'),
            taken_by_user_id=int(get_jwt_identity())
        )
        
        db.session.add(photo)
        db.session.commit()
        
        return jsonify(photo.serialize()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "upload_failed",
            "message": str(e)
        }), 500


@bp.post("/work-orders")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def create_work_order():
    """Create a work order for a maintenance request"""
    data = request.get_json(silent=True) or {}
    
    # Validate required fields
    required_fields = ['maintenance_request_id', 'work_order_number', 'description']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "error": "validation_error",
                "message": f"{field} is required"
            }), 400
    
    try:
        # Validate maintenance request exists
        maintenance_request = MaintenanceRequest.query.get(data['maintenance_request_id'])
        if not maintenance_request:
            return jsonify({
                "error": "validation_error",
                "message": "Invalid maintenance request"
            }), 400
        
        # Check if work order number is unique
        existing_wo = WorkOrder.query.filter_by(
            work_order_number=data['work_order_number']
        ).first()
        if existing_wo:
            return jsonify({
                "error": "validation_error",
                "message": "Work order number already exists"
            }), 400
        
        # Create work order
        work_order = WorkOrder(
            maintenance_request_id=data['maintenance_request_id'],
            work_order_number=data['work_order_number'],
            description=data['description'],
            instructions=data.get('instructions'),
            assigned_to_user_id=data.get('assigned_to_user_id'),
            vendor_name=data.get('vendor_name'),
            vendor_contact=data.get('vendor_contact'),
            status='pending',
            labor_cost=data.get('labor_cost'),
            material_cost=data.get('material_cost')
        )
        
        # Calculate total cost if components provided
        if work_order.labor_cost or work_order.material_cost:
            work_order.total_cost = (work_order.labor_cost or 0) + (work_order.material_cost or 0)
        
        # Handle scheduling
        if data.get('scheduled_start'):
            work_order.scheduled_start = datetime.strptime(
                data['scheduled_start'], '%Y-%m-%d %H:%M:%S'
            )
        
        if data.get('scheduled_end'):
            work_order.scheduled_end = datetime.strptime(
                data['scheduled_end'], '%Y-%m-%d %H:%M:%S'
            )
        
        db.session.add(work_order)
        db.session.commit()
        
        return jsonify(work_order.serialize()), 201
        
    except ValueError as e:
        return jsonify({
            "error": "validation_error",
            "message": "Invalid date format. Use YYYY-MM-DD HH:MM:SS"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "creation_failed",
            "message": str(e)
        }), 500


@bp.get("/maintenance-requests/statistics")
@jwt_required()
def get_maintenance_statistics():
    """Get maintenance request statistics"""
    # Status counts
    total_requests = MaintenanceRequest.query.count()
    open_requests = MaintenanceRequest.query.filter_by(status='open').count()
    assigned_requests = MaintenanceRequest.query.filter_by(status='assigned').count()
    in_progress_requests = MaintenanceRequest.query.filter_by(status='in_progress').count()
    completed_requests = MaintenanceRequest.query.filter_by(status='completed').count()
    
    # Priority counts
    high_priority = MaintenanceRequest.query.filter_by(priority='high').count()
    emergency_requests = MaintenanceRequest.query.filter_by(priority='emergency').count()
    
    # Category breakdown
    category_counts = db.session.query(
        MaintenanceRequest.category,
        func.count(MaintenanceRequest.id)
    ).group_by(MaintenanceRequest.category).all()
    
    # Average completion time (for completed requests with actual completion time)
    completed_with_times = MaintenanceRequest.query.filter(
        and_(
            MaintenanceRequest.status == 'completed',
            MaintenanceRequest.completed_at.isnot(None)
        )
    ).all()
    
    avg_completion_days = 0
    if completed_with_times:
        total_days = sum(
            (req.completed_at - req.created_at).days 
            for req in completed_with_times
        )
        avg_completion_days = total_days / len(completed_with_times)
    
    # Cost statistics
    total_estimated_cost = db.session.query(
        func.sum(MaintenanceRequest.estimated_cost)
    ).scalar() or 0
    
    total_actual_cost = db.session.query(
        func.sum(MaintenanceRequest.actual_cost)
    ).scalar() or 0
    
    return jsonify({
        "status_breakdown": {
            "total": total_requests,
            "open": open_requests,
            "assigned": assigned_requests,
            "in_progress": in_progress_requests,
            "completed": completed_requests
        },
        "priority_breakdown": {
            "high_priority": high_priority,
            "emergency": emergency_requests
        },
        "category_breakdown": {
            category: count for category, count in category_counts
        },
        "performance": {
            "average_completion_days": round(avg_completion_days, 2),
            "total_estimated_cost": float(total_estimated_cost),
            "total_actual_cost": float(total_actual_cost)
        }
    }), 200