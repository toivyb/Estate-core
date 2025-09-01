from flask import Blueprint, send_file, request
from flask_jwt_extended import jwt_required
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import io

bp = Blueprint("pdfs", __name__)

def _branded_pdf(title, rows):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    width, height = LETTER
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height-50, "EstateCore — Property Management")
    c.setFont("Helvetica", 10)
    c.drawString(50, height-65, title)
    y = height - 100
    c.setFont("Helvetica", 9)
    for row in rows:
        c.drawString(50, y, row)
        y -= 14
        if y < 80:
            c.showPage()
            y = height - 80
    c.showPage()
    c.save()
    buf.seek(0)
    return buf

@bp.get("/pdf/rent-receipt")
@jwt_required()
def rent_receipt():
    tenant = request.args.get("tenant","Tenant Name")
    month = request.args.get("month","8")
    year = request.args.get("year","2025")
    amount = request.args.get("amount","1500.00")
    buf = _branded_pdf("Rent Receipt", [f"Tenant: {tenant}", f"Period: {month}/{year}", f"Amount: ${amount}", "Status: PAID"])
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name="rent_receipt.pdf")

@bp.get("/pdf/income-vs-cost")
@jwt_required()
def income_vs_cost():
    income = request.args.get("income","10000")
    cost = request.args.get("cost","6000")
    net = float(income) - float(cost)
    buf = _branded_pdf("Income vs Cost", [f"Total Income: ${income}", f"Estimated Costs: ${cost}", f"Net Profit: ${net:.2f}"])
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name="income_vs_cost.pdf")
