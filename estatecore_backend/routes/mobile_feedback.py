from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.mobile_feedback import MobileFeedback
from utils.auth import token_required

feedback = Blueprint('feedback', __name__)

@feedback.route('/api/feedback', methods=['POST'])
@token_required
def submit_feedback(current_user):
    data = request.json
    entry = MobileFeedback(user_id=current_user.id, message=data['message'])
    db.session.add(entry)
    db.session.commit()
    return jsonify({"status": "submitted"})