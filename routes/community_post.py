from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.community_post import CommunityPost
from estatecore_backend.utils.auth import token_required  
from datetime import datetime

community = Blueprint('community', __name__)

@community.route('/api/community', methods=['POST'])
@token_required
def create_post(current_user):
    data = request.json
    post = CommunityPost(
        property_id=data['property_id'],
        posted_by=current_user.id,
        title=data['title'],
        content=data['content']
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({'message': 'Post created'}), 201

@community.route('/api/community/<int:property_id>', methods=['GET'])
@token_required
def get_posts(current_user, property_id):
    posts = CommunityPost.query.filter_by(property_id=property_id).order_by(CommunityPost.created_at.desc()).all()
    return jsonify([
        {
            'id': p.id,
            'title': p.title,
            'content': p.content,
            'posted_by': p.posted_by,
            'created_at': p.created_at.isoformat()
        } for p in posts
    ])