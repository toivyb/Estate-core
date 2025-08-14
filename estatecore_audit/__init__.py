"""
EstateCore Audit module
- Real filesystem folder creation for clients, buildings, tenants
- Audit trail logging
- Simple AI analytics for feature usage
"""

from .folders import ensure_client_folder, ensure_building_folder, ensure_tenant_folder
from .audit import log_event
from .analytics import recompute_usage_stats, get_usage_summary
