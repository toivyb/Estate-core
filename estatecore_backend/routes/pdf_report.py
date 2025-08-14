from flask import Blueprint, send_file
from io import BytesIO

pdf = Blueprint('pdf', __name__)

@pdf.route('/api/pdf-report', methods=['GET'])
def generate_pdf():
    fake_pdf = BytesIO()
    fake_pdf.write(b"%PDF-1.4\n%Fake PDF file")
    fake_pdf.seek(0)
    return send_file(fake_pdf, download_name="report.pdf", as_attachment=True)