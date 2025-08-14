
from flask import Blueprint, request, jsonify
import json
import os
from datetime import datetime

save_bp = Blueprint("save", __name__, url_prefix="/api/ai")

SAVE_DIR = "app/ai_models/summaries"
os.makedirs(SAVE_DIR, exist_ok=True)

@save_bp.route("/save-summary", methods=["POST"])
def save_summary():
    try:
        data = request.get_json()
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename = f"summary_{timestamp}.json"
        filepath = os.path.join(SAVE_DIR, filename)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return jsonify({"status": "success", "file": filename}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
