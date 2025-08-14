from ..extensions import db

# Import models so Alembic can detect them
from .user import User
from .rent import Rent

__all__ = ["db", "User", "Rent"]
