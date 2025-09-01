"""
Application configuration.

This file defines a simple configuration class for the Flask application.  You
can extend or replace these settings as needed for different environments.  By
default it uses an SQLite database stored in the project directory.
"""

import os


class Config:
    # Use an environment variable if set, otherwise default to a local SQLite DB.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", "postgresql://postgres:password@127.0.0.1:5432/estatecore_devpayment_access.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email settings for sending invitation links.  These values should be
    # overridden via environment variables in your deployment environment.
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 25))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "false").lower() in {"1", "true", "yes"}
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_SENDER = os.environ.get("MAIL_SENDER", "no-reply@example.com")

    # Base URL used to construct invitation links (without trailing slash).
    BASE_URL = os.environ.get("BASE_URL")  # e.g. "http://localhost:5000"