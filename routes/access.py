from flask import Blueprint

access_bp = Blueprint("access", __name__)

@access_bp.route("/access", methods=["GET"])
def list_access():
    return {"access": []}
