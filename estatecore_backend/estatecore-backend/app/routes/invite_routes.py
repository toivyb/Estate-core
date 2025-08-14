
from flask import Blueprint

invite_bp = Blueprint("invite", __name__, url_prefix="/api/invite")

@invite_bp.route("/ping")
def ping():
    return {"message": "Invite route working"}
