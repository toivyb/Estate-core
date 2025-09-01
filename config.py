import os

class Config:
    # Database connection with fallback
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///estatecore.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key with fallback for development
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-for-development")
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    
    # Flask Configuration
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"