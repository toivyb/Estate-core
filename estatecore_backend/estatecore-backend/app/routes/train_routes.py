
from flask import Blueprint

train_bp = Blueprint("train", __name__, url_prefix="/api/train")

@train_bp.route("/ping")
def ping():
    return {"message": "Train route working"}
