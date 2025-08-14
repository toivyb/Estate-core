
from .. import db
from .user import User, Role
from .property import Property, Unit, PropertyManager, Tenant
from .finance import RentRecord
from .maintenance import MaintenanceRequest, MaintenanceComment
from .access import AccessLog
from .invite import InviteToken

def register_models():
    # This function exists so Flask-Migrate can discover models via import side-effects.
    pass
