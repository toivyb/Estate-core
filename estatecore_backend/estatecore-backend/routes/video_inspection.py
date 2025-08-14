from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.video_inspection import VideoInspection
from estatecore_backend.models.user import User
from utils.auth import token_required

video_inspections = Blueprint('video_inspections', __name__)

@video_inspections.route('/api/video-inspections', methods=['POST'])
@token_required
def upload_video_inspection(current_user):
    data = request.json
    inspection = VideoInspection(
        property_id=data['property_id'],
        uploaded_by=current_user.id,
        video_url=data['video_url'],
        notes=data.get('notes', '')
    )
    db.session.add(inspection)
    db.session.commit()
    return jsonify({'message': 'Video uploaded'}), 201

@video_inspections.route('/api/video-inspections/<int:property_id>', methods=['GET'])
@token_required
def get_video_inspections(current_user, property_id):
    inspections = VideoInspection.query.filter_by(property_id=property_id).all()
    return jsonify([
        {
            'id': i.id,
            'video_url': i.video_url,
            'notes': i.notes,
            'uploaded_by': i.uploaded_by,
            'created_at': i.created_at.isoformat()
        } for i in inspections
    ])