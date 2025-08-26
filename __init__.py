from flask import Flask, jsonify
from flask_mail import Mail
from datetime import datetime
import os

def create_app():
    app = Flask(__name__)

    # --- config ---
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/estatecore"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
    
    # Email configuration
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "587"))
    app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USE_SSL"] = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", os.environ.get("MAIL_USERNAME"))

    # --- extensions ---
    from .app import db, migrate, cors
    db.init_app(app)
    migrate.init_app(app, db)
    # Get allowed origins from environment variable or default to local
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:5175").split(",")
    
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type","Authorization"],
        methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
    )
    
    # Initialize Flask-Mail
    mail = Mail()
    mail.init_app(app)

    # --- routes (single blueprint with everything) ---
    from .routes import auth_bp, metrics_bp, features_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(features_bp)

    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        })
    
    @app.get("/")
    def root():
        return jsonify({
            "message": "EstateCore API is running",
            "version": "1.0.0",
            "endpoints": "/api/health"
        })
    
    @app.get("/api/debug/routes")
    def debug_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': rule.rule
            })
        return jsonify(routes)

    return app
