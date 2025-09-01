from reportlab.pdfgen import canvas
import io

def generate_rent_pdf(user, rents):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    p.setFont("Helvetica", 12)
    p.drawString(100, 800, f"Rent Summary for {user.name} ({user.email})")

    y = 770
    for rent in rents:
        paid_status = "Paid" if rent.paid else "Unpaid"
        line = f"{rent.month}: ${rent.amount:.2f} - {paid_status}"
        p.drawString(100, y, line)
        y -= 20

    p.save()
    buffer.seek(0)
    return buffer
