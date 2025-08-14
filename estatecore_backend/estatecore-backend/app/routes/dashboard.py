
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from .. import db
from ..models.finance import RentRecord
from ..models.maintenance import MaintenanceRequest

bp = Blueprint('dashboard', __name__)

@bp.get('/dashboard/summary')
@jwt_required()
def summary():
    total_rent = db.session.query(func.coalesce(func.sum(RentRecord.amount_due), 0)).scalar() or 0
    total_paid = db.session.query(func.coalesce(func.sum(RentRecord.amount_paid), 0)).scalar() or 0
    est_costs = total_rent * 0.35  # simple placeholder
    net = total_rent - est_costs
    open_maint = MaintenanceRequest.query.filter(MaintenanceRequest.status != 'resolved').count()
    return jsonify({'total_rent': float(total_rent), 'est_costs': float(est_costs), 'net': float(net), 'open_maintenance': open_maint})
