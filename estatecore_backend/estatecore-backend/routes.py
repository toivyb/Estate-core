
from flask import Blueprint, jsonify, request
from estatecore_backend import db
from estatecore_backend.models import RentRecord
from estatecore_backend.utils.generate_rent_receipt import generate_rent_receipt_pdf

api_bp = Blueprint("api", __name__)

@api_bp.route("/api/rent/receipt/<int:rent_id>", methods=["GET"])
def download_rent_receipt(rent_id):
    rent = RentRecord.query.get_or_404(rent_id)
    return generate_rent_receipt_pdf(rent)
