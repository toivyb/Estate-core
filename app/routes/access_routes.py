
from flask import Blueprint

access_bp = Blueprint("access", __name__, url_prefix="/api/access")

@access_bp.route("/ping")
def ping():
    return {"message": "Access route working"}
