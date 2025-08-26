from flask import Blueprint, request, jsonify
from datetime import datetime, date
from decimal import Decimal
import os
import stripe
from estatecore_backend.extensions import db
from estatecore_backend.models import RentRecord, Payment

payment_mgmt_bp = Blueprint("payment_management", __name__, url_prefix="/api")

# Initialize Stripe if configured
def init_stripe():
    stripe_key = os.environ.get('STRIPE_SECRET_KEY')
    if stripe_key:
        stripe.api_key = stripe_key
        return True
    return False

# ============= PAYMENT MANAGEMENT =============

@payment_mgmt_bp.get("/payments")
def list_payments():
    """Get all payments with optional filtering"""
    try:
        # Query parameters for filtering
        tenant_id = request.args.get('tenant_id', type=int)
        status = request.args.get('status')
        payment_method = request.args.get('payment_method')
        rent_record_id = request.args.get('rent_record_id', type=int)
        
        query = Payment.query
        
        # Apply filters
        if tenant_id:
            query = query.filter(Payment.tenant_id == tenant_id)
        if status:
            query = query.filter(Payment.status == status)
        if payment_method:
            query = query.filter(Payment.payment_method == payment_method)
        if rent_record_id:
            query = query.filter(Payment.rent_record_id == rent_record_id)
        
        # Order by created date descending
        payments = query.order_by(Payment.created_at.desc()).all()
        
        return jsonify({
            "payments": [payment.serialize() for payment in payments],
            "count": len(payments)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@payment_mgmt_bp.post("/payments")
def create_payment():
    """Create a new payment record"""
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['tenant_id', 'amount', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        amount = Decimal(str(data['amount']))
        
        # Create payment record
        payment = Payment(
            tenant_id=data['tenant_id'],
            rent_record_id=data.get('rent_record_id'),
            amount=amount,
            payment_method=data['payment_method'],
            status='pending',
            description=data.get('description', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify(payment.serialize()), 201
        
    except ValueError as e:
        return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@payment_mgmt_bp.get("/payments/<int:payment_id>")
def get_payment(payment_id):
    """Get a specific payment"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        return jsonify(payment.serialize())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@payment_mgmt_bp.put("/payments/<int:payment_id>")
def update_payment(payment_id):
    """Update a payment record"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        data = request.get_json() or {}
        
        # Update allowed fields
        updateable_fields = ['amount', 'description', 'notes', 'status']
        
        for field in updateable_fields:
            if field in data:
                if field == 'amount':
                    payment.amount = Decimal(str(data[field]))
                else:
                    setattr(payment, field, data[field])
        
        db.session.commit()
        
        return jsonify(payment.serialize())
        
    except ValueError as e:
        return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@payment_mgmt_bp.delete("/payments/<int:payment_id>")
def delete_payment(payment_id):
    """Delete a payment record"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        # Only allow deletion of pending/failed payments
        if payment.status in ['completed', 'refunded']:
            return jsonify({"error": "Cannot delete completed or refunded payments"}), 400
        
        db.session.delete(payment)
        db.session.commit()
        
        return jsonify({"message": "Payment deleted successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= STRIPE INTEGRATION =============

@payment_mgmt_bp.post("/payments/create_intent")
def create_payment_intent():
    """Create a Stripe PaymentIntent for rent payment"""
    try:
        if not init_stripe():
            return jsonify({"error": "Stripe not configured"}), 500
        
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['tenant_id', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        amount_cents = int(Decimal(str(data['amount'])) * 100)  # Convert to cents
        rent_record_id = data.get('rent_record_id')
        
        # Get rent record if specified
        rent_record = None
        if rent_record_id:
            rent_record = RentRecord.query.get(rent_record_id)
            if not rent_record:
                return jsonify({"error": "Rent record not found"}), 404
        
        # Create PaymentIntent
        intent_params = {
            'amount': amount_cents,
            'currency': 'usd',
            'automatic_payment_methods': {'enabled': True},
            'metadata': {
                'tenant_id': str(data['tenant_id']),
                'rent_record_id': str(rent_record_id) if rent_record_id else '',
                'description': data.get('description', 'Rent Payment')
            }
        }
        
        # Add ACH options if requested
        if data.get('enable_ach', True):
            intent_params['payment_method_options'] = {
                'us_bank_account': {
                    'verification_method': os.environ.get('STRIPE_ACH_VERIFICATION', 'automatic')
                }
            }
        
        intent = stripe.PaymentIntent.create(**intent_params)
        
        # Create local payment record
        payment = Payment(
            tenant_id=data['tenant_id'],
            rent_record_id=rent_record_id,
            amount=Decimal(str(data['amount'])),
            payment_method='card',  # Will be updated when payment completes
            status='pending',
            stripe_payment_intent_id=intent['id'],
            description=data.get('description', 'Rent Payment')
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'client_secret': intent['client_secret'],
            'payment_intent_id': intent['id'],
            'payment_id': payment.id
        })
        
    except stripe.error.StripeError as e:
        return jsonify({"error": f"Stripe error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@payment_mgmt_bp.post("/payments/webhook")
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        if not init_stripe():
            return jsonify({"error": "Stripe not configured"}), 500
        
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature', '')
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        if not endpoint_secret:
            return jsonify({"error": "Webhook secret not configured"}), 500
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except stripe.error.SignatureVerificationError:
            return jsonify({"error": "Invalid signature"}), 400
        
        # Handle the event
        event_type = event['type']
        data = event['data']['object']
        
        if event_type == 'payment_intent.succeeded':
            # Payment successful
            payment_intent_id = data['id']
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if payment:
                payment.mark_completed()
                payment.stripe_charge_id = data.get('latest_charge')
                
                # Update payment method based on actual payment
                if data.get('payment_method'):
                    pm = stripe.PaymentMethod.retrieve(data['payment_method'])
                    payment.payment_method = pm.type
                
                db.session.commit()
        
        elif event_type == 'payment_intent.payment_failed':
            # Payment failed
            payment_intent_id = data['id']
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if payment:
                failure_reason = data.get('last_payment_error', {}).get('message', 'Unknown error')
                payment.mark_failed(failure_reason)
                db.session.commit()
        
        elif event_type in ['payment_intent.processing', 'payment_intent.requires_action']:
            # Payment is processing (common with ACH)
            payment_intent_id = data['id']
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if payment and payment.status == 'pending':
                payment.status = 'processing'
                db.session.commit()
        
        return jsonify({'received': True})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= PAYMENT HISTORY AND ANALYTICS =============

@payment_mgmt_bp.get("/payments/tenant/<int:tenant_id>")
def get_tenant_payments(tenant_id):
    """Get payment history for a specific tenant"""
    try:
        payments = Payment.query.filter_by(tenant_id=tenant_id).order_by(
            Payment.created_at.desc()
        ).all()
        
        # Calculate summary stats
        total_paid = sum(p.amount for p in payments if p.status == 'completed')
        pending_amount = sum(p.amount for p in payments if p.status in ['pending', 'processing'])
        
        return jsonify({
            "payments": [payment.serialize() for payment in payments],
            "summary": {
                "total_payments": len(payments),
                "total_paid": float(total_paid),
                "pending_amount": float(pending_amount),
                "last_payment": payments[0].created_at.isoformat() if payments else None
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@payment_mgmt_bp.get("/payments/metrics")
def payment_metrics():
    """Get payment analytics and metrics"""
    try:
        # Date range filter
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Payment.query
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Payment.created_at >= start)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Payment.created_at <= end)
        
        payments = query.all()
        
        # Calculate metrics
        total_amount = sum(p.amount for p in payments)
        completed_amount = sum(p.amount for p in payments if p.status == 'completed')
        pending_amount = sum(p.amount for p in payments if p.status in ['pending', 'processing'])
        failed_amount = sum(p.amount for p in payments if p.status == 'failed')
        
        # Payment method breakdown
        payment_methods = {}
        for payment in payments:
            method = payment.payment_method
            if method not in payment_methods:
                payment_methods[method] = {'count': 0, 'amount': 0}
            payment_methods[method]['count'] += 1
            payment_methods[method]['amount'] += float(payment.amount)
        
        # Status breakdown
        status_counts = {}
        for payment in payments:
            status = payment.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return jsonify({
            "total_amount": float(total_amount),
            "completed_amount": float(completed_amount),
            "pending_amount": float(pending_amount),
            "failed_amount": float(failed_amount),
            "success_rate": float(completed_amount / total_amount * 100) if total_amount > 0 else 0,
            "payment_methods": payment_methods,
            "status_counts": status_counts,
            "total_payments": len(payments)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= MANUAL PAYMENT PROCESSING =============

@payment_mgmt_bp.post("/payments/<int:payment_id>/mark_completed")
def mark_payment_completed(payment_id):
    """Manually mark payment as completed (for cash/check payments)"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        data = request.get_json() or {}
        
        if payment.status == 'completed':
            return jsonify({"error": "Payment already completed"}), 400
        
        # Mark as completed
        payment.mark_completed()
        
        # Add transaction details if provided
        if data.get('transaction_id'):
            payment.transaction_id = data['transaction_id']
        if data.get('notes'):
            payment.notes = data['notes']
        
        db.session.commit()
        
        return jsonify(payment.serialize())
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@payment_mgmt_bp.post("/payments/<int:payment_id>/refund")
def refund_payment(payment_id):
    """Process a payment refund"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        if payment.status != 'completed':
            return jsonify({"error": "Can only refund completed payments"}), 400
        
        # If it's a Stripe payment, process refund through Stripe
        if payment.stripe_charge_id and init_stripe():
            try:
                refund = stripe.Refund.create(charge=payment.stripe_charge_id)
                payment.status = 'refunded'
                payment.notes = f"Refunded via Stripe: {refund['id']}"
            except stripe.error.StripeError as e:
                return jsonify({"error": f"Stripe refund failed: {str(e)}"}), 400
        else:
            # Manual refund
            payment.status = 'refunded'
            payment.notes = "Manually refunded"
        
        # If payment was linked to rent record, update rent status
        if payment.rent_record:
            # Check if there are other completed payments for this rent
            other_payments = Payment.query.filter(
                Payment.rent_record_id == payment.rent_record_id,
                Payment.status == 'completed',
                Payment.id != payment.id
            ).all()
            
            if not other_payments:
                payment.rent_record.status = 'unpaid'
                payment.rent_record.paid_date = None
        
        db.session.commit()
        
        return jsonify(payment.serialize())
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500