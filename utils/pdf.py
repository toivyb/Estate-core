def generate_rent_receipt(rent):
    path = f"/tmp/rent_receipt_{rent.id}.pdf"
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="EstateCore Rent Receipt", ln=1, align="C")
    pdf.cell(200, 10, txt=f"Tenant ID: {rent.tenant_id}", ln=2)
    pdf.cell(200, 10, txt=f"Amount: ${rent.amount}", ln=3)
    pdf.cell(200, 10, txt=f"Due: {rent.due_date}", ln=4)
    pdf.cell(200, 10, txt=f"Paid: {rent.paid_on}", ln=5)
    pdf.cell(200, 10, txt=f"Status: {rent.status}", ln=6)
    pdf.cell(200, 10, txt=f"Late Fee: {rent.late_fee}", ln=7)
    pdf.output(path)
    return path
def generate_payment_receipt(payment):
    path = f"/tmp/payment_receipt_{payment.id}.pdf"
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="EstateCore Payment Receipt", ln=1, align="C")
    pdf.cell(200, 10, txt=f"Payment ID: {payment.id}", ln=2)
    pdf.cell(200, 10, txt=f"Amount: ${payment.amount}", ln=3)
    pdf.cell(200, 10, txt=f"Tenant ID: {payment.tenant_id}", ln=4)
    pdf.cell(200, 10, txt=f"Rent ID: {payment.rent_id}", ln=5)
    pdf.cell(200, 10, txt=f"Status: {payment.status}", ln=6)
    pdf.cell(200, 10, txt=f"Date: {payment.timestamp}", ln=7)
    pdf.output(path)
    return path
