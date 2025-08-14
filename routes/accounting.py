from flask import Blueprint, request, send_file, jsonify
from estatecore_backend.models.rent import Rent
from estatecore_backend.models.payment import Payment
from estatecore_backend.models.maintenance import MaintenanceRequest
import csv, io
from datetime import datetime

accounting_bp = Blueprint('accounting', __name__)

def qbo_rent_row(r):
    # Example: [Date, Type, Name, Memo, Amount]
    return [str(r.due_date), 'Invoice', f'Tenant {r.tenant_id}', f'Rent {r.id}', r.amount]

def qbo_payment_row(p):
    # Example: [Date, Type, Name, Memo, Amount]
    return [str(p.timestamp.date()), 'Payment', f'Tenant {p.tenant_id}', f'Rent {p.rent_id}', p.amount]

def qbo_expense_row(m):
    # Example: [Date, Type, Name, Memo, Amount]
    return [str(m.created_at.date()), 'Expense', f'Property {m.property_id}', f'Maintenance {m.id}', m.cost if hasattr(m, "cost") else 0]

@accounting_bp.route('/api/accounting/quickbooks_csv', methods=['GET'])
def quickbooks_csv():
    export_type = request.args.get('type')  # 'rent', 'payment', or 'expense'
    output = io.StringIO()
    writer = csv.writer(output)
    if export_type == 'rent':
        writer.writerow(['Date', 'Type', 'Name', 'Memo', 'Amount'])
        for r in Rent.query.all():
            writer.writerow(qbo_rent_row(r))
        fname = "quickbooks_rent.csv"
    elif export_type == 'payment':
        writer.writerow(['Date', 'Type', 'Name', 'Memo', 'Amount'])
        for p in Payment.query.all():
            writer.writerow(qbo_payment_row(p))
        fname = "quickbooks_payment.csv"
    elif export_type == 'expense':
        writer.writerow(['Date', 'Type', 'Name', 'Memo', 'Amount'])
        for m in MaintenanceRequest.query.all():
            writer.writerow(qbo_expense_row(m))
        fname = "quickbooks_expense.csv"
    else:
        return jsonify({'error': 'Invalid type'}), 400
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name=fname)

@accounting_bp.route('/api/accounting/tax_summary_pdf', methods=['GET'])
def tax_summary_pdf():
    # Minimal version, customize as needed
    year = int(request.args.get('year', datetime.now().year))
    # Filter all data for the year
    rents = Rent.query.filter(Rent.due_date >= datetime(year,1,1), Rent.due_date <= datetime(year,12,31)).all()
    payments = Payment.query.filter(Payment.timestamp >= datetime(year,1,1), Payment.timestamp <= datetime(year,12,31)).all()
    expenses = MaintenanceRequest.query.filter(MaintenanceRequest.created_at >= datetime(year,1,1), MaintenanceRequest.created_at <= datetime(year,12,31)).all()
    total_income = sum(p.amount for p in payments if p.status == 'success')
    total_expense = sum(getattr(e, 'cost', 0) for e in expenses)
    net_income = total_income - total_expense

    # PDF generation (simple text, use your PDF lib of choice)
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, f"Tax Summary {year}", ln=1, align="C")
    pdf.cell(200, 10, f"Total Income: ${total_income}", ln=2)
    pdf.cell(200, 10, f"Total Expenses: ${total_expense}", ln=3)
    pdf.cell(200, 10, f"Net Income: ${net_income}", ln=4)
    path = f"/tmp/tax_summary_{year}.pdf"
    pdf.output(path)
    return send_file(path, as_attachment=True)
