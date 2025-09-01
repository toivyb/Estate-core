# __init__.py
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

from flask import Flask, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

# --- Optional extensions (initialized only if present) -----------------------
# Your repo has an `extensions.py` – we try to import things from there but
# won't crash if any are missing.
db = migrate = jwt = mail = cache = limiter = cors_ext = None  # type: ignore

try:
    from extensions import db  # SQLAlchemy
except Exception:
    pass

try:
    from extensions import migrate  # Flask-Migrate / Alembic
except Exception:
    pass

try:
    from extensions import jwt  # flask-jwt-extended
except Exception:
    pass

try:
    from extensions import mail  # Flask-Mail(Man)
except Exception:
    pass

try:
    from extensions import cache  # Flask-Caching
except Exception:
    pass

try:
    from extensions import limiter  # Flask-Limiter
except Exception:
    pass

try:
    from flask_cors import CORS as _CORS  # direct import if not in extensions
    cors_ext = _CORS
except Exception:
    try:
        from extensions import cors as cors_ext  # type: ignore
    except Exception:
        cors_ext = None


# --- Config ------------------------------------------------------------------
def _get_allowed_origins() -> list[str]:
    """Allowed CORS origins from env; includes sensible defaults for your setup."""
    default = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://app.myestatecore.com",
        "https://www.app.myestatecore.com",
    ]
    # Support comma-separated list in env
    extra = os.getenv("CORS_ALLOWED_ORIGINS", "")
    extra_list = [o.strip() for o in extra.split(",") if o.strip()]
    return sorted(set(default + extra_list))


def _configure_logging(app: Flask) -> None:
    """JSON logs to stdout (works well on Fly.io/Render/Heroku/etc)."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    app.logger.setLevel(level)
    root = logging.getLogger()
    root.setLevel(level)

    # avoid duplicate handlers in reloaders
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s","name":"%(name)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)


def _configure_cors(app: Flask) -> None:
    """Enable permissive but safe CORS for API routes."""
    if not cors_ext:
        app.logger.warning("CORS not enabled (flask-cors missing).")
        return

    cors_ext(  # type: ignore
        app,
        resources={r"/api/*": {"origins": _get_allowed_origins()}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "ngrok-skip-browser-warning",  # fixes the ngrok preflight failure
            "X-CSRF-Token",
        ],
        expose_headers=["Content-Type"],
        max_age=86400,
    )

    @app.after_request
    def _add_extra_cors_headers(resp):
        # Some proxies/CDNs are picky; these extra headers make life easier.
        resp.headers.setdefault("Vary", "Origin")
        resp.headers.setdefault("Access-Control-Allow-Credentials", "true")
        return resp


def _configure_proxy(app: Flask) -> None:
    """Respect X-Forwarded-* from Fly.io/Render/Cloudflare/etc."""
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)  # type: ignore


def _init_extensions(app: Flask) -> None:
    for ext in (db, migrate, jwt, mail, cache, limiter):
        if ext and hasattr(ext, "init_app"):
            try:
                ext.init_app(app)  # type: ignore
            except Exception as e:
                app.logger.exception("Failed to init extension %r: %s", ext, e)


def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints under /api."""
    # Each import is wrapped so a missing file doesn't kill the app.
    def _register(module_path: str, attr: str = "bp", url_prefix: Optional[str] = "/api") -> None:
        try:
            mod = __import__(module_path, fromlist=[attr])
            bp = getattr(mod, attr)
            app.register_blueprint(bp, url_prefix=url_prefix)
            app.logger.info("Registered blueprint %s at %s", module_path, url_prefix or "")
        except Exception as e:
            app.logger.warning("Skipping blueprint %s: %s", module_path, e)

    # Your repo shows these:
    _register("routes.auth")
    _register("routes.status")
    _register("routes.tenants")
    _register("routes.rent")
    _register("routes.payment")


def _register_cli(app: Flask) -> None:
    """Optionally load CLI commands (if present)."""
    for mod_name in ("manage", "cli", "seed", "seed_super_admin", "create_super_admin", "create_test_org"):
        try:
            __import__(mod_name)
        except Exception:
            pass


# --- Application Factory ------------------------------------------------------
def create_app(config_object: Optional[str | Any] = None) -> Flask:
    """
    Standard Flask application factory.

    `config_object` may be:
      - a config object
      - dotted path to a config class (e.g., "config.ProductionConfig")
      - None (then we'll try CONFIG_CLASS env or default to config.Config)
    """
    app = Flask(__name__, instance_relative_config=True)

    # Instance folder (for sqlite/instance configs if you use them)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except Exception:
        pass

    # Load config
    if config_object is None:
        config_object = os.getenv("CONFIG_CLASS", "config.Config")

    try:
        if isinstance(config_object, str):
            # load "package.ClassName"
            module, _, cls = config_object.rpartition(".")
            if module:
                conf = getattr(__import__(module, fromlist=[cls]), cls)
                app.config.from_object(conf)
            else:
                app.config.from_object(config_object)
        else:
            app.config.from_object(config_object)
    except Exception as e:
        # Last-resort defaults
        app.logger.warning("Falling back to default config: %s", e)
        app.config.update(
            SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret"),
            SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "app.db")),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JSON_SORT_KEYS=False,
        )

    # Ensure API url prefix setting exists for other modules if they need it
    app.config.setdefault("API_PREFIX", "/api")

    # Core middleware/logging/CORS
    _configure_logging(app)
    _configure_proxy(app)
    _configure_cors(app)

    # Init extensions & blueprints
    _init_extensions(app)
    _register_blueprints(app)
    _register_cli(app)

    # --------- Health & root routes ----------
    @app.get(app.config["API_PREFIX"] + "/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "time": datetime.utcnow().isoformat() + "Z",
                "service": "estatecore-backend",
            }
        ), 200

    @app.get("/")
    def root():
        return jsonify({"service": "estatecore-backend", "message": "See /api/health"}), 200

    # Fast path for CORS preflights to anything under /api
    @app.route(app.config["API_PREFIX"] + "/<path:_any>", methods=["OPTIONS"])
    def preflight(_any: str):
        return ("", 204)

    # --------- Error Handlers ----------
    @app.errorhandler(404)
    def _not_found(e):
        return jsonify({"error": "Not Found", "path": request.path}), 404

    @app.errorhandler(400)
    def _bad_request(e):
        msg = getattr(e, "description", "Bad Request")
        return jsonify({"error": "Bad Request", "message": msg}), 400

    @app.errorhandler(500)
    def _server_error(e):
        app.logger.exception("Unhandled exception: %s", e)
        return jsonify({"error": "Internal Server Error"}), 500

    return app


# Export a module-level `app` to keep WSGI/Procfile simple:
#   - Procfile: `web: gunicorn wsgi:app` (recommended)
#   - If some environments import `estatecore_backend:app`, this also works.
app = create_app()
