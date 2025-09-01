from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from .. import db
from ..models import Lease, Tenant, Property, Unit, RentRecord, lease_tenants
from ..security.rbac import require_role

bp = Blueprint("leases", __name__)


@bp.get("/leases")
@jwt_required()
def list_leases():
    """Get list of leases with filtering options"""
    # Query parameters
    status = request.args.get("status")
    property_id = request.args.get("property_id", type=int)
    tenant_id = request.args.get("tenant_id", type=int)
    expiring_soon = request.args.get("expiring_soon", type=int, default=0)  # days
    limit = max(1, min(int(request.args.get("limit", 50)), 200))
    offset = max(0, int(request.args.get("offset", 0)))
    
    # Build query
    query = Lease.query
    
    # Filter by status
    if status:
        query = query.filter(Lease.status == status)
    
    # Filter by property
    if property_id:
        query = query.filter(Lease.property_id == property_id)
    
    # Filter by tenant
    if tenant_id:
        query = query.join(lease_tenants).filter(lease_tenants.c.tenant_id == tenant_id)
    
    # Filter by expiring soon
    if expiring_soon > 0:
        cutoff_date = date.today() + relativedelta(days=expiring_soon)
        query = query.filter(
            and_(
                Lease.status == 'active',
                Lease.end_date <= cutoff_date,
                Lease.end_date >= date.today()
            )
        )
    
    # Get total count and paginated results
    total = query.count()
    leases = query.order_by(Lease.end_date.desc()).limit(limit).offset(offset).all()
    
    return jsonify({
        "total": total,
        "leases": [lease.serialize() for lease in leases]
    }), 200


@bp.post("/leases")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def create_lease():
    """Create a new lease"""
    data = request.get_json(silent=True) or {}
    
    # Validate required fields
    required_fields = ['property_id', 'unit_id', 'start_date', 'end_date', 'monthly_rent', 'tenant_ids']
    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({
                "error": "validation_error",
                "message": f"{field} is required"
            }), 400
    
    # Validate tenant_ids is a list with at least one tenant
    if not isinstance(data['tenant_ids'], list) or len(data['tenant_ids']) == 0:
        return jsonify({
            "error": "validation_error",
            "message": "At least one tenant is required"
        }), 400
    
    try:
        # Validate dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        if start_date >= end_date:
            return jsonify({
                "error": "validation_error",
                "message": "End date must be after start date"
            }), 400
        
        # Calculate lease term in months
        lease_term_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        
        # Validate property and unit exist
        property_obj = Property.query.get(data['property_id'])
        unit = Unit.query.get(data['unit_id'])
        
        if not property_obj or not unit:
            return jsonify({
                "error": "validation_error",
                "message": "Invalid property or unit"
            }), 400
        
        if unit.property_id != property_obj.id:
            return jsonify({
                "error": "validation_error",
                "message": "Unit does not belong to the specified property"
            }), 400
        
        # Check if unit is available
        existing_active_lease = Lease.query.filter(
            and_(
                Lease.unit_id == data['unit_id'],
                Lease.status == 'active',
                or_(
                    and_(Lease.start_date <= start_date, Lease.end_date >= start_date),
                    and_(Lease.start_date <= end_date, Lease.end_date >= end_date),
                    and_(Lease.start_date >= start_date, Lease.end_date <= end_date)
                )
            )
        ).first()
        
        if existing_active_lease:
            return jsonify({
                "error": "validation_error",
                "message": "Unit is not available for the specified dates"
            }), 400
        
        # Validate tenants exist
        tenants = Tenant.query.filter(Tenant.id.in_(data['tenant_ids'])).all()
        if len(tenants) != len(data['tenant_ids']):
            return jsonify({
                "error": "validation_error",
                "message": "One or more tenants not found"
            }), 400
        
        # Create lease
        lease = Lease(
            property_id=data['property_id'],
            unit_id=data['unit_id'],
            start_date=start_date,
            end_date=end_date,
            lease_term_months=lease_term_months,
            monthly_rent=data['monthly_rent'],
            security_deposit=data.get('security_deposit', 0),
            pet_deposit=data.get('pet_deposit', 0),
            late_fee_amount=data.get('late_fee_amount', 50),
            late_fee_grace_days=data.get('late_fee_grace_days', 5),
            lease_type=data.get('lease_type', 'fixed'),
            payment_due_day=data.get('payment_due_day', 1),
            auto_renew=data.get('auto_renew', False),
            renewal_notice_days=data.get('renewal_notice_days', 60),
            status='draft',
            notes=data.get('notes')
        )
        
        db.session.add(lease)
        db.session.flush()  # Get the lease ID
        
        # Add tenants to lease
        for tenant in tenants:
            lease.tenants.append(tenant)
        
        db.session.commit()
        
        return jsonify(lease.serialize()), 201
        
    except ValueError as e:
        return jsonify({
            "error": "validation_error",
            "message": "Invalid date format. Use YYYY-MM-DD"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "creation_failed",
            "message": str(e)
        }), 500


@bp.get("/leases/<int:lease_id>")
@jwt_required()
def get_lease(lease_id):
    """Get lease details"""
    lease = Lease.query.get_or_404(lease_id)
    
    # Get additional details
    rent_records = RentRecord.query.filter_by(lease_id=lease_id).order_by(RentRecord.due_date.desc()).limit(12).all()
    
    response = lease.serialize()
    response.update({
        'recent_rent_records': [record.serialize() for record in rent_records]
    })
    
    return jsonify(response), 200


@bp.patch("/leases/<int:lease_id>")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def update_lease(lease_id):
    """Update lease details"""
    lease = Lease.query.get_or_404(lease_id)
    data = request.get_json(silent=True) or {}
    
    try:
        # Update allowed fields (cannot change property/unit once lease is active)
        updatable_fields = [
            'monthly_rent', 'security_deposit', 'pet_deposit', 'late_fee_amount',
            'late_fee_grace_days', 'payment_due_day', 'auto_renew',
            'renewal_notice_days', 'notes'
        ]
        
        # If lease is still draft, allow changing dates and tenants
        if lease.status == 'draft':
            updatable_fields.extend(['start_date', 'end_date'])
            
            # Handle date updates
            if 'start_date' in data:
                lease.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            if 'end_date' in data:
                lease.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            
            # Recalculate lease term
            if 'start_date' in data or 'end_date' in data:
                lease.lease_term_months = (lease.end_date.year - lease.start_date.year) * 12 + \
                                        (lease.end_date.month - lease.start_date.month)
            
            # Handle tenant updates
            if 'tenant_ids' in data:
                # Clear existing tenants and add new ones
                lease.tenants.clear()
                tenants = Tenant.query.filter(Tenant.id.in_(data['tenant_ids'])).all()
                if len(tenants) != len(data['tenant_ids']):
                    return jsonify({
                        "error": "validation_error",
                        "message": "One or more tenants not found"
                    }), 400
                
                for tenant in tenants:
                    lease.tenants.append(tenant)
        
        # Update other fields
        for field in updatable_fields:
            if field in data and field not in ['start_date', 'end_date']:
                setattr(lease, field, data[field])
        
        db.session.commit()
        return jsonify(lease.serialize()), 200
        
    except ValueError as e:
        return jsonify({
            "error": "validation_error",
            "message": "Invalid date format. Use YYYY-MM-DD"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "update_failed",
            "message": str(e)
        }), 500


@bp.post("/leases/<int:lease_id>/activate")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def activate_lease(lease_id):
    """Activate a lease and generate rent records"""
    lease = Lease.query.get_or_404(lease_id)
    
    if lease.status != 'draft':
        return jsonify({
            "error": "invalid_status",
            "message": "Only draft leases can be activated"
        }), 400
    
    try:
        # Activate the lease
        lease.activate()
        lease.signed_date = date.today()
        
        # Generate rent records for the lease term
        rent_records = lease.generate_rent_records()
        
        # Update tenant move-in date if not set
        for tenant in lease.tenants:
            if not tenant.move_in_date:
                tenant.move_in_date = lease.start_date
                tenant.status = 'active'
        
        db.session.commit()
        
        return jsonify({
            "message": "Lease activated successfully",
            "lease": lease.serialize(),
            "rent_records_created": len(rent_records)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "activation_failed",
            "message": str(e)
        }), 500


@bp.post("/leases/<int:lease_id>/terminate")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def terminate_lease(lease_id):
    """Terminate a lease"""
    lease = Lease.query.get_or_404(lease_id)
    data = request.get_json(silent=True) or {}
    
    if lease.status not in ['active', 'draft']:
        return jsonify({
            "error": "invalid_status",
            "message": "Only active or draft leases can be terminated"
        }), 400
    
    try:
        termination_date = date.today()
        if data.get('termination_date'):
            termination_date = datetime.strptime(data['termination_date'], '%Y-%m-%d').date()
        
        reason = data.get('reason', 'Terminated by management')
        
        # Terminate the lease
        lease.terminate(termination_date, reason)
        
        # Update tenant move-out dates and status
        for tenant in lease.tenants:
            tenant.move_out_date = termination_date
            tenant.status = 'former'
        
        db.session.commit()
        
        return jsonify({
            "message": "Lease terminated successfully",
            "lease": lease.serialize()
        }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "validation_error",
            "message": "Invalid date format. Use YYYY-MM-DD"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "termination_failed",
            "message": str(e)
        }), 500


@bp.get("/leases/<int:lease_id>/rent-records")
@jwt_required()
def get_lease_rent_records(lease_id):
    """Get all rent records for a lease"""
    lease = Lease.query.get_or_404(lease_id)
    
    rent_records = RentRecord.query.filter_by(lease_id=lease_id)\
        .order_by(RentRecord.due_date.desc()).all()
    
    return jsonify({
        'lease_id': lease_id,
        'rent_records': [record.serialize() for record in rent_records]
    }), 200


@bp.post("/leases/<int:lease_id>/generate-rent-records")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def generate_lease_rent_records(lease_id):
    """Generate rent records for a lease"""
    lease = Lease.query.get_or_404(lease_id)
    data = request.get_json(silent=True) or {}
    
    if lease.status != 'active':
        return jsonify({
            "error": "invalid_status",
            "message": "Can only generate rent records for active leases"
        }), 400
    
    try:
        months_ahead = data.get('months_ahead', 12)
        rent_records = lease.generate_rent_records(months_ahead)
        
        return jsonify({
            "message": f"Generated {len(rent_records)} rent records",
            "rent_records": [record.serialize() for record in rent_records]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "generation_failed",
            "message": str(e)
        }), 500


@bp.get("/leases/expiring")
@jwt_required()
def get_expiring_leases():
    """Get leases expiring within specified timeframe"""
    days = request.args.get("days", type=int, default=60)
    
    cutoff_date = date.today() + relativedelta(days=days)
    
    expiring_leases = Lease.query.filter(
        and_(
            Lease.status == 'active',
            Lease.end_date <= cutoff_date,
            Lease.end_date >= date.today()
        )
    ).order_by(Lease.end_date).all()
    
    return jsonify({
        'cutoff_date': cutoff_date.isoformat(),
        'count': len(expiring_leases),
        'leases': [lease.serialize() for lease in expiring_leases]
    }), 200


@bp.get("/leases/statistics")
@jwt_required()
def get_lease_statistics():
    """Get lease statistics"""
    total_leases = Lease.query.count()
    active_leases = Lease.query.filter_by(status='active').count()
    draft_leases = Lease.query.filter_by(status='draft').count()
    terminated_leases = Lease.query.filter_by(status='terminated').count()
    expired_leases = Lease.query.filter(
        and_(Lease.status == 'active', Lease.end_date < date.today())
    ).count()
    
    # Leases expiring in next 30 days
    expiring_soon = Lease.query.filter(
        and_(
            Lease.status == 'active',
            Lease.end_date <= date.today() + relativedelta(days=30),
            Lease.end_date >= date.today()
        )
    ).count()
    
    return jsonify({
        'total_leases': total_leases,
        'active_leases': active_leases,
        'draft_leases': draft_leases,
        'terminated_leases': terminated_leases,
        'expired_leases': expired_leases,
        'expiring_in_30_days': expiring_soon
    }), 200