from flask import Blueprint, request, jsonify
from utils.auth import token_required

ai_tagging = Blueprint('ai_tagging', __name__)

@ai_tagging.route('/api/ai-video-tags', methods=['POST'])
@token_required
def tag_video(current_user):
    return jsonify({"tags": ["mold", "crack", "peeling paint"]})