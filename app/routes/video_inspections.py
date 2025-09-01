from flask import Blueprint, jsonify
video_bp = Blueprint('video_bp', __name__)

@video_bp.route('/api/video-inspections/<int:property_id>', methods=['GET'])
def list_video_inspections(property_id):
    # Return empty list or mock data
    return jsonify([])
