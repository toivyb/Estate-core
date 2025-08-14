import os
import stripe
from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required
from .. import db
from ..models import RentInvoice, Payment

bp = Blueprint('payments', __name__)

def _require_env():
    sk = os.getenv('STRIPE_SECRET_KEY')
    if not sk:
        abort(500, description='STRIPE_SECRET_KEY not set')
    stripe.api_key = sk

@bp.post('/payments/create')
@jwt_required()
def create_payment():
    _require_env()
    d = request.get_json() or {}
    inv = RentInvoice.query.get_or_404(d['invoice_id'])

    amount = int(d.get('amount_cents') or inv.amount_cents)
    currency = d.get('currency', 'usd')
    use_ach = bool(d.get('use_ach', True))  # default to allowing ACH with cards

    # Create PaymentIntent with automatic payment methods, but prefer ACH if requested
    params = dict(
        amount=amount,
        currency=currency,
        automatic_payment_methods={'enabled': True},
        metadata={'invoice_id': str(inv.id), 'tenant_id': str(inv.tenant_id or '')},
    )

    # If ACH explicitly requested, set options to enable instant or microdeposit verification
    if use_ach:
        # If you enable Stripe Financial Connections, set verification_method='instant'
        verification = os.getenv('STRIPE_ACH_VERIFICATION', 'automatic')  # 'instant' or 'automatic'
        params['payment_method_options'] = {
            'us_bank_account': {
                'verification_method': verification
            }
        }
        # Optionally force ACH only:
        if d.get('ach_only'):
            params['payment_method_types'] = ['us_bank_account']

    intent = stripe.PaymentIntent.create(**params)

    # Track locally
    pay = Payment(
        rent_invoice_id=inv.id,
        amount_cents=amount,
        method='us_bank_account' if use_ach and d.get('ach_only') else 'card',
        status='pending',
        stripe_payment_intent_id=intent['id'],
    )
    db.session.add(pay); db.session.commit()
    return jsonify({'client_secret': intent['client_secret'], 'payment_intent_id': intent['id']})

@bp.post('/payments/webhook')
def webhook():
    _require_env()
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature', '')
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if not endpoint_secret:
        abort(500, description='STRIPE_WEBHOOK_SECRET not set')

    event = None
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    type = event['type']
    data = event['data']['object']

    if type in ('payment_intent.processing', 'payment_intent.requires_action'):
        # ACH may sit in processing for a while
        pi = data
        p = Payment.query.filter_by(stripe_payment_intent_id=pi['id']).order_by(Payment.id.desc()).first()
        if p and p.status != 'succeeded':
            p.status = 'pending'
            db.session.commit()

    if type == 'payment_intent.succeeded':
        pi = data
        p = Payment.query.filter_by(stripe_payment_intent_id=pi['id']).order_by(Payment.id.desc()).first()
        if p:
            p.status = 'succeeded'
            p.stripe_charge_id = (pi.get('latest_charge') or None)
            inv = p.invoice
            paid = sum(x.amount_cents for x in inv.payments if x.status in ('succeeded','refunded'))
            inv.status = 'paid' if paid >= inv.amount_cents else 'partial'
            db.session.commit()

    if type == 'payment_intent.payment_failed':
        pi = data
        p = Payment.query.filter_by(stripe_payment_intent_id=pi['id']).order_by(Payment.id.desc()).first()
        if p:
            p.status = 'failed'
            db.session.commit()

    if type == 'charge.refunded':
        ch = data
        p = Payment.query.filter_by(stripe_charge_id=ch['id']).first()
        if p:
            p.status = 'refunded'
            db.session.commit()

    return jsonify({'received': True})
