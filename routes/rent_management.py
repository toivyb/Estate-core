from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from decimal import Decimal
from estatecore_backend.extensions import db
from estatecore_backend.models import RentRecord, Payment

rent_mgmt_bp = Blueprint("rent_management", __name__, url_prefix="/api")

# Configuration
LATE_FEE_AMOUNT = Decimal('50.00')
LATE_FEE_DAYS = 5  # Apply late fee after 5 days overdue

# ============= RENT RECORDS MANAGEMENT =============

@rent_mgmt_bp.get("/rent")
def list_rent_records():
    """Get all rent records with optional filtering"""
    try:
        # Query parameters for filtering
        tenant_id = request.args.get('tenant_id', type=int)
        status = request.args.get('status')  # 'unpaid', 'paid', 'overdue'
        month = request.args.get('month')  # YYYY-MM format
        property_id = request.args.get('property_id', type=int)
        
        query = RentRecord.query
        
        # Apply filters
        if tenant_id:
            query = query.filter(RentRecord.tenant_id == tenant_id)
        if status:
            query = query.filter(RentRecord.status == status)
        if property_id:
            query = query.filter(RentRecord.property_id == property_id)
        if month:
            # Filter by month and year
            year, month_num = map(int, month.split('-'))
            start_date = date(year, month_num, 1)
            if month_num == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month_num + 1, 1)
            query = query.filter(RentRecord.due_date >= start_date, RentRecord.due_date < end_date)
        
        # Order by due date descending
        records = query.order_by(RentRecord.due_date.desc()).all()
        
        return jsonify({
            "rent_records": [record.serialize() for record in records],
            "count": len(records)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rent_mgmt_bp.post("/rent")
def create_rent_record():
    """Create a new rent record"""
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['tenant_id', 'property_id', 'amount', 'due_date']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Parse and validate data
        due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        amount = Decimal(str(data['amount']))
        
        # Create rent record
        rent_record = RentRecord(
            tenant_id=data['tenant_id'],
            property_id=data['property_id'],
            unit=data.get('unit', ''),
            amount=amount,
            late_fee=Decimal('0'),
            total_amount=amount,
            due_date=due_date,
            status='unpaid',
            notes=data.get('notes', ''),
            preferred_payment_method=data.get('preferred_payment_method', 'card')
        )
        
        db.session.add(rent_record)
        db.session.commit()
        
        return jsonify(rent_record.serialize()), 201
        
    except ValueError as e:
        return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rent_mgmt_bp.get("/rent/<int:rent_id>")
def get_rent_record(rent_id):
    """Get a specific rent record"""
    try:
        rent_record = RentRecord.query.get_or_404(rent_id)
        return jsonify(rent_record.serialize())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rent_mgmt_bp.put("/rent/<int:rent_id>")
def update_rent_record(rent_id):
    """Update a rent record"""
    try:
        rent_record = RentRecord.query.get_or_404(rent_id)
        data = request.get_json() or {}
        
        # Update allowed fields
        updateable_fields = ['amount', 'due_date', 'unit', 'notes', 'preferred_payment_method']
        
        for field in updateable_fields:
            if field in data:
                if field == 'due_date':
                    rent_record.due_date = datetime.strptime(data[field], '%Y-%m-%d').date()
                elif field == 'amount':
                    rent_record.amount = Decimal(str(data[field]))
                    rent_record.calculate_total_amount()
                else:
                    setattr(rent_record, field, data[field])
        
        rent_record.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(rent_record.serialize())
        
    except ValueError as e:
        return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rent_mgmt_bp.delete("/rent/<int:rent_id>")
def delete_rent_record(rent_id):
    """Delete a rent record"""
    try:
        rent_record = RentRecord.query.get_or_404(rent_id)
        
        # Check if there are payments associated
        if rent_record.payments:
            return jsonify({"error": "Cannot delete rent record with associated payments"}), 400
        
        db.session.delete(rent_record)
        db.session.commit()
        
        return jsonify({"message": "Rent record deleted successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= RENT STATUS MANAGEMENT =============

@rent_mgmt_bp.post("/rent/<int:rent_id>/mark_paid")
def mark_rent_paid(rent_id):
    """Mark rent as paid"""
    try:
        rent_record = RentRecord.query.get_or_404(rent_id)
        data = request.get_json() or {}
        
        payment_date = None
        if data.get('payment_date'):
            payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d %H:%M:%S')
        
        rent_record.mark_paid(payment_date)
        db.session.commit()
        
        return jsonify(rent_record.serialize())
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rent_mgmt_bp.post("/rent/<int:rent_id>/mark_unpaid")
def mark_rent_unpaid(rent_id):
    """Mark rent as unpaid"""
    try:
        rent_record = RentRecord.query.get_or_404(rent_id)
        
        rent_record.status = 'unpaid'
        rent_record.paid_date = None
        db.session.commit()
        
        return jsonify(rent_record.serialize())
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rent_mgmt_bp.post("/rent/<int:rent_id>/apply_late_fee")
def apply_late_fee(rent_id):
    """Apply late fee to rent record"""
    try:
        rent_record = RentRecord.query.get_or_404(rent_id)
        data = request.get_json() or {}
        
        late_fee_amount = Decimal(str(data.get('amount', LATE_FEE_AMOUNT)))
        
        if rent_record.apply_late_fee(late_fee_amount):
            db.session.commit()
            return jsonify({
                "message": "Late fee applied successfully",
                "rent_record": rent_record.serialize()
            })
        else:
            return jsonify({"error": "Late fee already applied"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= BULK OPERATIONS =============

@rent_mgmt_bp.post("/rent/bulk_create")
def bulk_create_rent_records():
    """Create multiple rent records at once"""
    try:
        data = request.get_json() or {}
        records = data.get('records', [])
        
        if not records:
            return jsonify({"error": "No records provided"}), 400
        
        created_records = []
        errors = []
        
        for i, record_data in enumerate(records):
            try:
                # Validate required fields
                required_fields = ['tenant_id', 'property_id', 'amount', 'due_date']
                for field in required_fields:
                    if field not in record_data:
                        errors.append(f"Record {i}: Missing required field: {field}")
                        continue
                
                # Parse data
                due_date = datetime.strptime(record_data['due_date'], '%Y-%m-%d').date()
                amount = Decimal(str(record_data['amount']))
                
                # Create rent record
                rent_record = RentRecord(
                    tenant_id=record_data['tenant_id'],
                    property_id=record_data['property_id'],
                    unit=record_data.get('unit', ''),
                    amount=amount,
                    late_fee=Decimal('0'),
                    total_amount=amount,
                    due_date=due_date,
                    status='unpaid',
                    notes=record_data.get('notes', ''),
                    preferred_payment_method=record_data.get('preferred_payment_method', 'card')
                )
                
                db.session.add(rent_record)
                created_records.append(rent_record)
                
            except Exception as e:
                errors.append(f"Record {i}: {str(e)}")
        
        if created_records:
            db.session.commit()
        
        return jsonify({
            "created_count": len(created_records),
            "error_count": len(errors),
            "errors": errors,
            "created_records": [record.serialize() for record in created_records]
        }), 201 if created_records else 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rent_mgmt_bp.post("/rent/apply_late_fees")
def apply_late_fees_batch():
    """Apply late fees to all overdue rent records"""
    try:
        # Find all overdue unpaid rent records
        cutoff_date = date.today() - timedelta(days=LATE_FEE_DAYS)
        
        overdue_records = RentRecord.query.filter(
            RentRecord.status == 'unpaid',
            RentRecord.due_date <= cutoff_date,
            RentRecord.late_fee_applied == False
        ).all()
        
        updated_count = 0
        for record in overdue_records:
            if record.apply_late_fee(LATE_FEE_AMOUNT):
                record.status = 'overdue'
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
        
        return jsonify({
            "message": f"Late fees applied to {updated_count} rent records",
            "updated_count": updated_count,
            "late_fee_amount": float(LATE_FEE_AMOUNT)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= ANALYTICS AND REPORTS =============

@rent_mgmt_bp.get("/rent/metrics")
def rent_metrics():
    """Get rent collection metrics"""
    try:
        month = request.args.get('month')  # YYYY-MM format
        tenant_id = request.args.get('tenant_id', type=int)
        
        query = RentRecord.query
        
        # Apply filters
        if tenant_id:
            query = query.filter(RentRecord.tenant_id == tenant_id)
        
        if month:
            year, month_num = map(int, month.split('-'))
            start_date = date(year, month_num, 1)
            if month_num == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month_num + 1, 1)
            query = query.filter(RentRecord.due_date >= start_date, RentRecord.due_date < end_date)
        
        records = query.all()
        
        # Calculate metrics
        total_rent = sum(record.amount for record in records)
        total_collected = sum(record.amount for record in records if record.status == 'paid')
        total_late_fees = sum(record.late_fee for record in records)
        
        unpaid_count = len([r for r in records if r.status == 'unpaid'])
        paid_count = len([r for r in records if r.status == 'paid'])
        overdue_count = len([r for r in records if r.status == 'overdue'])
        
        return jsonify({
            "total_rent": float(total_rent),
            "collected": float(total_collected),
            "outstanding": float(total_rent - total_collected),
            "late_fees": float(total_late_fees),
            "net": float(total_collected - total_late_fees),
            "collection_rate": float(total_collected / total_rent * 100) if total_rent > 0 else 0,
            "counts": {
                "total": len(records),
                "paid": paid_count,
                "unpaid": unpaid_count,
                "overdue": overdue_count
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= PDF RECEIPT GENERATION =============

@rent_mgmt_bp.get("/rent/<int:rent_id>/pdf")
def generate_rent_receipt_pdf(rent_id):
    """Generate PDF receipt for rent record"""
    try:
        from estatecore_backend.app.utils.generate_rent_receipt import generate_rent_receipt_pdf
        
        rent_record = RentRecord.query.get_or_404(rent_id)
        
        if rent_record.status != 'paid':
            return jsonify({"error": "Cannot generate receipt for unpaid rent"}), 400
        
        return generate_rent_receipt_pdf(rent_record)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500