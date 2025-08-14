
from fpdf import FPDF
from flask import send_file
import os

def generate_rent_receipt_pdf(rent_record):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Rent Receipt", ln=True, align="C")
    pdf.cell(200, 10, txt=f"Name: {rent_record.name}", ln=True)
    pdf.cell(200, 10, txt=f"Unit: {rent_record.unit}", ln=True)
    pdf.cell(200, 10, txt=f"Amount: ${rent_record.amount}", ln=True)
    pdf.cell(200, 10, txt=f"Status: {rent_record.status}", ln=True)
    pdf.output("receipt.pdf")
    return send_file("receipt.pdf", as_attachment=True)
