import os

class Config:
    # Secret key for sessions / JWT - REQUIRED
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")

    # Database connection - REQUIRED
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable must be set")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    
    # Flask Configuration
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
