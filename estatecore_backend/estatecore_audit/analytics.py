from collections import Counter, defaultdict
from datetime import datetime, timedelta
from sqlalchemy import func
from .models import db, AuditEvent, FeatureUsageDaily, UsageSummary

# Consider these as app features to track (customize as needed)
TRACKED_FEATURES = [
    "rent_receipt_pdf",
    "maintenance_request_create",
    "access_attempt",
    "lease_score_ai",
    "invite_token_create",
    "mobile_unlock",
    "visitor_pass",
]

def recompute_usage_stats(days:int=30, client_id:int=None):
    cutoff = datetime.utcnow() - timedelta(days=days)
    q = db.session.query(AuditEvent).filter(AuditEvent.created_at>=cutoff)
    if client_id is not None:
        q = q.filter(AuditEvent.client_id==client_id)

    # roll up by day and feature
    day_counts = defaultdict(int)
    events = q.all()
    for ev in events:
        if ev.entity_type == "feature" and ev.action in TRACKED_FEATURES:
            day = ev.created_at.strftime("%Y-%m-%d")
            key = (ev.client_id, ev.action, day)
            day_counts[key] += 1

    # upsert into FeatureUsageDaily
    for (cid, feature, day), cnt in day_counts.items():
        row = FeatureUsageDaily.query.filter_by(client_id=cid, feature=feature, day=day).first()
        if not row:
            row = FeatureUsageDaily(client_id=cid, feature=feature, day=day, count=cnt)
            db.session.add(row)
        else:
            row.count = cnt

    db.session.commit()

    # compute summary per client
    clients = set(cid for (cid, _, _) in day_counts.keys())
    for cid in clients:
        rows = FeatureUsageDaily.query.filter_by(client_id=cid).all()
        total = Counter()
        for r in rows:
            total[r.feature] += r.count
        top = total.most_common(5)
        under = [f for f in TRACKED_FEATURES if total[f] == 0]
        summary = UsageSummary.query.filter_by(client_id=cid).order_by(UsageSummary.computed_at.desc()).first()
        if not summary:
            summary = UsageSummary(client_id=cid)
            db.session.add(summary)
        summary.computed_at = datetime.utcnow()
        summary.top_features = [{"feature": f, "count": n} for f, n in top]
        summary.underused_features = [{"feature": f, "reason": "no usage in period"} for f in under]

    db.session.commit()


def get_usage_summary(client_id:int):
    return UsageSummary.query.filter_by(client_id=client_id).order_by(UsageSummary.computed_at.desc()).first()
