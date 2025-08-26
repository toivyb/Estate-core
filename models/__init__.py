from flask_sqlalchemy import SQLAlchemy
from estatecore_backend.extensions import db

from .user import User
from .lpr_event import LPREvent
from .rent_record import RentRecord
from .payment import Payment