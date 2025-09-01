from flask import Blueprint

maintenance_bp = Blueprint("maintenance", __name__)

@maintenance_bp.route("/maintenance", methods=["GET"])
def list_maintenance():
    return {"maintenance": []}
