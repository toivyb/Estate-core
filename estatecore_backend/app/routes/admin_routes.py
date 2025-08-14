
from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@admin_bp.route("/ping")
def ping():
    return {"message": "Admin route working"}
