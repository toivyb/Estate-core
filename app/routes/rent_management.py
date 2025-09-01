from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from .. import db
from ..models import RentRecord, Lease, Tenant, Property, Unit, Payment
from ..security.rbac import require_role

bp = Blueprint("rent", __name__)


@bp.get("/rent-records")
@jwt_required()
def list_rent_records():
    """Get rent records with filtering options"""
    # Query parameters
    status = request.args.get("status")
    tenant_id = request.args.get("tenant_id", type=int)
    property_id = request.args.get("property_id", type=int)
    overdue_only = request.args.get("overdue_only", default=False, type=bool)
    month = request.args.get("month")  # Format: YYYY-MM
    limit = max(1, min(int(request.args.get("limit", 50)), 200))
    offset = max(0, int(request.args.get("offset", 0)))
    
    # Build query
    query = RentRecord.query
    
    # Filter by status
    if status:
        query = query.filter(RentRecord.status == status)
    
    # Filter by tenant
    if tenant_id:
        query = query.filter(RentRecord.tenant_id == tenant_id)
    
    # Filter by property
    if property_id:
        query = query.filter(RentRecord.property_id == property_id)
    
    # Filter by overdue
    if overdue_only:
        query = query.filter(
            and_(
                RentRecord.status == 'unpaid',
                RentRecord.due_date < date.today()
            )
        )
    
    # Filter by month
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            start_date = date(year, month_num, 1)
            if month_num == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month_num + 1, 1)
            
            query = query.filter(
                and_(
                    RentRecord.period_start >= start_date,
                    RentRecord.period_start < end_date
                )
            )
        except ValueError:
            return jsonify({
                "error": "validation_error",
                "message": "Invalid month format. Use YYYY-MM"
            }), 400
    
    # Get total count and paginated results
    total = query.count()
    rent_records = query.order_by(desc(RentRecord.due_date)).limit(limit).offset(offset).all()
    
    # Calculate totals
    total_amount = query.with_entities(func.sum(RentRecord.total_amount)).scalar() or 0
    total_paid = query.with_entities(func.sum(RentRecord.amount_paid)).scalar() or 0
    total_outstanding = query.with_entities(func.sum(RentRecord.amount_outstanding)).scalar() or 0
    
    return jsonify({
        "total": total,
        "total_amount": float(total_amount),
        "total_paid": float(total_paid),
        "total_outstanding": float(total_outstanding),
        "rent_records": [record.serialize() for record in rent_records]
    }), 200


@bp.post("/rent-records")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def create_rent_record():
    """Create a manual rent record"""
    data = request.get_json(silent=True) or {}
    
    # Validate required fields
    required_fields = ['lease_id', 'tenant_id', 'amount', 'due_date', 'period_start', 'period_end']
    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({
                "error": "validation_error",
                "message": f"{field} is required"
            }), 400
    
    try:
        # Validate dates
        due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        period_start = datetime.strptime(data['period_start'], '%Y-%m-%d').date()
        period_end = datetime.strptime(data['period_end'], '%Y-%m-%d').date()
        
        if period_start >= period_end:
            return jsonify({
                "error": "validation_error",
                "message": "Period end must be after period start"
            }), 400
        
        # Validate lease and tenant
        lease = Lease.query.get(data['lease_id'])
        tenant = Tenant.query.get(data['tenant_id'])
        
        if not lease or not tenant:
            return jsonify({
                "error": "validation_error",
                "message": "Invalid lease or tenant"
            }), 400
        
        # Check if tenant is on the lease
        if tenant not in lease.tenants:
            return jsonify({
                "error": "validation_error",
                "message": "Tenant is not on the specified lease"
            }), 400
        
        # Check for duplicate rent record
        existing_record = RentRecord.query.filter(
            and_(
                RentRecord.lease_id == data['lease_id'],
                RentRecord.period_start == period_start,
                RentRecord.period_end == period_end
            )
        ).first()
        
        if existing_record:
            return jsonify({
                "error": "validation_error",
                "message": "Rent record already exists for this period"
            }), 400
        
        # Calculate amounts
        amount = Decimal(str(data['amount']))
        late_fee = Decimal(str(data.get('late_fee', 0)))
        other_fees = Decimal(str(data.get('other_fees', 0)))
        total_amount = amount + late_fee + other_fees
        
        # Create rent record
        rent_record = RentRecord(
            lease_id=data['lease_id'],
            tenant_id=data['tenant_id'],
            property_id=lease.property_id,
            unit_id=lease.unit_id,
            amount=amount,
            late_fee=late_fee,
            other_fees=other_fees,
            total_amount=total_amount,
            amount_paid=Decimal('0'),
            amount_outstanding=total_amount,
            period_start=period_start,
            period_end=period_end,
            due_date=due_date,
            status='unpaid',
            preferred_payment_method=data.get('preferred_payment_method', 'card'),
            notes=data.get('notes')
        )
        
        db.session.add(rent_record)
        db.session.commit()
        
        return jsonify(rent_record.serialize()), 201
        
    except ValueError as e:
        return jsonify({
            "error": "validation_error",
            "message": "Invalid date or number format"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "creation_failed",
            "message": str(e)
        }), 500


@bp.get("/rent-records/<int:record_id>")
@jwt_required()
def get_rent_record(record_id):
    """Get rent record details with payment history"""
    rent_record = RentRecord.query.get_or_404(record_id)
    
    # Get payment history
    payments = Payment.query.filter_by(rent_record_id=record_id)\
        .order_by(desc(Payment.created_at)).all()
    
    response = rent_record.serialize()
    response['payments'] = [payment.serialize() for payment in payments]
    
    return jsonify(response), 200


@bp.patch("/rent-records/<int:record_id>")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def update_rent_record(record_id):
    """Update rent record"""
    rent_record = RentRecord.query.get_or_404(record_id)
    data = request.get_json(silent=True) or {}
    
    try:
        # Update allowed fields
        if 'amount' in data:
            rent_record.amount = Decimal(str(data['amount']))
        
        if 'late_fee' in data:
            rent_record.late_fee = Decimal(str(data['late_fee']))
            rent_record.late_fee_applied = rent_record.late_fee > 0
        
        if 'other_fees' in data:
            rent_record.other_fees = Decimal(str(data['other_fees']))
        
        # Recalculate totals if amounts changed
        if any(field in data for field in ['amount', 'late_fee', 'other_fees']):
            rent_record.total_amount = rent_record.amount + rent_record.late_fee + rent_record.other_fees
            rent_record.amount_outstanding = rent_record.total_amount - rent_record.amount_paid
        
        if 'due_date' in data:
            rent_record.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        
        if 'notes' in data:
            rent_record.notes = data['notes']
        
        if 'preferred_payment_method' in data:
            rent_record.preferred_payment_method = data['preferred_payment_method']
        
        db.session.commit()
        return jsonify(rent_record.serialize()), 200
        
    except ValueError as e:
        return jsonify({
            "error": "validation_error",
            "message": "Invalid date or number format"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "update_failed",
            "message": str(e)
        }), 500


@bp.post("/rent-records/<int:record_id>/apply-late-fee")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def apply_late_fee(record_id):
    """Apply late fee to a rent record"""
    rent_record = RentRecord.query.get_or_404(record_id)
    data = request.get_json(silent=True) or {}
    
    if rent_record.status == 'paid':
        return jsonify({
            "error": "invalid_status",
            "message": "Cannot apply late fee to paid rent record"
        }), 400
    
    if rent_record.late_fee_applied:
        return jsonify({
            "error": "already_applied",
            "message": "Late fee has already been applied"
        }), 400
    
    try:
        # Use provided late fee amount or get from lease
        late_fee_amount = data.get('late_fee_amount')
        if late_fee_amount is None:
            lease = Lease.query.get(rent_record.lease_id)
            late_fee_amount = lease.late_fee_amount if lease else 50
        
        # Apply late fee
        success = rent_record.apply_late_fee(Decimal(str(late_fee_amount)))
        
        if success:
            db.session.commit()
            return jsonify({
                "message": "Late fee applied successfully",
                "rent_record": rent_record.serialize()
            }), 200
        else:
            return jsonify({
                "error": "already_applied",
                "message": "Late fee has already been applied"
            }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "application_failed",
            "message": str(e)
        }), 500


@bp.post("/rent-records/<int:record_id>/mark-paid")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def mark_rent_paid(record_id):
    """Mark rent record as paid (manual payment)"""
    rent_record = RentRecord.query.get_or_404(record_id)
    data = request.get_json(silent=True) or {}
    
    if rent_record.status == 'paid':
        return jsonify({
            "error": "already_paid",
            "message": "Rent record is already marked as paid"
        }), 400
    
    try:
        payment_date = datetime.utcnow()
        if data.get('payment_date'):
            payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d %H:%M:%S')
        
        amount_paid = data.get('amount_paid', rent_record.total_amount)
        
        # Update rent record
        rent_record.amount_paid = Decimal(str(amount_paid))
        rent_record.amount_outstanding = rent_record.total_amount - rent_record.amount_paid
        
        if rent_record.amount_outstanding <= 0:
            rent_record.status = 'paid'
            rent_record.paid_date = payment_date
        elif rent_record.amount_paid > 0:
            rent_record.status = 'partial'
        
        # Create payment record if requested
        if data.get('create_payment_record', True):
            payment = Payment(
                rent_record_id=record_id,
                tenant_id=rent_record.tenant_id,
                amount=amount_paid,
                payment_method=data.get('payment_method', 'cash'),
                status='completed',
                completed_at=payment_date,
                description=data.get('description', 'Manual payment entry'),
                notes=data.get('notes')
            )
            db.session.add(payment)
        
        db.session.commit()
        
        return jsonify({
            "message": "Rent record updated successfully",
            "rent_record": rent_record.serialize()
        }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "validation_error",
            "message": "Invalid date or number format"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "update_failed",
            "message": str(e)
        }), 500


@bp.get("/rent-records/overdue")
@jwt_required()
def get_overdue_rent():
    """Get overdue rent records"""
    days_overdue = request.args.get("days_overdue", type=int)
    
    query = RentRecord.query.filter(
        and_(
            RentRecord.status.in_(['unpaid', 'partial']),
            RentRecord.due_date < date.today()
        )
    )
    
    if days_overdue:
        cutoff_date = date.today() - relativedelta(days=days_overdue)
        query = query.filter(RentRecord.due_date <= cutoff_date)
    
    overdue_records = query.order_by(RentRecord.due_date).all()
    
    # Calculate totals
    total_overdue_amount = sum(record.amount_outstanding for record in overdue_records)
    
    return jsonify({
        "count": len(overdue_records),
        "total_overdue_amount": float(total_overdue_amount),
        "overdue_records": [record.serialize() for record in overdue_records]
    }), 200


@bp.post("/rent-records/bulk-generate")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def bulk_generate_rent_records():
    """Generate rent records for all active leases"""
    data = request.get_json(silent=True) or {}
    
    months_ahead = data.get('months_ahead', 1)
    property_id = data.get('property_id')  # Optional: only for specific property
    
    try:
        # Get active leases
        query = Lease.query.filter_by(status='active')
        if property_id:
            query = query.filter_by(property_id=property_id)
        
        active_leases = query.all()
        
        total_created = 0
        created_by_lease = {}
        
        for lease in active_leases:
            try:
                records_created = lease.generate_rent_records(months_ahead)
                total_created += len(records_created)
                created_by_lease[lease.id] = len(records_created)
            except Exception as e:
                # Log error but continue with other leases
                created_by_lease[lease.id] = f"Error: {str(e)}"
        
        db.session.commit()
        
        return jsonify({
            "message": f"Generated {total_created} rent records",
            "total_created": total_created,
            "leases_processed": len(active_leases),
            "created_by_lease": created_by_lease
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "generation_failed",
            "message": str(e)
        }), 500


@bp.get("/rent-records/statistics")
@jwt_required()
def get_rent_statistics():
    """Get rent collection statistics"""
    # Current month statistics
    today = date.today()
    current_month_start = today.replace(day=1)
    next_month_start = (current_month_start + relativedelta(months=1))
    
    current_month_records = RentRecord.query.filter(
        and_(
            RentRecord.period_start >= current_month_start,
            RentRecord.period_start < next_month_start
        )
    )
    
    total_expected = current_month_records.with_entities(func.sum(RentRecord.total_amount)).scalar() or 0
    total_collected = current_month_records.with_entities(func.sum(RentRecord.amount_paid)).scalar() or 0
    
    # Overall statistics
    total_rent_records = RentRecord.query.count()
    paid_records = RentRecord.query.filter_by(status='paid').count()
    unpaid_records = RentRecord.query.filter_by(status='unpaid').count()
    partial_records = RentRecord.query.filter_by(status='partial').count()
    
    # Overdue statistics
    overdue_records = RentRecord.query.filter(
        and_(
            RentRecord.status.in_(['unpaid', 'partial']),
            RentRecord.due_date < today
        )
    )
    overdue_count = overdue_records.count()
    overdue_amount = overdue_records.with_entities(func.sum(RentRecord.amount_outstanding)).scalar() or 0
    
    # Collection rate
    collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else 0
    
    return jsonify({
        "current_month": {
            "expected_amount": float(total_expected),
            "collected_amount": float(total_collected),
            "collection_rate": round(collection_rate, 2),
            "outstanding_amount": float(total_expected - total_collected)
        },
        "overall": {
            "total_records": total_rent_records,
            "paid_records": paid_records,
            "unpaid_records": unpaid_records,
            "partial_records": partial_records
        },
        "overdue": {
            "count": overdue_count,
            "amount": float(overdue_amount)
        }
    }), 200