from flask import Blueprint, request, jsonify, g
from estatecore_backend.models import db, InviteToken, User, Organization, RentInvoice, Payment, Property
from datetime import datetime, timedelta
import uuid
from functools import wraps

main = Blueprint('main', __name__)

# -----------------------------
# Role-Based Access Decorator
# -----------------------------
def require_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if not user or user.role not in roles:
                return jsonify({'error': 'Unauthorized'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# -----------------------------
# Simulate Auth Middleware
# -----------------------------
@main.before_request
def load_user_from_headers():
    email = request.headers.get('X-User-Email')
    if email:
        user = User.query.filter_by(email=email).first()
        g.current_user = user if user else None
    else:
        g.current_user = None

# -----------------------------
# Step 9: Invite & Register
# -----------------------------
@main.route('/generate-test-invite', methods=['POST'])
@require_roles('super_admin')
def generate_test_invite():
    data = request.json
    email = data.get('email')
    role = data.get('role', 'tenant')
    organization_id = data.get('organization_id')

    if not all([email, role, organization_id]):
        return jsonify({'error': 'Missing required fields'}), 400

    token = str(uuid.uuid4())
    invite = InviteToken(
        email=email,
        role=role,
        token=token,
        organization_id=organization_id,
        expires_at=datetime.utcnow() + timedelta(days=1)
    )
    db.session.add(invite)
    db.session.commit()

    return jsonify({'invite_url': f'http://localhost:5000/register/{token}'}), 200


@main.route('/register/<token>', methods=['GET', 'POST'])
def register_with_token(token):
    invite = InviteToke

@main.route('/super-admin/overview', methods=['GET'])
@require_roles('super_admin')
def super_admin_overview():
    from sqlalchemy import func

    total_orgs = db.session.query(func.count(Organization.id)).scalar()
    total_users = db.session.query(func.count(User.id)).scalar()
    total_properties = db.session.query(func.count(Property.id)).scalar()
    total_due = db.session.query(func.sum(RentInvoice.amount_due)).scalar() or 0.0
    total_paid = db.session.query(func.sum(Payment.amount_paid)).scalar() or 0.0

    return jsonify({
        'total_organizations': total_orgs,
        'total_users': total_users,
        'total_properties': total_properties,
        'total_rent_due': round(total_due, 2),
        'total_rent_collected': round(total_paid, 2),
        'total_outstanding': round(total_due - total_paid, 2)
    }), 200
from io import BytesIO
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Generate PDF Rent Receipt by Invoice
@main.route('/receipt/<int:invoice_id>', methods=['GET'])
@require_roles('super_admin', 'property_manager', 'property_admin', 'tenant')
def generate_receipt(invoice_id):
    invoice = RentInvoice.query.get(invoice_id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    payments = Payment.query.filter_by(invoice_id=invoice_id).all()
    if not payments:
        return jsonify({'error': 'No payments found for this invoice'}), 404

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica", 12)

    p.drawString(50, 750, "Rent Receipt")
    p.drawString(50, 730, f"Tenant: {invoice.tenant.full_name}")
    p.drawString(50, 710, f"Property ID: {invoice.property_id}")
    p.drawString(50, 690, f"Amount Due: ${invoice.amount_due:.2f}")
    p.drawString(50, 670, f"Due Date: {invoice.due_date.strftime('%Y-%m-%d')}")

    y = 640
    for pay in payments:
        p.drawString(50, y, f"Payment: ${pay.amount_paid:.2f} on {pay.payment_date.strftime('%Y-%m-%d')} ({pay.method})")
        y -= 20

    p.drawString(50, y - 20, f"Total Paid: ${sum(p.amount_paid for p in payments):.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"receipt_{invoice_id}.pdf", mimetype='application/pdf')
@bp.route("/users")
def get_users():
    users = User.query.all()
    return jsonify([u.email for u in users])
