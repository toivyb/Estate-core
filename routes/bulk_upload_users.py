from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.user import User
import csv
import io
from utils.auth import token_required

bulk = Blueprint('bulk', __name__)

@bulk.route('/api/bulk-upload-users', methods=['POST'])
@token_required
def upload_users(current_user):
    file = request.files['file']
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    reader = csv.DictReader(stream)
    for row in reader:
        u = User(email=row['email'], name=row['name'], role=row['role'])
        db.session.add(u)
    db.session.commit()
    return jsonify({"status": "imported"})