
from flask import Blueprint

save_bp = Blueprint("save", __name__, url_prefix="/api/save")

@save_bp.route("/ping")
def ping():
    return {"message": "Save summary route working"}
