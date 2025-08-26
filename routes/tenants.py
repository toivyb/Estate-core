from flask import Blueprint

tenants_bp = Blueprint("tenants", __name__)

@tenants_bp.route("/tenants", methods=["GET"])
def list_tenants():
    return {"tenants": []}
