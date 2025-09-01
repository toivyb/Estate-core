from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.notification import Notification
from utils.auth import token_required

notifications = Blueprint('notifications', __name__)

@notifications.route('/api/notify', methods=['POST'])
@token_required
def send_notification(current_user):
    data = request.json
    note = Notification(
        to_user_id=data['to'],
        message=data['message'],
        type=data.get('type', 'info')
    )
    db.session.add(note)
    db.session.commit()
    return jsonify({"message": "Notification sent."})

@notifications.route('/api/inbox/<int:user_id>', methods=['GET'])
@token_required
def get_notifications(current_user, user_id):
    notes = Notification.query.filter_by(to_user_id=user_id).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        "message": n.message,
        "type": n.type,
        "created_at": n.created_at.isoformat()
    } for n in notes])