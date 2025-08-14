
from flask import Blueprint

rent_bp = Blueprint("rent", __name__, url_prefix="/api/rent")

@rent_bp.route("/ping")
def ping():
    return {"message": "Rent route working"}
