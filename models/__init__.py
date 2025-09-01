from flask_sqlalchemy import SQLAlchemy
from estatecore_backend.extensions import db

# Core Models
from .user import User
from .property import Property, Unit
from .tenant import Tenant
from .lease import Lease, LeaseDocument, lease_tenants
from .rent_record import RentRecord
from .payment import Payment
from .maintenance import MaintenanceRequest, WorkOrder, MaintenancePhoto
from .expense import Expense
from .utilitybill import UtilityBill

# Legacy/Additional Models
from .lpr_event import LPREvent