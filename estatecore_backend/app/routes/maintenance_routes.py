
from flask import Blueprint

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/api/maintenance")

@maintenance_bp.route("/ping")
def ping():
    return {"message": "Maintenance route working"}
