from flask import Blueprint, request, jsonify, send_file
from estatecore_backend.models.rent import Rent
from estatecore_backend.models.payment import Payment
from estatecore_backend.models.maintenance import MaintenanceRequest
from estatecore_backend.models import db
import csv, io
from datetime import datetime

reporting_bp = Blueprint('reporting', __name__)

@reporting_bp.route('/api/reports/summary', methods=['GET'])
def summary_report():
    month = request.args.get('month')
    property_id = request.args.get('property_id')
    query = Rent.query
    if month:
        dt = datetime.strptime(month, '%Y-%m')
        query = query.filter(Rent.due_date >= dt, Rent.due_date < dt.replace(day=28) + timedelta(days=4))
    if property_id:
        query = query.filter_by(property_id=property_id)
    rents = query.all()
    total_due = sum(r.amount for r in rents)
    total_paid = sum(r.amount for r in rents if r.status == 'paid')
    total_unpaid = total_due - total_paid
    # Payments
    payments = Payment.query.filter(Payment.timestamp >= dt, Payment.timestamp < dt.replace(day=28) + timedelta(days=4)) if month else Payment.query
    total_payments = sum(p.amount for p in payments)
    # Maintenance
    open_maint = MaintenanceRequest.query.filter_by(status='open').count()
    closed_maint = MaintenanceRequest.query.filter_by(status='closed').count()
    return jsonify({
        "total_due": total_due,
        "total_paid": total_paid,
        "total_unpaid": total_unpaid,
        "total_payments": total_payments,
        "open_maintenance": open_maint,
        "closed_maintenance": closed_maint
    })

@reporting_bp.route('/api/reports/rent_csv', methods=['GET'])
def rent_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','Tenant','Property','Amount','Due','Paid','Status','Late Fee'])
    for r in Rent.query.all():
        writer.writerow([r.id, r.tenant_id, r.property_id, r.amount, r.due_date, r.paid_on, r.status, r.late_fee])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='rent_report.csv')

@reporting_bp.route('/api/reports/payments_csv', methods=['GET'])
def payments_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','Tenant','Rent','Amount','Status','Timestamp'])
    for p in Payment.query.all():
        writer.writerow([p.id, p.tenant_id, p.rent_id, p.amount, p.status, p.timestamp])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='payment_report.csv')

@reporting_bp.route('/api/reports/maintenance_csv', methods=['GET'])
def maint_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','Property','Tenant','Description','Status','Assigned To','Created','Updated','Priority'])
    for m in MaintenanceRequest.query.all():
        writer.writerow([
            m.id, m.property_id, m.tenant_id, m.description, m.status, m.assigned_to,
            m.created_at, m.updated_at, m.priority
        ])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='maintenance_report.csv')
