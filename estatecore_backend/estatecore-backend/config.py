
import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:password@127.0.0.1:5433/estatecore_devestatecore.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret")
    INVITE_TOKEN_TTL_HOURS = int(os.getenv("INVITE_TOKEN_TTL_HOURS", "72"))
    PDF_BRAND_NAME = os.getenv("PDF_BRAND_NAME", "EstateCore")
    PDF_TAGLINE = os.getenv("PDF_TAGLINE", "Intelligent Property Management")
    PDF_LOGO_PATH = os.getenv("PDF_LOGO_PATH", None)  # absolute path or None
