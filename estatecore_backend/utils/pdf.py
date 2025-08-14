def generate_rent_receipt(rent):
    path = f"/tmp/rent_receipt_{rent.id}.pdf"
    try:
        from fpdf import FPDF
    except Exception as e:
        raise RuntimeError("FPDF not installed: pip install fpdf2") from e
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
