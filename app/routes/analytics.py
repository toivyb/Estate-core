from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from .. import db
from ..models import (
    Property, Unit, Lease, Tenant, RentRecord, Payment, 
    MaintenanceRequest, WorkOrder, User
)
from ..security.rbac import require_role

bp = Blueprint("analytics", __name__)


@bp.get("/analytics/dashboard")
@jwt_required()
def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    
    # Property Statistics
    total_properties = Property.query.filter_by(status='active').count()
    total_units = Unit.query.count()
    occupied_units = Unit.query.filter_by(status='occupied').count()
    available_units = Unit.query.filter_by(status='available').count()
    occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
    
    # Tenant Statistics
    active_tenants = Tenant.query.filter_by(status='active').count()
    total_tenants = Tenant.query.count()
    
    # Lease Statistics
    active_leases = Lease.query.filter_by(status='active').count()
    draft_leases = Lease.query.filter_by(status='draft').count()
    
    # Expiring leases (next 30 days)
    next_month = date.today() + relativedelta(days=30)
    expiring_leases = Lease.query.filter(
        and_(
            Lease.status == 'active',
            Lease.end_date <= next_month,
            Lease.end_date >= date.today()
        )
    ).count()
    
    # Financial Statistics (Current Month)
    current_month_start = date.today().replace(day=1)
    next_month_start = current_month_start + relativedelta(months=1)
    
    current_month_rent = db.session.query(
        func.sum(RentRecord.total_amount),
        func.sum(RentRecord.amount_paid),
        func.sum(RentRecord.amount_outstanding)
    ).filter(
        and_(
            RentRecord.period_start >= current_month_start,
            RentRecord.period_start < next_month_start
        )
    ).first()
    
    rent_expected = float(current_month_rent[0] or 0)
    rent_collected = float(current_month_rent[1] or 0)
    rent_outstanding = float(current_month_rent[2] or 0)
    collection_rate = (rent_collected / rent_expected * 100) if rent_expected > 0 else 0
    
    # Overdue Rent
    overdue_rent = db.session.query(
        func.count(RentRecord.id),
        func.sum(RentRecord.amount_outstanding)
    ).filter(
        and_(
            RentRecord.status.in_(['unpaid', 'partial']),
            RentRecord.due_date < date.today()
        )
    ).first()
    
    overdue_count = overdue_rent[0] or 0
    overdue_amount = float(overdue_rent[1] or 0)
    
    # Maintenance Statistics
    maintenance_stats = db.session.query(
        func.count(MaintenanceRequest.id).filter(MaintenanceRequest.status == 'open').label('open'),
        func.count(MaintenanceRequest.id).filter(MaintenanceRequest.status == 'in_progress').label('in_progress'),
        func.count(MaintenanceRequest.id).filter(MaintenanceRequest.priority == 'emergency').label('emergency'),
        func.sum(MaintenanceRequest.estimated_cost).label('estimated_cost'),
        func.sum(MaintenanceRequest.actual_cost).label('actual_cost')
    ).first()
    
    # Recent Activity (last 30 days)
    thirty_days_ago = date.today() - relativedelta(days=30)
    
    recent_new_leases = Lease.query.filter(
        Lease.created_at >= thirty_days_ago
    ).count()
    
    recent_payments = Payment.query.filter(
        and_(
            Payment.created_at >= thirty_days_ago,
            Payment.status == 'completed'
        )
    ).count()
    
    recent_maintenance = MaintenanceRequest.query.filter(
        MaintenanceRequest.created_at >= thirty_days_ago
    ).count()
    
    return jsonify({
        "property_stats": {
            "total_properties": total_properties,
            "total_units": total_units,
            "occupied_units": occupied_units,
            "available_units": available_units,
            "occupancy_rate": round(occupancy_rate, 2)
        },
        "tenant_stats": {
            "active_tenants": active_tenants,
            "total_tenants": total_tenants
        },
        "lease_stats": {
            "active_leases": active_leases,
            "draft_leases": draft_leases,
            "expiring_soon": expiring_leases
        },
        "financial_stats": {
            "rent_expected": rent_expected,
            "rent_collected": rent_collected,
            "rent_outstanding": rent_outstanding,
            "collection_rate": round(collection_rate, 2),
            "overdue_count": overdue_count,
            "overdue_amount": overdue_amount
        },
        "maintenance_stats": {
            "open_requests": maintenance_stats.open or 0,
            "in_progress_requests": maintenance_stats.in_progress or 0,
            "emergency_requests": maintenance_stats.emergency or 0,
            "estimated_costs": float(maintenance_stats.estimated_cost or 0),
            "actual_costs": float(maintenance_stats.actual_cost or 0)
        },
        "recent_activity": {
            "new_leases": recent_new_leases,
            "payments_received": recent_payments,
            "maintenance_requests": recent_maintenance
        }
    }), 200


@bp.get("/analytics/financial-report")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def get_financial_report():
    """Get detailed financial report"""
    # Query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    property_id = request.args.get('property_id', type=int)
    
    # Default to current year if no dates provided
    if not start_date_str or not end_date_str:
        today = date.today()
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                "error": "validation_error",
                "message": "Invalid date format. Use YYYY-MM-DD"
            }), 400
    
    # Base query for rent records in date range
    rent_query = RentRecord.query.filter(
        and_(
            RentRecord.period_start >= start_date,
            RentRecord.period_end <= end_date
        )
    )
    
    if property_id:
        rent_query = rent_query.filter(RentRecord.property_id == property_id)
    
    # Revenue Statistics
    revenue_stats = rent_query.with_entities(
        func.sum(RentRecord.total_amount).label('total_expected'),
        func.sum(RentRecord.amount_paid).label('total_collected'),
        func.sum(RentRecord.amount_outstanding).label('total_outstanding'),
        func.sum(RentRecord.late_fee).label('total_late_fees')
    ).first()
    
    # Payment Method Breakdown
    payment_methods = db.session.query(
        Payment.payment_method,
        func.sum(Payment.amount),
        func.count(Payment.id)
    ).join(RentRecord).filter(
        and_(
            RentRecord.period_start >= start_date,
            RentRecord.period_end <= end_date,
            Payment.status == 'completed'
        )
    )
    
    if property_id:
        payment_methods = payment_methods.filter(RentRecord.property_id == property_id)
    
    payment_methods = payment_methods.group_by(Payment.payment_method).all()
    
    # Monthly Breakdown
    monthly_revenue = db.session.query(
        func.extract('year', RentRecord.period_start).label('year'),
        func.extract('month', RentRecord.period_start).label('month'),
        func.sum(RentRecord.total_amount).label('expected'),
        func.sum(RentRecord.amount_paid).label('collected')
    ).filter(
        and_(
            RentRecord.period_start >= start_date,
            RentRecord.period_end <= end_date
        )
    )
    
    if property_id:
        monthly_revenue = monthly_revenue.filter(RentRecord.property_id == property_id)
    
    monthly_revenue = monthly_revenue.group_by(
        func.extract('year', RentRecord.period_start),
        func.extract('month', RentRecord.period_start)
    ).order_by('year', 'month').all()
    
    # Property Performance
    property_performance = db.session.query(
        Property.id,
        Property.name,
        func.sum(RentRecord.total_amount).label('expected'),
        func.sum(RentRecord.amount_paid).label('collected'),
        func.count(RentRecord.id).label('rent_records')
    ).join(RentRecord).filter(
        and_(
            RentRecord.period_start >= start_date,
            RentRecord.period_end <= end_date
        )
    )
    
    if property_id:
        property_performance = property_performance.filter(Property.id == property_id)
    
    property_performance = property_performance.group_by(
        Property.id, Property.name
    ).order_by(desc('collected')).all()
    
    # Maintenance Costs for the period
    maintenance_costs = db.session.query(
        func.sum(MaintenanceRequest.actual_cost)
    ).filter(
        and_(
            MaintenanceRequest.completed_at >= start_date,
            MaintenanceRequest.completed_at <= end_date,
            MaintenanceRequest.status == 'completed'
        )
    )
    
    if property_id:
        maintenance_costs = maintenance_costs.filter(
            MaintenanceRequest.property_id == property_id
        )
    
    total_maintenance_costs = float(maintenance_costs.scalar() or 0)
    
    # Calculate profit/loss
    total_revenue = float(revenue_stats.total_collected or 0)
    net_income = total_revenue - total_maintenance_costs
    
    return jsonify({
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "property_id": property_id
        },
        "revenue_summary": {
            "total_expected": float(revenue_stats.total_expected or 0),
            "total_collected": total_revenue,
            "total_outstanding": float(revenue_stats.total_outstanding or 0),
            "total_late_fees": float(revenue_stats.total_late_fees or 0),
            "collection_rate": round((total_revenue / float(revenue_stats.total_expected or 1)) * 100, 2)
        },
        "expenses": {
            "maintenance_costs": total_maintenance_costs
        },
        "net_income": net_income,
        "payment_methods": [
            {
                "method": method,
                "amount": float(amount),
                "count": count
            }
            for method, amount, count in payment_methods
        ],
        "monthly_breakdown": [
            {
                "year": int(year),
                "month": int(month),
                "expected": float(expected),
                "collected": float(collected),
                "collection_rate": round((float(collected) / float(expected or 1)) * 100, 2)
            }
            for year, month, expected, collected in monthly_revenue
        ],
        "property_performance": [
            {
                "property_id": prop_id,
                "property_name": name,
                "expected": float(expected),
                "collected": float(collected),
                "rent_records": records,
                "collection_rate": round((float(collected) / float(expected or 1)) * 100, 2)
            }
            for prop_id, name, expected, collected, records in property_performance
        ]
    }), 200


@bp.get("/analytics/occupancy-report")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def get_occupancy_report():
    """Get occupancy analytics"""
    property_id = request.args.get('property_id', type=int)
    
    # Overall occupancy stats
    query = Unit.query
    if property_id:
        query = query.filter(Unit.property_id == property_id)
    
    total_units = query.count()
    occupied_units = query.filter(Unit.status == 'occupied').count()
    available_units = query.filter(Unit.status == 'available').count()
    maintenance_units = query.filter(Unit.status == 'maintenance').count()
    unavailable_units = query.filter(Unit.status == 'unavailable').count()
    
    overall_occupancy = (occupied_units / total_units * 100) if total_units > 0 else 0
    
    # Property-wise occupancy
    property_occupancy = db.session.query(
        Property.id,
        Property.name,
        func.count(Unit.id).label('total_units'),
        func.sum(func.case([(Unit.status == 'occupied', 1)], else_=0)).label('occupied'),
        func.sum(func.case([(Unit.status == 'available', 1)], else_=0)).label('available')
    ).join(Unit).group_by(Property.id, Property.name)
    
    if property_id:
        property_occupancy = property_occupancy.filter(Property.id == property_id)
    
    property_occupancy = property_occupancy.all()
    
    # Lease expiration analysis
    lease_expirations = db.session.query(
        func.extract('year', Lease.end_date).label('year'),
        func.extract('month', Lease.end_date).label('month'),
        func.count(Lease.id).label('expiring_leases')
    ).filter(
        and_(
            Lease.status == 'active',
            Lease.end_date >= date.today(),
            Lease.end_date <= date.today() + relativedelta(months=12)
        )
    )
    
    if property_id:
        lease_expirations = lease_expirations.filter(Lease.property_id == property_id)
    
    lease_expirations = lease_expirations.group_by(
        func.extract('year', Lease.end_date),
        func.extract('month', Lease.end_date)
    ).order_by('year', 'month').all()
    
    # Average lease length
    avg_lease_length = db.session.query(
        func.avg(Lease.lease_term_months)
    ).filter(Lease.status.in_(['active', 'terminated']))
    
    if property_id:
        avg_lease_length = avg_lease_length.filter(Lease.property_id == property_id)
    
    avg_lease_length = avg_lease_length.scalar() or 0
    
    # Tenant turnover (last 12 months)
    twelve_months_ago = date.today() - relativedelta(months=12)
    
    terminated_leases = Lease.query.filter(
        and_(
            Lease.status == 'terminated',
            Lease.termination_date >= twelve_months_ago
        )
    )
    
    if property_id:
        terminated_leases = terminated_leases.filter(Lease.property_id == property_id)
    
    turnover_count = terminated_leases.count()
    turnover_rate = (turnover_count / occupied_units * 100) if occupied_units > 0 else 0
    
    return jsonify({
        "overall_occupancy": {
            "total_units": total_units,
            "occupied_units": occupied_units,
            "available_units": available_units,
            "maintenance_units": maintenance_units,
            "unavailable_units": unavailable_units,
            "occupancy_rate": round(overall_occupancy, 2)
        },
        "property_occupancy": [
            {
                "property_id": prop_id,
                "property_name": name,
                "total_units": int(total),
                "occupied_units": int(occupied or 0),
                "available_units": int(available or 0),
                "occupancy_rate": round((int(occupied or 0) / int(total or 1)) * 100, 2)
            }
            for prop_id, name, total, occupied, available in property_occupancy
        ],
        "lease_expirations": [
            {
                "year": int(year),
                "month": int(month),
                "expiring_count": int(count)
            }
            for year, month, count in lease_expirations
        ],
        "lease_metrics": {
            "average_lease_length_months": round(float(avg_lease_length), 1),
            "turnover_count_12m": turnover_count,
            "turnover_rate": round(turnover_rate, 2)
        }
    }), 200


@bp.get("/analytics/maintenance-report")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def get_maintenance_report():
    """Get maintenance analytics"""
    # Query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    property_id = request.args.get('property_id', type=int)
    
    # Default to last 6 months if no dates provided
    if not start_date_str or not end_date_str:
        end_date = date.today()
        start_date = end_date - relativedelta(months=6)
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                "error": "validation_error",
                "message": "Invalid date format. Use YYYY-MM-DD"
            }), 400
    
    # Base query
    query = MaintenanceRequest.query.filter(
        MaintenanceRequest.created_at >= start_date
    )
    
    if property_id:
        query = query.filter(MaintenanceRequest.property_id == property_id)
    
    # Status breakdown
    status_breakdown = db.session.query(
        MaintenanceRequest.status,
        func.count(MaintenanceRequest.id)
    ).filter(MaintenanceRequest.created_at >= start_date)
    
    if property_id:
        status_breakdown = status_breakdown.filter(
            MaintenanceRequest.property_id == property_id
        )
    
    status_breakdown = status_breakdown.group_by(
        MaintenanceRequest.status
    ).all()
    
    # Category breakdown
    category_breakdown = db.session.query(
        MaintenanceRequest.category,
        func.count(MaintenanceRequest.id),
        func.avg(MaintenanceRequest.actual_cost)
    ).filter(MaintenanceRequest.created_at >= start_date)
    
    if property_id:
        category_breakdown = category_breakdown.filter(
            MaintenanceRequest.property_id == property_id
        )
    
    category_breakdown = category_breakdown.group_by(
        MaintenanceRequest.category
    ).all()
    
    # Response time analysis (average days from created to completed)
    completed_requests = query.filter(
        and_(
            MaintenanceRequest.status == 'completed',
            MaintenanceRequest.completed_at.isnot(None)
        )
    ).all()
    
    if completed_requests:
        avg_response_time = sum(
            (req.completed_at.date() - req.created_at.date()).days
            for req in completed_requests
        ) / len(completed_requests)
    else:
        avg_response_time = 0
    
    # Cost analysis
    cost_stats = query.filter(
        MaintenanceRequest.status == 'completed'
    ).with_entities(
        func.sum(MaintenanceRequest.estimated_cost),
        func.sum(MaintenanceRequest.actual_cost),
        func.avg(MaintenanceRequest.actual_cost),
        func.count(MaintenanceRequest.id)
    ).first()
    
    # Monthly trends
    monthly_trends = db.session.query(
        func.extract('year', MaintenanceRequest.created_at).label('year'),
        func.extract('month', MaintenanceRequest.created_at).label('month'),
        func.count(MaintenanceRequest.id).label('count'),
        func.sum(MaintenanceRequest.actual_cost).label('cost')
    ).filter(MaintenanceRequest.created_at >= start_date)
    
    if property_id:
        monthly_trends = monthly_trends.filter(
            MaintenanceRequest.property_id == property_id
        )
    
    monthly_trends = monthly_trends.group_by(
        func.extract('year', MaintenanceRequest.created_at),
        func.extract('month', MaintenanceRequest.created_at)
    ).order_by('year', 'month').all()
    
    return jsonify({
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "property_id": property_id
        },
        "status_breakdown": {
            status: count for status, count in status_breakdown
        },
        "category_analysis": [
            {
                "category": category,
                "count": count,
                "average_cost": float(avg_cost or 0)
            }
            for category, count, avg_cost in category_breakdown
        ],
        "performance_metrics": {
            "average_response_time_days": round(avg_response_time, 1),
            "total_estimated_cost": float(cost_stats[0] or 0),
            "total_actual_cost": float(cost_stats[1] or 0),
            "average_cost_per_request": float(cost_stats[2] or 0),
            "completed_requests": cost_stats[3] or 0
        },
        "monthly_trends": [
            {
                "year": int(year),
                "month": int(month),
                "request_count": count,
                "total_cost": float(cost or 0)
            }
            for year, month, count, cost in monthly_trends
        ]
    }), 200


@bp.get("/analytics/tenant-report")
@jwt_required()
@require_role(['super_admin', 'admin', 'property_manager'])
def get_tenant_report():
    """Get tenant analytics"""
    
    # Tenant status breakdown
    tenant_status = db.session.query(
        Tenant.status,
        func.count(Tenant.id)
    ).group_by(Tenant.status).all()
    
    # Payment behavior analysis
    payment_behavior = db.session.query(
        Tenant.id,
        Tenant.first_name,
        Tenant.last_name,
        func.count(RentRecord.id).label('total_records'),
        func.sum(func.case([(RentRecord.status == 'paid', 1)], else_=0)).label('on_time_payments'),
        func.sum(RentRecord.amount_outstanding).label('outstanding_balance')
    ).outerjoin(RentRecord).group_by(
        Tenant.id, Tenant.first_name, Tenant.last_name
    ).having(func.count(RentRecord.id) > 0).all()
    
    # Calculate payment scores
    tenant_scores = []
    for tenant_data in payment_behavior:
        tenant_id, first_name, last_name, total, on_time, outstanding = tenant_data
        payment_rate = (on_time / total * 100) if total > 0 else 0
        
        tenant_scores.append({
            "tenant_id": tenant_id,
            "tenant_name": f"{first_name} {last_name}",
            "total_rent_records": total,
            "on_time_payments": on_time,
            "payment_rate": round(payment_rate, 1),
            "outstanding_balance": float(outstanding or 0)
        })
    
    # Sort by payment rate (best tenants first)
    tenant_scores.sort(key=lambda x: x['payment_rate'], reverse=True)
    
    # Lease length analysis
    lease_lengths = db.session.query(
        func.avg(Lease.lease_term_months),
        func.min(Lease.lease_term_months),
        func.max(Lease.lease_term_months)
    ).filter(Lease.status.in_(['active', 'terminated'])).first()
    
    # Move-in trends (last 12 months)
    twelve_months_ago = date.today() - relativedelta(months=12)
    
    move_in_trends = db.session.query(
        func.extract('year', Tenant.move_in_date).label('year'),
        func.extract('month', Tenant.move_in_date).label('month'),
        func.count(Tenant.id).label('move_ins')
    ).filter(
        and_(
            Tenant.move_in_date >= twelve_months_ago,
            Tenant.move_in_date.isnot(None)
        )
    ).group_by(
        func.extract('year', Tenant.move_in_date),
        func.extract('month', Tenant.move_in_date)
    ).order_by('year', 'month').all()
    
    return jsonify({
        "tenant_status_breakdown": {
            status: count for status, count in tenant_status
        },
        "payment_analysis": {
            "top_tenants": tenant_scores[:10],  # Top 10 by payment rate
            "problem_tenants": [
                tenant for tenant in tenant_scores 
                if tenant['outstanding_balance'] > 0 or tenant['payment_rate'] < 80
            ]
        },
        "lease_metrics": {
            "average_lease_length": round(float(lease_lengths[0] or 0), 1),
            "shortest_lease": int(lease_lengths[1] or 0),
            "longest_lease": int(lease_lengths[2] or 0)
        },
        "move_in_trends": [
            {
                "year": int(year),
                "month": int(month),
                "move_ins": move_ins
            }
            for year, month, move_ins in move_in_trends
        ]
    }), 200