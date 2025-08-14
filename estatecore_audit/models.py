from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from estatecore_backend import db

class AuditEvent(db.Model):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, index=True, nullable=False)
    actor_id = Column(Integer, index=True, nullable=True)
    entity_type = Column(String(50), nullable=False)   # client/building/tenant/feature
    entity_id = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False)        # created/updated/deleted/login/etc
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_audit_events_client_created", "client_id", "created_at"),
    )

class FeatureUsageDaily(db.Model):
    __tablename__ = "feature_usage_daily"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, index=True, nullable=False)
    feature = Column(String(64), index=True, nullable=False)
    day = Column(String(10), index=True, nullable=False)   # YYYY-MM-DD
    count = Column(Integer, default=0)

class UsageSummary(db.Model):
    __tablename__ = "usage_summary"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, index=True, nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow)
    top_features = Column(JSON, nullable=True)  # [{"feature":"X","count":N}, ...]
    underused_features = Column(JSON, nullable=True)
