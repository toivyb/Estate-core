# estatecore_backend/app/__init__.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

# Extension singletons (no app bound here)
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
