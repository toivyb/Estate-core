import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "devkey123")

    # Default to your local PostgreSQL 17 instance
    SQLALCHEMY_DATABASE_URI = "postgresql://estatecore_user:StrongPassword123@localhost:5433/estatecore_dev"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
