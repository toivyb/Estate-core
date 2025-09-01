from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from .. import db
from ..models import Property, Unit, Lease, Tenant, MaintenanceRequest
from ..security.rbac import require_role

bp = Blueprint("properties", __name__)


@bp.get("/properties")
@jwt_required()
def list_properties():
    """Get list of properties with optional filtering"""
    # Query parameters
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status")
    property_type = request.args.get("type")
    limit = max(1, min(int(request.args.get("limit", 50)), 200))
    offset = max(0, int(request.args.get("offset", 0)))
    
    # Build query
    query = Property.query
    
    # Filter by status
    if status:
        query = query.filter(Property.status == status)
    
    # Filter by property type
    if property_type:
        query = query.filter(Property.property_type == property_type)
    
    # Search in name, address, city
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Property.name.ilike(like),
            Property.address.ilike(like),
            Property.city.ilike(like)
        ))
    
    # Get total count and paginated results
    total = query.count()
    properties = query.order_by(Property.id).limit(limit).offset(offset).all()
    
    return jsonify({
        "total": total,
        "properties": [prop.serialize() for prop in properties]
    }), 200


@bp.post("/properties")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def create_property():
    """Create a new property"""
    data = request.get_json(silent=True) or {}
    
    # Validate required fields
    required_fields = ['name', 'address', 'city', 'state', 'zip_code']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "error": "validation_error",
                "message": f"{field} is required"
            }), 400
    
    try:
        # Create property
        property_obj = Property(
            name=data['name'],
            address=data['address'],
            city=data['city'],
            state=data['state'],
            zip_code=data['zip_code'],
            property_type=data.get('property_type', 'residential'),
            total_units=data.get('total_units', 1),
            bedrooms=data.get('bedrooms'),
            bathrooms=data.get('bathrooms'),
            square_feet=data.get('square_feet'),
            year_built=data.get('year_built'),
            purchase_price=data.get('purchase_price'),
            current_market_value=data.get('current_market_value'),
            monthly_mortgage=data.get('monthly_mortgage'),
            monthly_insurance=data.get('monthly_insurance'),
            monthly_taxes=data.get('monthly_taxes'),
            acquisition_date=data.get('acquisition_date'),
            notes=data.get('notes')
        )
        
        db.session.add(property_obj)
        db.session.flush()  # Get the ID
        
        # Create units if specified
        units_data = data.get('units', [])
        if not units_data and property_obj.total_units == 1:
            # Create a single default unit
            unit = Unit(
                property_id=property_obj.id,
                unit_number='1',
                bedrooms=property_obj.bedrooms,
                bathrooms=property_obj.bathrooms,
                square_feet=property_obj.square_feet,
                rent_amount=data.get('rent_amount')
            )
            db.session.add(unit)
        else:
            # Create specified units
            for unit_data in units_data:
                unit = Unit(
                    property_id=property_obj.id,
                    unit_number=unit_data['unit_number'],
                    bedrooms=unit_data.get('bedrooms'),
                    bathrooms=unit_data.get('bathrooms'),
                    square_feet=unit_data.get('square_feet'),
                    rent_amount=unit_data.get('rent_amount'),
                    status=unit_data.get('status', 'available'),
                    notes=unit_data.get('notes')
                )
                db.session.add(unit)
        
        db.session.commit()
        return jsonify(property_obj.serialize()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "creation_failed",
            "message": str(e)
        }), 500


@bp.get("/properties/<int:property_id>")
@jwt_required()
def get_property(property_id):
    """Get property details including units"""
    property_obj = Property.query.get_or_404(property_id)
    
    # Get additional details
    active_leases = Lease.query.filter_by(property_id=property_id, status='active').count()
    open_maintenance = MaintenanceRequest.query.filter_by(
        property_id=property_id, 
        status='open'
    ).count()
    
    response = property_obj.serialize()
    response.update({
        'units': [unit.serialize() for unit in property_obj.units],
        'active_leases_count': active_leases,
        'open_maintenance_count': open_maintenance
    })
    
    return jsonify(response), 200


@bp.patch("/properties/<int:property_id>")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def update_property(property_id):
    """Update property details"""
    property_obj = Property.query.get_or_404(property_id)
    data = request.get_json(silent=True) or {}
    
    try:
        # Update allowed fields
        updatable_fields = [
            'name', 'address', 'city', 'state', 'zip_code', 'property_type',
            'total_units', 'bedrooms', 'bathrooms', 'square_feet', 'year_built',
            'purchase_price', 'current_market_value', 'monthly_mortgage',
            'monthly_insurance', 'monthly_taxes', 'status', 'acquisition_date', 'notes'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(property_obj, field, data[field])
        
        db.session.commit()
        return jsonify(property_obj.serialize()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "update_failed",
            "message": str(e)
        }), 500


@bp.delete("/properties/<int:property_id>")
@jwt_required()
@require_role(['super_admin', 'admin'])
def delete_property(property_id):
    """Delete property (soft delete by setting status to inactive)"""
    property_obj = Property.query.get_or_404(property_id)
    
    # Check if property has active leases
    active_leases = Lease.query.filter_by(property_id=property_id, status='active').count()
    if active_leases > 0:
        return jsonify({
            "error": "cannot_delete",
            "message": "Cannot delete property with active leases"
        }), 400
    
    try:
        # Soft delete by setting status to inactive
        property_obj.status = 'inactive'
        
        # Also mark all units as unavailable
        for unit in property_obj.units:
            unit.status = 'unavailable'
        
        db.session.commit()
        return jsonify({"message": "Property deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "deletion_failed",
            "message": str(e)
        }), 500


@bp.get("/properties/<int:property_id>/units")
@jwt_required()
def get_property_units(property_id):
    """Get all units for a property"""
    property_obj = Property.query.get_or_404(property_id)
    
    return jsonify({
        'property_id': property_id,
        'property_name': property_obj.name,
        'units': [unit.serialize() for unit in property_obj.units]
    }), 200


@bp.post("/properties/<int:property_id>/units")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def create_unit(property_id):
    """Create a new unit for a property"""
    property_obj = Property.query.get_or_404(property_id)
    data = request.get_json(silent=True) or {}
    
    if not data.get('unit_number'):
        return jsonify({
            "error": "validation_error",
            "message": "unit_number is required"
        }), 400
    
    # Check if unit number already exists for this property
    existing_unit = Unit.query.filter_by(
        property_id=property_id,
        unit_number=data['unit_number']
    ).first()
    
    if existing_unit:
        return jsonify({
            "error": "validation_error",
            "message": "Unit number already exists for this property"
        }), 400
    
    try:
        unit = Unit(
            property_id=property_id,
            unit_number=data['unit_number'],
            bedrooms=data.get('bedrooms'),
            bathrooms=data.get('bathrooms'),
            square_feet=data.get('square_feet'),
            rent_amount=data.get('rent_amount'),
            status=data.get('status', 'available'),
            is_rentable=data.get('is_rentable', True),
            notes=data.get('notes')
        )
        
        db.session.add(unit)
        db.session.commit()
        
        return jsonify(unit.serialize()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "creation_failed",
            "message": str(e)
        }), 500


@bp.patch("/units/<int:unit_id>")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def update_unit(unit_id):
    """Update unit details"""
    unit = Unit.query.get_or_404(unit_id)
    data = request.get_json(silent=True) or {}
    
    try:
        # Update allowed fields
        updatable_fields = [
            'unit_number', 'bedrooms', 'bathrooms', 'square_feet',
            'rent_amount', 'status', 'is_rentable', 'notes'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(unit, field, data[field])
        
        db.session.commit()
        return jsonify(unit.serialize()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "update_failed",
            "message": str(e)
        }), 500


@bp.get("/properties/<int:property_id>/financial-summary")
@jwt_required()
def get_property_financial_summary(property_id):
    """Get financial summary for a property"""
    property_obj = Property.query.get_or_404(property_id)
    
    # Calculate total rent potential
    total_rent_potential = sum(unit.rent_amount or 0 for unit in property_obj.units)
    
    # Calculate occupancy rate
    occupied_units = sum(1 for unit in property_obj.units if unit.status == 'occupied')
    total_units = len(property_obj.units)
    occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
    
    # Monthly expenses
    monthly_expenses = (property_obj.monthly_mortgage or 0) + \
                      (property_obj.monthly_insurance or 0) + \
                      (property_obj.monthly_taxes or 0)
    
    # Net operating income (potential rent - expenses)
    net_operating_income = total_rent_potential - monthly_expenses
    
    return jsonify({
        'property_id': property_id,
        'property_name': property_obj.name,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'occupancy_rate': round(occupancy_rate, 2),
        'total_rent_potential': float(total_rent_potential),
        'monthly_expenses': float(monthly_expenses),
        'net_operating_income': float(net_operating_income),
        'current_market_value': float(property_obj.current_market_value or 0),
        'cap_rate': round((net_operating_income * 12 / (property_obj.current_market_value or 1)) * 100, 2) if property_obj.current_market_value else 0
    }), 200