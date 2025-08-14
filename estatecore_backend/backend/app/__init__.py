from estatecore_backend.extensions import db
﻿import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
from flask_migrate import Migrate


migrate = Migrate()

jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

def create_app():
    app = Flask(__name__)
    # ... your config ...
    db.init_app(app)
    migrate.init_app(app, db)   # <-- required for Flask-Migrate
    # import models so metadata exists
    from .models import User, Role
    return app

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "postgresql://postgres:password@127.0.0.1:5433/estatecore_devestatecore.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt")

    db.init_app(app)
    jwt.init_app(app)

    # Import models and create tables
    from .models.user import User, Role  # noqa
    with app.app_context():

    @app.get("/api/ping")
    def ping():
        return jsonify({"ok": True})

    # Auth routes (bootstrap + login)
    @app.post("/api/bootstrap-admin")
    def bootstrap_admin():
        data = request.get_json() or {}
        email = data.get("email", "admin@example.com").strip().lower()
        password = data.get("password", "admin123")
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(email=email, role=Role.SUPER_ADMIN)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
        return jsonify({"ok": True})

    @app.post("/api/login")
    def login():
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        u = User.query.filter_by(email=email).first()
        if not u or not u.check_password(password):
            return jsonify({"error":"Invalid credentials"}), 401
        token = create_access_token(identity={"id": u.id, "email": u.email, "role": u.role})
        return jsonify({"token": token, "user": {"email": u.email, "role": u.role}})

    return app
