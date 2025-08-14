
from flask import Blueprint

user_bp = Blueprint("user", __name__, url_prefix="/api/user")

@user_bp.route("/ping")
def ping():
    return {"message": "User route working"}
