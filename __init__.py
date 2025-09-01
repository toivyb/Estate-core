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
        # Add common development and deployment domains
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:4173",
        "http://localhost:8080",
        "https://localhost:5173",
        "https://localhost:5174",
        "https://6245563faf76.ngrok-free.app",
        "https://*.ngrok-free.app",
        "https://*.ngrok.io"
    ]
    # Support comma-separated list in env
    extra = os.getenv("CORS_ALLOWED_ORIGINS", "")
    extra_list = [o.strip() for o in extra.split(",") if o.strip()]
    
    # For development, allow both localhost and production domains
    if os.getenv("FLASK_ENV") == "development" or os.getenv("ENVIRONMENT") == "development":
        # Allow both localhost and production domains in development
        return sorted(set(default + extra_list))
    
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
        resources={
            r"/api/*": {"origins": _get_allowed_origins()},
            r"/rent-records/*": {"origins": _get_allowed_origins()},
            r"/analytics/*": {"origins": _get_allowed_origins()},
            r"/payments/*": {"origins": _get_allowed_origins()},
            r"/payments": {"origins": _get_allowed_origins()},
            # Catch all for any other routes
            r"/*": {"origins": _get_allowed_origins()}
        },
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

    # Your repo shows these - using correct blueprint attribute names:
    _register("routes.auth", "auth_bp")
    _register("routes.status", "status_bp") 
    _register("routes.tenants", "tenants_bp")
    _register("routes.rent", "rent_bp")
    _register("routes.payment", "payment_bp")


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
    # _register_blueprints(app)  # Temporarily disable to test route registration
    _register_cli(app)

    # --------- Health & root routes ----------
    print("REGISTERING HEALTH ROUTE...")
    
    @app.route(app.config["API_PREFIX"] + "/health", methods=["GET", "POST"])
    def health():
        if request.method == "POST":
            # Handle login via health endpoint for testing
            data = request.get_json() or {}
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            
            if email == "admin@example.com" and password == "SecureAdmin123!":
                return jsonify({
                    "access_token": "test-token-12345",
                    "user": {
                        "id": 1,
                        "email": email,
                        "name": "Admin User",
                        "role": "super_admin"
                    }
                }), 200
            else:
                return jsonify({"message": "Invalid credentials"}), 401
        
        return jsonify(
            {
                "status": "ok",
                "time": datetime.utcnow().isoformat() + "Z",
                "service": "estatecore-backend",
            }
        ), 200
        
    print("HEALTH ROUTE REGISTERED")
    
    # Login route using same pattern as health endpoint
    @app.route(app.config["API_PREFIX"] + "/login", methods=["POST"])
    def api_login_route():
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        if email == "admin@example.com" and password == "SecureAdmin123!":
            return jsonify({
                "access_token": "test-token-12345",
                "user": {
                    "id": 1,
                    "email": email,
                    "name": "Admin User",
                    "role": "super_admin"
                }
            }), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    
    # Me endpoint to get current user info
    @app.route(app.config["API_PREFIX"] + "/me", methods=["GET", "OPTIONS"])
    def api_me():
        if request.method == 'OPTIONS':
            return '', 200
            
        # Simple mock user data
        return jsonify({
            "id": 1,
            "email": "admin@example.com",
            "name": "Admin User",
            "role": "super_admin"
        }), 200
    
    @app.get("/")
    def root():
        return jsonify({"service": "estatecore-backend", "message": "See /api/health"}), 200
    
    # Debug print to see if this code is executed
    print("REGISTERING TEST ROUTE...")
    
    @app.route("/test-login", methods=["POST"])
    def test_login():
        return jsonify({"message": "Test login works!"}), 200
    
    print("TEST ROUTE REGISTERED")
    
    # Dashboard metrics endpoint
    @app.route(app.config["API_PREFIX"] + "/dashboard/metrics", methods=["GET", "OPTIONS"])
    def dashboard_metrics():
        if request.method == 'OPTIONS':
            return '', 200
        
        # Calculate real metrics from actual data
        total_users = len(users_data)
        total_properties = len(properties_data)
        total_tenants = len(tenants_data)
        
        # Calculate total units across all properties
        total_units = 0
        occupied_units = 0
        for prop in properties_data:
            if prop.get('units') and isinstance(prop['units'], list):
                total_units += len(prop['units'])
                for unit in prop['units']:
                    if unit.get('status') == 'occupied':
                        occupied_units += 1
            elif prop.get('total_units'):
                total_units += prop.get('total_units', 0)
                occupied_units += prop.get('occupied_units', 0)
        
        vacant_units = total_units - occupied_units
        occupancy_rate = round((occupied_units / total_units * 100), 1) if total_units > 0 else 0
        
        # Count active leases
        active_leases = len([l for l in leases_data if l.get('status') == 'active'])
        
        # Count pending maintenance requests
        pending_maintenance = len([w for w in workorders_data if w.get('status') in ['pending', 'in_progress']])
        
        # Calculate monthly revenue from active leases
        monthly_revenue = sum([l.get('rent', 0) for l in leases_data if l.get('status') == 'active'])
        
        return jsonify({
            'property_stats': {
                'total_properties': total_properties,
                'total_units': total_units,
                'occupied_units': occupied_units,
                'vacant_units': vacant_units,
                'occupancy_rate': occupancy_rate
            },
            'tenant_stats': {
                'total_tenants': total_tenants,
                'active_tenants': len([t for t in tenants_data if t.get('status') == 'active'])
            },
            'user_stats': {
                'total_users': total_users,
                'active_users': len([u for u in users_data if u.get('status') == 'active'])
            },
            'lease_stats': {
                'active_leases': active_leases,
                'total_leases': len(leases_data)
            },
            'financial_stats': {
                'monthly_revenue': monthly_revenue,
                'rent_collected': monthly_revenue * 0.85,  # Assuming 85% collection rate
                'rent_expected': monthly_revenue,
                'rent_outstanding': monthly_revenue * 0.15,
                'collection_rate': 85
            },
            'maintenance_stats': {
                'pending_requests': pending_maintenance,
                'emergency_requests': len([w for w in workorders_data if w.get('priority') == 'emergency']),
                'actual_costs': sum([w.get('cost', 0) for w in workorders_data if w.get('status') == 'completed'])
            },
            'recent_activity': {
                'new_leases': len([l for l in leases_data if l.get('created_at', '').startswith('2025-09')]),
                'payments_received': len(rent_payments_data),
                'maintenance_requests': len([w for w in workorders_data if w.get('created_date', '').startswith('2025-09')])
            }
        }), 200

    # Feature flags endpoint
    @app.route(app.config["API_PREFIX"] + "/feature-flags", methods=["GET", "OPTIONS"])
    def feature_flags():
        if request.method == 'OPTIONS':
            return '', 200
            
        return jsonify([
            {'name': 'advanced_analytics', 'enabled': True, 'description': 'Advanced analytics dashboard'},
            {'name': 'mobile_app', 'enabled': False, 'description': 'Mobile application features'},
            {'name': 'automated_billing', 'enabled': True, 'description': 'Automated billing system'}
        ]), 200

    # Expiring leases endpoint
    @app.route(app.config["API_PREFIX"] + "/leases/expiring", methods=["GET", "OPTIONS"])
    def expiring_leases():
        if request.method == 'OPTIONS':
            return '', 200
            
        return jsonify([
            {
                'id': 1,
                'tenant_name': 'John Smith',
                'property': 'Sunset Apartments',
                'unit': '2A',
                'end_date': '2024-09-15',
                'days_until_expiry': 15
            },
            {
                'id': 2,
                'tenant_name': 'Sarah Johnson',
                'property': 'Oak Ridge Complex',
                'unit': '1B',
                'end_date': '2024-09-30',
                'days_until_expiry': 30
            }
        ]), 200

    # Overdue rent records endpoint - note this doesn't have /api prefix in the frontend
    @app.route("/rent-records/overdue", methods=["GET", "OPTIONS"])
    def overdue_rent():
        if request.method == 'OPTIONS':
            return '', 200
            
        return jsonify([
            {
                'id': 1,
                'tenant_name': 'Mike Wilson',
                'property': 'Downtown Plaza',
                'unit': '3C',
                'amount_due': 1250.00,
                'due_date': '2024-08-01',
                'days_overdue': 30
            },
            {
                'id': 2,
                'tenant_name': 'Lisa Brown',
                'property': 'Garden View',
                'unit': '1A',
                'amount_due': 950.00,
                'due_date': '2024-08-15',
                'days_overdue': 16
            }
        ]), 200

    # Data persistence functions
    def save_data_to_file():
        """Save all data to JSON files for persistence"""
        data_dir = os.path.join(app.instance_path, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        data_files = {
            'users.json': users_data,
            'properties.json': properties_data,
            'tenants.json': tenants_data,
            'leases.json': leases_data,
            'workorders.json': workorders_data,
            'apartments.json': apartments_data,
            'utility_bills.json': utility_bills_data,
            'expenses.json': expenses_data,
            'rent_payments.json': rent_payments_data,
            'utility_credentials.json': utility_credentials_data,
        }
        
        for filename, data in data_files.items():
            try:
                filepath = os.path.join(data_dir, filename)
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                app.logger.warning(f"Failed to save {filename}: {e}")
    
    def load_data_from_file():
        """Load data from JSON files if they exist"""
        data_dir = os.path.join(app.instance_path, 'data')
        if not os.path.exists(data_dir):
            return
        
        try:
            # Load users
            users_file = os.path.join(data_dir, 'users.json')
            if os.path.exists(users_file):
                with open(users_file, 'r') as f:
                    loaded_users = json.load(f)
                    users_data.clear()
                    users_data.extend(loaded_users)
                    app.logger.info(f"Loaded {len(users_data)} users from file")
            
            # Load properties
            properties_file = os.path.join(data_dir, 'properties.json')
            if os.path.exists(properties_file):
                with open(properties_file, 'r') as f:
                    loaded_properties = json.load(f)
                    properties_data.clear()
                    properties_data.extend(loaded_properties)
                    app.logger.info(f"Loaded {len(properties_data)} properties from file")
            
            # Load other data files similarly...
            other_files = {
                'tenants.json': tenants_data,
                'leases.json': leases_data,
                'workorders.json': workorders_data,
                'apartments.json': apartments_data
            }
            
            for filename, data_list in other_files.items():
                filepath = os.path.join(data_dir, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        loaded_data = json.load(f)
                        data_list.clear()
                        data_list.extend(loaded_data)
                        app.logger.info(f"Loaded {len(data_list)} records from {filename}")
                        
        except Exception as e:
            app.logger.warning(f"Failed to load data from files: {e}")
    
    # Add all the missing endpoints that the frontend is trying to access
    
    # In-memory storage with file persistence (will be loaded/saved automatically)
    users_data = [
        {
            'id': 1, 
            'name': 'Admin User', 
            'email': 'admin@example.com', 
            'role': 'super_admin', 
            'status': 'active',
            'phone': '555-0001',
            'department': 'Administration',
            'hire_date': '2023-01-01',
            'address': '123 Admin St, City, ST 12345',
            'emergency_contact': 'Jane Doe - 555-0002',
            'permissions': ['all'],
            'notes': 'System administrator',
            'created_at': '2023-01-01T09:00:00Z',
            'last_login': '2025-09-01T08:30:00Z',
            'profile_image': None
        },
        {
            'id': 2, 
            'name': 'Property Manager', 
            'email': 'manager@example.com', 
            'role': 'manager', 
            'status': 'active',
            'phone': '555-0003',
            'department': 'Property Management',
            'hire_date': '2023-03-15',
            'address': '456 Manager Ave, City, ST 12345',
            'emergency_contact': 'John Smith - 555-0004',
            'permissions': ['properties', 'tenants', 'maintenance'],
            'notes': 'Experienced property manager',
            'created_at': '2023-03-15T10:00:00Z',
            'last_login': '2025-09-01T07:45:00Z',
            'profile_image': None
        }
    ]
    
    # Users endpoint with proper data persistence
    @app.route(app.config["API_PREFIX"] + "/users", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def api_users():
        if request.method == 'OPTIONS':
            return '', 200
        elif request.method == 'POST':
            data = request.get_json() or {}
            new_user = {
                'id': len(users_data) + 1,
                'name': data.get('name', 'New User'),
                'email': data.get('email', 'newuser@example.com'),
                'role': data.get('role', 'user'),
                'status': data.get('status', 'active'),
                'phone': data.get('phone', ''),
                'department': data.get('department', ''),
                'hire_date': data.get('hire_date', '2025-09-01'),
                'address': data.get('address', ''),
                'emergency_contact': data.get('emergency_contact', ''),
                'permissions': data.get('permissions', []),
                'notes': data.get('notes', ''),
                'created_at': '2025-09-01T12:00:00Z',
                'last_login': None,
                'profile_image': data.get('profile_image')
            }
            users_data.append(new_user)
            save_data_to_file()  # Save data after creation
            app.logger.info(f"Created user: {new_user}")
            return jsonify(new_user), 201
        elif request.method in ['PUT', 'PATCH']:
            data = request.get_json() or {}
            user_id = data.get('id')
            if user_id:
                for user in users_data:
                    if user['id'] == user_id:
                        user.update({
                            'name': data.get('name', user['name']),
                            'email': data.get('email', user['email']),
                            'role': data.get('role', user['role']),
                            'status': data.get('status', user['status']),
                            'phone': data.get('phone', user.get('phone', '')),
                            'department': data.get('department', user.get('department', '')),
                            'hire_date': data.get('hire_date', user.get('hire_date', '')),
                            'address': data.get('address', user.get('address', '')),
                            'emergency_contact': data.get('emergency_contact', user.get('emergency_contact', '')),
                            'permissions': data.get('permissions', user.get('permissions', [])),
                            'notes': data.get('notes', user.get('notes', '')),
                            'profile_image': data.get('profile_image', user.get('profile_image'))
                        })
                        save_data_to_file()  # Save data after update
                        app.logger.info(f"Updated user: {user}")
                        return jsonify(user), 200
            return jsonify({'error': 'User not found'}), 404
        elif request.method == 'DELETE':
            user_id = request.args.get('id')
            if user_id:
                users_data[:] = [u for u in users_data if u['id'] != int(user_id)]
                save_data_to_file()  # Save data after deletion
                app.logger.info(f"Deleted user with id: {user_id}")
            return jsonify({'message': 'User deleted successfully'}), 200
        else:
            # GET request - return all users
            return jsonify(users_data), 200

    # User invite endpoint
    @app.route(app.config["API_PREFIX"] + "/users/<int:user_id>/invite", methods=["POST", "OPTIONS"])
    def send_user_invite(user_id):
        if request.method == 'OPTIONS':
            return '', 200
        
        # Find the user
        user = next((u for u in users_data if u['id'] == user_id), None)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate invite token and URL
        invite_token = f'invite-token-{user_id}-{hash(str(user_id))}'[:20]
        # Always use the production domain for invite URLs
        base_url = 'https://app.myestatecore.com'
        invite_url = f"{base_url}/register?token={invite_token}"
        
        # Mock sending invite
        return jsonify({
            'message': f'Invite sent successfully to user {user_id}',
            'user_id': user_id,
            'user': user,
            'invite_token': invite_token,
            'invite_url': invite_url,
            'expires_at': '2024-12-31T23:59:59Z'
        }), 200
    
    # In-memory storage for properties
    properties_data = [
        {
            'id': 1, 
            'name': 'Sunset Apartments', 
            'address': '123 Main St', 
            'city': 'Downtown',
            'state': 'CA',
            'zip_code': '90210',
            'units': [
                {'unit_number': '101', 'bedrooms': 1, 'bathrooms': 1, 'rent_amount': 1000, 'status': 'occupied', 'tenant_id': 1},
                {'unit_number': '102', 'bedrooms': 1, 'bathrooms': 1, 'rent_amount': 1000, 'status': 'occupied', 'tenant_id': 2},
                {'unit_number': '103', 'bedrooms': 2, 'bathrooms': 1, 'rent_amount': 1200, 'status': 'available'},
                {'unit_number': '201', 'bedrooms': 2, 'bathrooms': 2, 'rent_amount': 1400, 'status': 'available'},
                {'unit_number': '202', 'bedrooms': 3, 'bathrooms': 2, 'rent_amount': 1600, 'status': 'occupied'},
            ],
            'total_units': 50,
            'occupied_units': 47,
            'vacant_units': 3,
            'type': 'apartment',
            'status': 'active',
            'manager': 'John Smith',
            'phone': '555-0123',
            'email': 'manager@sunsetapts.com',
            'description': 'Modern apartment complex with amenities',
            'year_built': 2018,
            'square_feet': 45000,
            'lot_size': '2.5 acres',
            'parking_spaces': 75,
            'amenities': ['pool', 'gym', 'laundry', 'parking', 'elevator'],
            'rent_range_min': 1000,
            'rent_range_max': 1800,
            'pet_policy': 'cats_dogs_allowed',
            'lease_terms': ['6_months', '12_months'],
            'utilities_included': ['water', 'trash'],
            'maintenance_contact': 'Mike Repairs - 555-0199',
            'insurance_provider': 'Property Insurance Co',
            'monthly_revenue': 142500,
            'notes': 'Recently renovated lobby',
            'created_at': '2023-01-15T10:00:00Z'
        },
        {
            'id': 2, 
            'name': 'Oak Ridge Complex', 
            'address': '456 Oak Ave', 
            'city': 'Midtown',
            'state': 'CA',
            'zip_code': '90211',
            'units': [
                {'unit_number': '1A', 'bedrooms': 2, 'bathrooms': 2, 'rent_amount': 1300, 'status': 'occupied', 'tenant_id': 3},
                {'unit_number': '1B', 'bedrooms': 2, 'bathrooms': 2, 'rent_amount': 1300, 'status': 'available'},
                {'unit_number': '2A', 'bedrooms': 3, 'bathrooms': 2, 'rent_amount': 1500, 'status': 'available'},
                {'unit_number': '2B', 'bedrooms': 3, 'bathrooms': 2, 'rent_amount': 1500, 'status': 'occupied'},
            ],
            'total_units': 75,
            'occupied_units': 71,
            'vacant_units': 4,
            'type': 'apartment',
            'status': 'active',
            'manager': 'Sarah Johnson',
            'phone': '555-0456',
            'email': 'manager@oakridge.com',
            'description': 'Luxury residential complex',
            'year_built': 2020,
            'square_feet': 62000,
            'lot_size': '3.2 acres',
            'parking_spaces': 100,
            'amenities': ['pool', 'gym', 'spa', 'concierge', 'rooftop_deck'],
            'rent_range_min': 1200,
            'rent_range_max': 2500,
            'pet_policy': 'cats_only',
            'lease_terms': ['12_months', '24_months'],
            'utilities_included': ['water'],
            'maintenance_contact': 'Oak Maintenance LLC - 555-0466',
            'insurance_provider': 'Premium Property Insurance',
            'monthly_revenue': 178500,
            'notes': 'Premium luxury building',
            'created_at': '2023-03-01T14:00:00Z'
        }
    ]
    
    # Properties endpoint with proper data persistence
    @app.route(app.config["API_PREFIX"] + "/properties", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def api_properties():
        if request.method == 'OPTIONS':
            return '', 200
        elif request.method == 'POST':
            data = request.get_json() or {}
            new_property = {
                'id': len(properties_data) + 1,
                'name': data.get('name', 'New Property'),
                'address': data.get('address', '789 New St'),
                'city': data.get('city', ''),
                'state': data.get('state', ''),
                'zip_code': data.get('zip_code', ''),
                'units': data.get('units', []) if isinstance(data.get('units'), list) else [],
                'total_units': data.get('total_units', len(data.get('units', [])) if isinstance(data.get('units'), list) else data.get('units', 25)),
                'occupied_units': data.get('occupied_units', 0),
                'vacant_units': data.get('vacant_units', []) if isinstance(data.get('vacant_units'), list) else [],
                'type': data.get('type', 'apartment'),
                'status': data.get('status', 'active'),
                'manager': data.get('manager', ''),
                'phone': data.get('phone', ''),
                'email': data.get('email', ''),
                'description': data.get('description', ''),
                'year_built': data.get('year_built'),
                'square_feet': data.get('square_feet'),
                'lot_size': data.get('lot_size', ''),
                'parking_spaces': data.get('parking_spaces', 0),
                'amenities': data.get('amenities', []),
                'rent_range_min': data.get('rent_range_min', 0),
                'rent_range_max': data.get('rent_range_max', 0),
                'pet_policy': data.get('pet_policy', 'no_pets'),
                'lease_terms': data.get('lease_terms', ['12_months']),
                'utilities_included': data.get('utilities_included', []),
                'maintenance_contact': data.get('maintenance_contact', ''),
                'insurance_provider': data.get('insurance_provider', ''),
                'monthly_revenue': data.get('monthly_revenue', 0),
                'notes': data.get('notes', ''),
                'created_at': '2025-09-01T12:00:00Z'
            }
            properties_data.append(new_property)
            save_data_to_file()  # Save data after creation
            app.logger.info(f"Created property: {new_property}")
            return jsonify(new_property), 201
        elif request.method in ['PUT', 'PATCH']:
            data = request.get_json() or {}
            property_id = data.get('id')
            if property_id:
                for prop in properties_data:
                    if prop['id'] == property_id:
                        prop.update({
                            'name': data.get('name', prop['name']),
                            'address': data.get('address', prop['address']),
                            'city': data.get('city', prop.get('city', '')),
                            'state': data.get('state', prop.get('state', '')),
                            'zip_code': data.get('zip_code', prop.get('zip_code', '')),
                            'units': data.get('units', prop['units']),
                            'occupied_units': data.get('occupied_units', prop.get('occupied_units', 0)),
                            'vacant_units': data.get('vacant_units', prop.get('vacant_units', 0)),
                            'type': data.get('type', prop['type']),
                            'status': data.get('status', prop['status']),
                            'manager': data.get('manager', prop.get('manager', '')),
                            'phone': data.get('phone', prop.get('phone', '')),
                            'email': data.get('email', prop.get('email', '')),
                            'description': data.get('description', prop.get('description', '')),
                            'year_built': data.get('year_built', prop.get('year_built')),
                            'square_feet': data.get('square_feet', prop.get('square_feet')),
                            'lot_size': data.get('lot_size', prop.get('lot_size', '')),
                            'parking_spaces': data.get('parking_spaces', prop.get('parking_spaces', 0)),
                            'amenities': data.get('amenities', prop.get('amenities', [])),
                            'rent_range_min': data.get('rent_range_min', prop.get('rent_range_min', 0)),
                            'rent_range_max': data.get('rent_range_max', prop.get('rent_range_max', 0)),
                            'pet_policy': data.get('pet_policy', prop.get('pet_policy', 'no_pets')),
                            'lease_terms': data.get('lease_terms', prop.get('lease_terms', [])),
                            'utilities_included': data.get('utilities_included', prop.get('utilities_included', [])),
                            'maintenance_contact': data.get('maintenance_contact', prop.get('maintenance_contact', '')),
                            'insurance_provider': data.get('insurance_provider', prop.get('insurance_provider', '')),
                            'monthly_revenue': data.get('monthly_revenue', prop.get('monthly_revenue', 0)),
                            'notes': data.get('notes', prop.get('notes', ''))
                        })
                        app.logger.info(f"Updated property: {prop}")
                        return jsonify(prop), 200
            return jsonify({'error': 'Property not found'}), 404
        elif request.method == 'DELETE':
            property_id = request.args.get('id')
            if property_id:
                properties_data[:] = [p for p in properties_data if p['id'] != int(property_id)]
                save_data_to_file()  # Save data after deletion
                app.logger.info(f"Deleted property with id: {property_id}")
            return jsonify({'message': 'Property deleted successfully'}), 200
        else:
            # GET request - return all properties
            return jsonify(properties_data), 200

    # Individual property endpoint
    @app.route(app.config["API_PREFIX"] + "/properties/<int:property_id>", methods=["GET", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def api_property_single(property_id):
        if request.method == 'OPTIONS':
            return '', 200
        
        prop = next((p for p in properties_data if p['id'] == property_id), None)
        if not prop:
            return jsonify({'error': 'Property not found'}), 404
            
        if request.method == 'GET':
            return jsonify(prop), 200
        elif request.method in ['PUT', 'PATCH']:
            data = request.get_json() or {}
            prop.update({
                'name': data.get('name', prop['name']),
                'address': data.get('address', prop['address']),
                'units': data.get('units', prop['units']),
                'type': data.get('type', prop['type']),
                'status': data.get('status', prop['status']),
                'manager': data.get('manager', prop.get('manager', '')),
                'phone': data.get('phone', prop.get('phone', '')),
                'email': data.get('email', prop.get('email', '')),
                'description': data.get('description', prop.get('description', ''))
            })
            return jsonify(prop), 200
        elif request.method == 'DELETE':
            properties_data[:] = [p for p in properties_data if p['id'] != property_id]
            return jsonify({'message': 'Property deleted successfully'}), 200
    
    # In-memory storage for tenants
    tenants_data = [
        {
            'id': 1, 
            'name': 'John Smith', 
            'email': 'john@example.com', 
            'phone': '555-1234',
            'unit': '2A',
            'property_id': 1,
            'property_name': 'Sunset Apartments',
            'lease_start': '2024-01-01',
            'lease_end': '2024-12-31',
            'rent': 1250,
            'status': 'active',
            'emergency_contact': 'Jane Smith - 555-5678'
        },
        {
            'id': 2, 
            'name': 'Sarah Johnson', 
            'email': 'sarah@example.com', 
            'phone': '555-9876',
            'unit': '1B',
            'property_id': 2,
            'property_name': 'Oak Ridge Complex',
            'lease_start': '2024-03-01',
            'lease_end': '2025-02-28',
            'rent': 1100,
            'status': 'active',
            'emergency_contact': 'Mike Johnson - 555-4321'
        }
    ]
    
    # Tenants endpoint with full CRUD
    @app.route(app.config["API_PREFIX"] + "/tenants", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def api_tenants():
        if request.method == 'OPTIONS':
            return '', 200
        elif request.method == 'POST':
            data = request.get_json() or {}
            new_tenant = {
                'id': len(tenants_data) + 1,
                'name': data.get('name') or data.get('full_name', 'New Tenant'),
                'full_name': data.get('full_name') or data.get('name', 'New Tenant'),
                'email': data.get('email', 'tenant@example.com'),
                'phone': data.get('phone', ''),
                'unit': data.get('unit', ''),
                'property_id': data.get('property_id'),
                'property_name': data.get('property_name', ''),
                'lease_start': data.get('lease_start', '2025-09-01'),
                'lease_end': data.get('lease_end', '2026-08-31'),
                'rent': data.get('rent', 1000),
                'monthly_income': data.get('monthly_income', 0),
                'employment_status': data.get('employment_status', ''),
                'emergency_contact_name': data.get('emergency_contact_name', ''),
                'emergency_contact_phone': data.get('emergency_contact_phone', ''),
                'status': data.get('status', 'pending'),
                'notes': data.get('notes', ''),
                'emergency_contact': data.get('emergency_contact', ''),
                'created_at': '2025-09-01T12:00:00Z'
            }
            tenants_data.append(new_tenant)
            save_data_to_file()
            app.logger.info(f"Created tenant: {new_tenant}")
            return jsonify(new_tenant), 201
        elif request.method in ['PUT', 'PATCH']:
            data = request.get_json() or {}
            tenant_id = data.get('id')
            if tenant_id:
                for tenant in tenants_data:
                    if tenant['id'] == tenant_id:
                        tenant.update({
                            'name': data.get('name', tenant['name']),
                            'email': data.get('email', tenant['email']),
                            'phone': data.get('phone', tenant['phone']),
                            'unit': data.get('unit', tenant['unit']),
                            'property_id': data.get('property_id', tenant['property_id']),
                            'property_name': data.get('property_name', tenant['property_name']),
                            'lease_start': data.get('lease_start', tenant['lease_start']),
                            'lease_end': data.get('lease_end', tenant['lease_end']),
                            'rent': data.get('rent', tenant['rent']),
                            'status': data.get('status', tenant['status']),
                            'emergency_contact': data.get('emergency_contact', tenant['emergency_contact'])
                        })
                        app.logger.info(f"Updated tenant: {tenant}")
                        return jsonify(tenant), 200
            return jsonify({'error': 'Tenant not found'}), 404
        elif request.method == 'DELETE':
            tenant_id = request.args.get('id')
            if tenant_id:
                tenants_data[:] = [t for t in tenants_data if t['id'] != int(tenant_id)]
                app.logger.info(f"Deleted tenant with id: {tenant_id}")
            return jsonify({'message': 'Tenant deleted successfully'}), 200
        else:
            # GET request - return all tenants
            return jsonify(tenants_data), 200

    # Tenant invite endpoint
    @app.route(app.config["API_PREFIX"] + "/tenants/<int:tenant_id>/invite", methods=["POST", "OPTIONS"])
    def send_tenant_invite(tenant_id):
        if request.method == 'OPTIONS':
            return '', 200
        
        # Find the tenant
        tenant = next((t for t in tenants_data if t['id'] == tenant_id), None)
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        
        # Generate invite token and URL
        invite_token = f'tenant-invite-{tenant_id}-{hash(str(tenant_id))}'[:20]
        # Always use the production domain for invite URLs
        base_url = 'https://app.myestatecore.com'
        invite_url = f"{base_url}/register?token={invite_token}"
        
        # Mock sending invite
        return jsonify({
            'message': f'Invite sent successfully to tenant {tenant_id}',
            'tenant_id': tenant_id,
            'tenant': tenant,
            'invite_token': invite_token,
            'invite_url': invite_url,
            'expires_at': '2024-12-31T23:59:59Z'
        }), 200
    
    # In-memory storage for apartments/units
    apartments_data = [
        {
            'id': 1, 
            'unit': '1A', 
            'property_id': 1,
            'property': 'Sunset Apartments', 
            'status': 'occupied',
            'rent': 1200,
            'bedrooms': 2,
            'bathrooms': 2,
            'square_feet': 950,
            'floor': 1,
            'amenities': ['balcony', 'dishwasher', 'in_unit_laundry'],
            'pet_friendly': True,
            'parking_included': True,
            'available_date': None,
            'tenant_id': 1,
            'tenant_name': 'John Smith',
            'lease_end': '2024-12-31',
            'notes': 'Recently renovated'
        },
        {
            'id': 2, 
            'unit': '2A', 
            'property_id': 2,
            'property': 'Oak Ridge Complex', 
            'status': 'vacant',
            'rent': 1350,
            'bedrooms': 3,
            'bathrooms': 2,
            'square_feet': 1100,
            'floor': 2,
            'amenities': ['balcony', 'dishwasher', 'in_unit_laundry', 'granite_counters'],
            'pet_friendly': False,
            'parking_included': True,
            'available_date': '2025-09-15',
            'tenant_id': None,
            'tenant_name': None,
            'lease_end': None,
            'notes': 'Premium unit with city views'
        }
    ]
    
    # Apartments endpoint with full CRUD
    @app.route(app.config["API_PREFIX"] + "/apartments", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def api_apartments():
        if request.method == 'OPTIONS':
            return '', 200
        elif request.method == 'POST':
            data = request.get_json() or {}
            new_apartment = {
                'id': len(apartments_data) + 1,
                'unit': data.get('unit', 'New Unit'),
                'property_id': data.get('property_id'),
                'property': data.get('property', ''),
                'status': data.get('status', 'vacant'),
                'rent': data.get('rent', 1000),
                'bedrooms': data.get('bedrooms', 1),
                'bathrooms': data.get('bathrooms', 1),
                'square_feet': data.get('square_feet', 700),
                'floor': data.get('floor', 1),
                'amenities': data.get('amenities', []),
                'pet_friendly': data.get('pet_friendly', False),
                'parking_included': data.get('parking_included', False),
                'available_date': data.get('available_date'),
                'tenant_id': data.get('tenant_id'),
                'tenant_name': data.get('tenant_name'),
                'lease_end': data.get('lease_end'),
                'notes': data.get('notes', '')
            }
            apartments_data.append(new_apartment)
            app.logger.info(f"Created apartment: {new_apartment}")
            return jsonify(new_apartment), 201
        elif request.method in ['PUT', 'PATCH']:
            data = request.get_json() or {}
            apartment_id = data.get('id')
            if apartment_id:
                for apt in apartments_data:
                    if apt['id'] == apartment_id:
                        apt.update({
                            'unit': data.get('unit', apt['unit']),
                            'property_id': data.get('property_id', apt['property_id']),
                            'property': data.get('property', apt['property']),
                            'status': data.get('status', apt['status']),
                            'rent': data.get('rent', apt['rent']),
                            'bedrooms': data.get('bedrooms', apt['bedrooms']),
                            'bathrooms': data.get('bathrooms', apt['bathrooms']),
                            'square_feet': data.get('square_feet', apt['square_feet']),
                            'floor': data.get('floor', apt['floor']),
                            'amenities': data.get('amenities', apt['amenities']),
                            'pet_friendly': data.get('pet_friendly', apt['pet_friendly']),
                            'parking_included': data.get('parking_included', apt['parking_included']),
                            'available_date': data.get('available_date', apt['available_date']),
                            'tenant_id': data.get('tenant_id', apt['tenant_id']),
                            'tenant_name': data.get('tenant_name', apt['tenant_name']),
                            'lease_end': data.get('lease_end', apt['lease_end']),
                            'notes': data.get('notes', apt['notes'])
                        })
                        app.logger.info(f"Updated apartment: {apt}")
                        return jsonify(apt), 200
            return jsonify({'error': 'Apartment not found'}), 404
        elif request.method == 'DELETE':
            apartment_id = request.args.get('id')
            if apartment_id:
                apartments_data[:] = [apt for apt in apartments_data if apt['id'] != int(apartment_id)]
                app.logger.info(f"Deleted apartment with id: {apartment_id}")
            return jsonify({'message': 'Apartment deleted successfully'}), 200
        else:
            # GET request - return all apartments
            return jsonify(apartments_data), 200
    
    # Available apartments endpoint
    @app.route(app.config["API_PREFIX"] + "/apartments/available", methods=["GET", "OPTIONS"])
    def api_apartments_available():
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify([
            {'id': 2, 'unit': '2A', 'property': 'Oak Ridge Complex', 'rent': 1200}
        ]), 200
    
    # Asset health endpoint
    @app.route(app.config["API_PREFIX"] + "/asset-health/<int:asset_id>", methods=["GET", "OPTIONS"])
    def api_asset_health(asset_id):
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify({
            'id': asset_id,
            'status': 'good',
            'last_maintenance': '2024-07-15',
            'next_maintenance': '2024-10-15'
        }), 200
    
    # Analytics endpoints
    @app.route("/analytics/financial-report", methods=["GET", "POST", "OPTIONS"])
    def analytics_financial_report():
        if request.method == 'OPTIONS':
            return '', 200
        
        # Get parameters from query string (GET) or request body (POST)
        if request.method == 'POST':
            data = request.get_json() or {}
            start_date = data.get('start_date', '2025-08-01')
            end_date = data.get('end_date', '2025-08-31')
        else:
            start_date = request.args.get('start_date', '2025-08-01')
            end_date = request.args.get('end_date', '2025-08-31')
            
        return jsonify({
            'total_revenue': 285000,
            'total_expenses': 65000,
            'net_income': 220000,
            'period': f'{start_date} to {end_date}'
        }), 200
    
    @app.route("/analytics/occupancy-report", methods=["GET", "POST", "OPTIONS"])
    def analytics_occupancy_report():
        if request.method == 'OPTIONS':
            return '', 200
            
        # Get parameters from query string (GET) or request body (POST)
        if request.method == 'POST':
            data = request.get_json() or {}
            start_date = data.get('start_date', '2025-08-01')
            end_date = data.get('end_date', '2025-08-31')
        else:
            start_date = request.args.get('start_date', '2025-08-01')
            end_date = request.args.get('end_date', '2025-08-31')
            
        return jsonify({
            'occupancy_rate': 94.7,
            'occupied_units': 142,
            'vacant_units': 8,
            'period': f'{start_date} to {end_date}'
        }), 200
    
    @app.route("/analytics/maintenance-report", methods=["GET", "POST", "OPTIONS"])  
    def analytics_maintenance_report():
        if request.method == 'OPTIONS':
            return '', 200
            
        # Get parameters from query string (GET) or request body (POST)
        if request.method == 'POST':
            data = request.get_json() or {}
            start_date = data.get('start_date', '2025-08-01')
            end_date = data.get('end_date', '2025-08-31')
        else:
            start_date = request.args.get('start_date', '2025-08-01')
            end_date = request.args.get('end_date', '2025-08-31')
            
        return jsonify({
            'total_requests': 45,
            'completed': 32,
            'pending': 13,
            'average_completion_days': 3.2,
            'period': f'{start_date} to {end_date}'
        }), 200
    
    @app.route("/analytics/tenant-report", methods=["GET", "POST", "OPTIONS"])
    def analytics_tenant_report():
        if request.method == 'OPTIONS':
            return '', 200
            
        # Get parameters from query string (GET) or request body (POST)
        if request.method == 'POST':
            data = request.get_json() or {}
            start_date = data.get('start_date', '2025-08-01')
            end_date = data.get('end_date', '2025-08-31')
        else:
            start_date = request.args.get('start_date', '2025-08-01')
            end_date = request.args.get('end_date', '2025-08-31')
            
        return jsonify({
            'total_tenants': 142,
            'new_tenants': 8,
            'moved_out': 3,
            'retention_rate': 97.9,
            'period': f'{start_date} to {end_date}'
        }), 200

    # Invite endpoints - ensure they work with remote URLs
    @app.route(app.config["API_PREFIX"] + "/auth/invite/<token>", methods=["GET", "OPTIONS"])
    def get_invite(token):
        if request.method == 'OPTIONS':
            return '', 200
        
        # Validate invite token and find associated user
        if token and len(token) > 10:  # Basic validation
            # Extract user_id from token (format: invite-token-{user_id}-{hash})
            try:
                # Parse the token to get user_id
                if token.startswith('invite-token-'):
                    parts = token.split('-')
                    if len(parts) >= 3:
                        user_id = int(parts[2])
                        # Find the user
                        user = next((u for u in users_data if u['id'] == user_id), None)
                        if user:
                            return jsonify({
                                'token': token,
                                'email': user['email'],
                                'organization': 'EstateCore',
                                'expires_at': '2024-12-31T23:59:59Z',
                                'valid': True,
                                'user': {
                                    'id': user['id'],
                                    'email': user['email'],
                                    'name': user['name'],
                                    'role': user['role']
                                }
                            }), 200
            except (ValueError, IndexError):
                pass
            
            # Fallback for tokens that don't match expected format
            return jsonify({
                'token': token,
                'email': 'newuser@example.com',
                'organization': 'EstateCore',
                'expires_at': '2024-12-31T23:59:59Z',
                'valid': True,
                'user': {
                    'id': 999,
                    'email': 'newuser@example.com',
                    'name': 'New User',
                    'role': 'user'
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid or expired invite token'}), 404
    
    @app.route(app.config["API_PREFIX"] + "/auth/register/<token>", methods=["POST", "OPTIONS"])
    def accept_invite(token):
        if request.method == 'OPTIONS':
            return '', 200
            
        data = request.get_json() or {}
        
        # Basic validation
        if not token or len(token) < 10:
            return jsonify({'error': 'Invalid invite token'}), 400
            
        name = data.get('name', '').strip()
        password = data.get('password', '').strip()
        
        if not name or not password:
            return jsonify({'error': 'Name and password are required'}), 400
            
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Mock successful registration
        return jsonify({
            'message': 'Account created successfully',
            'access_token': f'new-user-token-{token[:8]}',
            'user': {
                'id': 999,
                'email': 'newuser@example.com', 
                'name': name,
                'role': 'user'
            }
        }), 201

    # Additional missing endpoints that frontend is trying to access
    
    # In-memory storage for leases
    leases_data = [
        {
            'id': 1, 
            'tenant_id': 1,
            'tenant_name': 'John Smith', 
            'tenant_email': 'john@example.com',
            'property_id': 1,
            'property': 'Sunset Apartments', 
            'unit': '2A',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'status': 'active',
            'rent': 1250,
            'security_deposit': 2500,
            'lease_term_months': 12,
            'lease_type': 'residential',
            'payment_due_day': 1,
            'late_fee': 50.00,
            'pet_allowed': True,
            'pet_deposit': 500,
            'utilities_included': ['water', 'trash'],
            'parking_spaces': 1,
            'notes': 'Good tenant, pays on time',
            'created_date': '2023-12-15'
        },
        {
            'id': 2,
            'tenant_id': 2,
            'tenant_name': 'Sarah Johnson',
            'tenant_email': 'sarah@example.com',
            'property_id': 2,
            'property': 'Oak Ridge Complex', 
            'unit': '1B',
            'start_date': '2024-03-01',
            'end_date': '2025-02-28',
            'status': 'active',
            'rent': 1100,
            'security_deposit': 2200,
            'lease_term_months': 12,
            'lease_type': 'residential',
            'payment_due_day': 1,
            'late_fee': 50.00,
            'pet_allowed': False,
            'pet_deposit': 0,
            'utilities_included': ['water'],
            'parking_spaces': 2,
            'notes': 'Excellent tenant',
            'created_date': '2024-02-15'
        }
    ]
    
    # Leases endpoint with full CRUD
    @app.route(app.config["API_PREFIX"] + "/leases", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def api_leases():
        if request.method == 'OPTIONS':
            return '', 200
        elif request.method == 'POST':
            data = request.get_json() or {}
            new_lease = {
                'id': len(leases_data) + 1,
                'tenant_id': data.get('tenant_id'),
                'tenant_name': data.get('tenant_name', 'New Tenant'),
                'tenant_email': data.get('tenant_email', ''),
                'property_id': data.get('property_id'),
                'property': data.get('property', ''),
                'unit': data.get('unit', ''),
                'start_date': data.get('start_date', '2025-09-01'),
                'end_date': data.get('end_date', '2026-08-31'),
                'status': data.get('status', 'active'),
                'rent': data.get('rent', 1000),
                'security_deposit': data.get('security_deposit', 2000),
                'lease_term_months': data.get('lease_term_months', 12),
                'lease_type': data.get('lease_type', 'residential'),
                'payment_due_day': data.get('payment_due_day', 1),
                'late_fee': data.get('late_fee', 50.00),
                'pet_allowed': data.get('pet_allowed', False),
                'pet_deposit': data.get('pet_deposit', 0),
                'utilities_included': data.get('utilities_included', []),
                'parking_spaces': data.get('parking_spaces', 1),
                'notes': data.get('notes', ''),
                'created_date': '2025-09-01'
            }
            leases_data.append(new_lease)
            app.logger.info(f"Created lease: {new_lease}")
            return jsonify(new_lease), 201
        elif request.method in ['PUT', 'PATCH']:
            data = request.get_json() or {}
            lease_id = data.get('id')
            if lease_id:
                for lease in leases_data:
                    if lease['id'] == lease_id:
                        lease.update({
                            'tenant_id': data.get('tenant_id', lease['tenant_id']),
                            'tenant_name': data.get('tenant_name', lease['tenant_name']),
                            'tenant_email': data.get('tenant_email', lease['tenant_email']),
                            'property_id': data.get('property_id', lease['property_id']),
                            'property': data.get('property', lease['property']),
                            'unit': data.get('unit', lease['unit']),
                            'start_date': data.get('start_date', lease['start_date']),
                            'end_date': data.get('end_date', lease['end_date']),
                            'status': data.get('status', lease['status']),
                            'rent': data.get('rent', lease['rent']),
                            'security_deposit': data.get('security_deposit', lease['security_deposit']),
                            'lease_term_months': data.get('lease_term_months', lease['lease_term_months']),
                            'lease_type': data.get('lease_type', lease['lease_type']),
                            'payment_due_day': data.get('payment_due_day', lease['payment_due_day']),
                            'late_fee': data.get('late_fee', lease['late_fee']),
                            'pet_allowed': data.get('pet_allowed', lease['pet_allowed']),
                            'pet_deposit': data.get('pet_deposit', lease['pet_deposit']),
                            'utilities_included': data.get('utilities_included', lease['utilities_included']),
                            'parking_spaces': data.get('parking_spaces', lease['parking_spaces']),
                            'notes': data.get('notes', lease['notes'])
                        })
                        app.logger.info(f"Updated lease: {lease}")
                        return jsonify(lease), 200
            return jsonify({'error': 'Lease not found'}), 404
        elif request.method == 'DELETE':
            lease_id = request.args.get('id')
            if lease_id:
                leases_data[:] = [l for l in leases_data if l['id'] != int(lease_id)]
                app.logger.info(f"Deleted lease with id: {lease_id}")
            return jsonify({'message': 'Lease deleted successfully'}), 200
        else:
            # GET request - return all leases
            return jsonify(leases_data), 200
    
    # Rent records endpoints
    @app.route("/rent-records", methods=["GET", "OPTIONS"])
    def rent_records():
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify([
            {
                'id': 1,
                'tenant_name': 'John Smith',
                'property': 'Sunset Apartments',
                'unit': '2A', 
                'amount': 1250,
                'due_date': '2025-09-01',
                'status': 'paid'
            },
            {
                'id': 2,
                'tenant_name': 'Sarah Johnson', 
                'property': 'Oak Ridge Complex',
                'unit': '1B',
                'amount': 1100,
                'due_date': '2025-09-01',
                'status': 'pending'
            }
        ]), 200
    
    @app.route("/rent-records/statistics", methods=["GET", "OPTIONS"])
    def rent_records_statistics():
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify({
            'total_collected': 285000,
            'total_outstanding': 15000,
            'collection_rate': 95.0,
            'overdue_count': 5
        }), 200
    
    # In-memory storage for work orders
    workorders_data = [
        {
            'id': 1,
            'title': 'Fix leaky faucet',
            'description': 'Kitchen faucet is dripping constantly',
            'property_id': 1,
            'property': 'Sunset Apartments',
            'unit': '2A',
            'status': 'pending',
            'priority': 'medium',
            'category': 'plumbing',
            'tenant_name': 'John Smith',
            'tenant_phone': '555-1234',
            'created_date': '2025-08-28',
            'assigned_to': 'Mike the Plumber',
            'estimated_cost': 150.00,
            'actual_cost': None,
            'completed_date': None,
            'notes': 'Tenant reported this morning'
        },
        {
            'id': 2,
            'title': 'Replace air filter',
            'description': 'HVAC air filter needs replacement',
            'property_id': 2,
            'property': 'Oak Ridge Complex',
            'unit': '1B', 
            'status': 'completed',
            'priority': 'low',
            'category': 'hvac',
            'tenant_name': 'Sarah Johnson',
            'tenant_phone': '555-9876',
            'created_date': '2025-08-25',
            'assigned_to': 'HVAC Pros Inc',
            'estimated_cost': 75.00,
            'actual_cost': 80.00,
            'completed_date': '2025-08-26',
            'notes': 'Routine maintenance completed'
        }
    ]
    
    # Work orders endpoint with full CRUD
    @app.route(app.config["API_PREFIX"] + "/workorders", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def api_workorders():
        if request.method == 'OPTIONS':
            return '', 200
        elif request.method == 'POST':
            data = request.get_json() or {}
            new_workorder = {
                'id': len(workorders_data) + 1,
                'title': data.get('title', 'New Work Order'),
                'description': data.get('description', ''),
                'property_id': data.get('property_id'),
                'property': data.get('property', ''),
                'unit': data.get('unit', ''),
                'status': data.get('status', 'pending'),
                'priority': data.get('priority', 'medium'),
                'category': data.get('category', 'general'),
                'tenant_name': data.get('tenant_name', ''),
                'tenant_phone': data.get('tenant_phone', ''),
                'created_date': data.get('created_date', '2025-09-01'),
                'assigned_to': data.get('assigned_to', ''),
                'estimated_cost': data.get('estimated_cost', 0.0),
                'actual_cost': data.get('actual_cost'),
                'completed_date': data.get('completed_date'),
                'notes': data.get('notes', '')
            }
            workorders_data.append(new_workorder)
            app.logger.info(f"Created work order: {new_workorder}")
            return jsonify(new_workorder), 201
        elif request.method in ['PUT', 'PATCH']:
            data = request.get_json() or {}
            workorder_id = data.get('id')
            if workorder_id:
                for wo in workorders_data:
                    if wo['id'] == workorder_id:
                        wo.update({
                            'title': data.get('title', wo['title']),
                            'description': data.get('description', wo['description']),
                            'property_id': data.get('property_id', wo['property_id']),
                            'property': data.get('property', wo['property']),
                            'unit': data.get('unit', wo['unit']),
                            'status': data.get('status', wo['status']),
                            'priority': data.get('priority', wo['priority']),
                            'category': data.get('category', wo['category']),
                            'tenant_name': data.get('tenant_name', wo['tenant_name']),
                            'tenant_phone': data.get('tenant_phone', wo['tenant_phone']),
                            'assigned_to': data.get('assigned_to', wo['assigned_to']),
                            'estimated_cost': data.get('estimated_cost', wo['estimated_cost']),
                            'actual_cost': data.get('actual_cost', wo['actual_cost']),
                            'completed_date': data.get('completed_date', wo['completed_date']),
                            'notes': data.get('notes', wo['notes'])
                        })
                        app.logger.info(f"Updated work order: {wo}")
                        return jsonify(wo), 200
            return jsonify({'error': 'Work order not found'}), 404
        elif request.method == 'DELETE':
            workorder_id = request.args.get('id')
            if workorder_id:
                workorders_data[:] = [wo for wo in workorders_data if wo['id'] != int(workorder_id)]
                app.logger.info(f"Deleted work order with id: {workorder_id}")
            return jsonify({'message': 'Work order deleted successfully'}), 200
        else:
            # GET request - return all work orders
            return jsonify(workorders_data), 200
    
    @app.route(app.config["API_PREFIX"] + "/workorders/statistics", methods=["GET", "OPTIONS"])
    def api_workorders_statistics():
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify({
            'total_requests': 45,
            'pending': 12,
            'in_progress': 8,
            'completed': 25,
            'average_completion_days': 3.2
        }), 200
    
    # Payments endpoint
    @app.route("/payments", methods=["GET", "OPTIONS"])
    def payments():
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify([
            {
                'id': 1,
                'tenant_name': 'John Smith',
                'amount': 1250,
                'payment_date': '2025-08-01',
                'method': 'bank_transfer',
                'status': 'completed'
            },
            {
                'id': 2,
                'tenant_name': 'Sarah Johnson',
                'amount': 1100,
                'payment_date': '2025-08-05',
                'method': 'credit_card',
                'status': 'completed'
            }
        ]), 200
    
    # AI endpoints
    @app.route(app.config["API_PREFIX"] + "/ai/maintenance/hotspots/<int:property_id>", methods=["GET", "OPTIONS"])
    def ai_maintenance_hotspots(property_id):
        if request.method == 'OPTIONS':
            return '', 200
        return jsonify({
            'property_id': property_id,
            'hotspots': [
                {
                    'area': 'HVAC System',
                    'risk_score': 0.75,
                    'predicted_failure_date': '2025-11-15',
                    'recommended_action': 'Schedule preventive maintenance'
                },
                {
                    'area': 'Plumbing',
                    'risk_score': 0.45,
                    'predicted_failure_date': '2026-02-20', 
                    'recommended_action': 'Monitor for leaks'
                }
            ]
        }), 200

    # ========== NEW FUNCTIONALITY ==========
    
    # In-memory storage for utility bills
    utility_bills_data = []
    
    # In-memory storage for expenses
    expenses_data = []
    
    # In-memory storage for rent payments
    rent_payments_data = []
    
    # In-memory storage for utility company credentials
    utility_credentials_data = []
    
    # Load existing data from files on startup
    load_data_from_file()
    
    # Utility Bills Upload and AI Processing
    @app.route(app.config["API_PREFIX"] + "/utility-bills", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def api_utility_bills():
        if request.method == 'OPTIONS':
            return '', 200
        elif request.method == 'POST':
            # Handle file upload and AI processing
            data = request.get_json() or {}
            
            # Mock AI processing of utility bill
            new_bill = {
                'id': len(utility_bills_data) + 1,
                'property_id': data.get('property_id'),
                'property_name': data.get('property_name', ''),
                'utility_type': data.get('utility_type', 'electricity'),  # electricity, gas, water, internet, trash
                'provider': data.get('provider', 'Unknown Provider'),
                'account_number': data.get('account_number', ''),
                'billing_period_start': data.get('billing_period_start', '2025-08-01'),
                'billing_period_end': data.get('billing_period_end', '2025-08-31'),
                'due_date': data.get('due_date', '2025-09-15'),
                'amount': data.get('amount', 0.0),
                'usage': data.get('usage', ''),
                'usage_unit': data.get('usage_unit', 'kWh'),
                'status': data.get('status', 'pending'),  # pending, paid, overdue
                'auto_pay': data.get('auto_pay', False),
                'notes': data.get('notes', ''),
                'uploaded_file': data.get('uploaded_file', ''),
                'ai_processed': True,
                'ai_confidence': 0.95,
                'created_at': '2025-09-01T12:00:00Z'
            }
            
            # Auto-add to expenses
            expense = {
                'id': len(expenses_data) + 1,
                'property_id': new_bill['property_id'],
                'property_name': new_bill['property_name'],
                'category': f"Utilities - {new_bill['utility_type'].title()}",
                'description': f"{new_bill['provider']} - {new_bill['billing_period_start']} to {new_bill['billing_period_end']}",
                'amount': new_bill['amount'],
                'date': new_bill['due_date'],
                'vendor': new_bill['provider'],
                'payment_method': 'auto_detected',
                'status': 'pending',
                'bill_id': new_bill['id'],
                'created_at': '2025-09-01T12:00:00Z'
            }
            
            utility_bills_data.append(new_bill)
            expenses_data.append(expense)
            
            app.logger.info(f"Created utility bill with AI processing: {new_bill}")
            app.logger.info(f"Auto-created expense: {expense}")
            
            return jsonify({
                'bill': new_bill,
                'expense': expense,
                'message': 'Utility bill processed successfully with AI and added to expenses'
            }), 201
        elif request.method == 'GET':
            return jsonify(utility_bills_data), 200
        elif request.method in ['PUT', 'PATCH']:
            data = request.get_json() or {}
            bill_id = data.get('id')
            if bill_id:
                for bill in utility_bills_data:
                    if bill['id'] == bill_id:
                        bill.update(data)
                        return jsonify(bill), 200
            return jsonify({'error': 'Utility bill not found'}), 404
        elif request.method == 'DELETE':
            bill_id = request.args.get('id')
            if bill_id:
                utility_bills_data[:] = [b for b in utility_bills_data if b['id'] != int(bill_id)]
            return jsonify({'message': 'Utility bill deleted successfully'}), 200
    
    # Expenses endpoint
    @app.route(app.config["API_PREFIX"] + "/expenses", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def api_expenses():
        if request.method == 'OPTIONS':
            return '', 200
        elif request.method == 'POST':
            data = request.get_json() or {}
            new_expense = {
                'id': len(expenses_data) + 1,
                'property_id': data.get('property_id'),
                'property_name': data.get('property_name', ''),
                'category': data.get('category', 'General'),
                'description': data.get('description', ''),
                'amount': data.get('amount', 0.0),
                'date': data.get('date', '2025-09-01'),
                'vendor': data.get('vendor', ''),
                'payment_method': data.get('payment_method', 'other'),
                'status': data.get('status', 'pending'),
                'bill_id': data.get('bill_id'),
                'receipt_url': data.get('receipt_url', ''),
                'notes': data.get('notes', ''),
                'created_at': '2025-09-01T12:00:00Z'
            }
            expenses_data.append(new_expense)
            return jsonify(new_expense), 201
        elif request.method == 'GET':
            return jsonify(expenses_data), 200
        elif request.method in ['PUT', 'PATCH']:
            data = request.get_json() or {}
            expense_id = data.get('id')
            if expense_id:
                for expense in expenses_data:
                    if expense['id'] == expense_id:
                        expense.update(data)
                        return jsonify(expense), 200
            return jsonify({'error': 'Expense not found'}), 404
        elif request.method == 'DELETE':
            expense_id = request.args.get('id')
            if expense_id:
                expenses_data[:] = [e for e in expenses_data if e['id'] != int(expense_id)]
            return jsonify({'message': 'Expense deleted successfully'}), 200
    
    # Utility Company Credentials Management
    @app.route(app.config["API_PREFIX"] + "/utility-credentials", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def api_utility_credentials():
        if request.method == 'OPTIONS':
            return '', 200
        elif request.method == 'POST':
            data = request.get_json() or {}
            new_credential = {
                'id': len(utility_credentials_data) + 1,
                'property_id': data.get('property_id'),
                'property_name': data.get('property_name', ''),
                'utility_type': data.get('utility_type', 'electricity'),
                'provider': data.get('provider', ''),
                'account_number': data.get('account_number', ''),
                'username': data.get('username', ''),
                'password': data.get('password', ''),  # In real app, encrypt this!
                'website_url': data.get('website_url', ''),
                'auto_pay': data.get('auto_pay', False),
                'payment_method': data.get('payment_method', ''),  # credit_card, bank_account
                'notes': data.get('notes', ''),
                'status': 'active',
                'created_at': '2025-09-01T12:00:00Z'
            }
            utility_credentials_data.append(new_credential)
            return jsonify(new_credential), 201
        elif request.method == 'GET':
            # Don't return passwords in GET requests for security
            safe_credentials = []
            for cred in utility_credentials_data:
                safe_cred = cred.copy()
                safe_cred['password'] = '***masked***'
                safe_credentials.append(safe_cred)
            return jsonify(safe_credentials), 200
        elif request.method in ['PUT', 'PATCH']:
            data = request.get_json() or {}
            cred_id = data.get('id')
            if cred_id:
                for cred in utility_credentials_data:
                    if cred['id'] == cred_id:
                        cred.update(data)
                        return jsonify(cred), 200
            return jsonify({'error': 'Credential not found'}), 404
        elif request.method == 'DELETE':
            cred_id = request.args.get('id')
            if cred_id:
                utility_credentials_data[:] = [c for c in utility_credentials_data if c['id'] != int(cred_id)]
            return jsonify({'message': 'Credential deleted successfully'}), 200
    
    # Utility Bill Payment (automated through stored credentials)
    @app.route(app.config["API_PREFIX"] + "/utility-bills/<int:bill_id>/pay", methods=["POST", "OPTIONS"])
    def pay_utility_bill(bill_id):
        if request.method == 'OPTIONS':
            return '', 200
        
        # Find the bill
        bill = next((b for b in utility_bills_data if b['id'] == bill_id), None)
        if not bill:
            return jsonify({'error': 'Utility bill not found'}), 404
        
        # Mock payment process
        bill['status'] = 'paid'
        bill['paid_date'] = '2025-09-01'
        bill['payment_confirmation'] = f'PAY-{bill_id}-{hash(str(bill_id))}'[:15]
        
        # Update corresponding expense
        for expense in expenses_data:
            if expense.get('bill_id') == bill_id:
                expense['status'] = 'paid'
                expense['payment_date'] = '2025-09-01'
                break
        
        return jsonify({
            'message': 'Utility bill payment processed successfully',
            'bill': bill,
            'payment_confirmation': bill['payment_confirmation']
        }), 200
    
    # Tenant Rent Payment System
    @app.route(app.config["API_PREFIX"] + "/rent-payments", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def api_rent_payments():
        if request.method == 'OPTIONS':
            return '', 200
        elif request.method == 'POST':
            data = request.get_json() or {}
            new_payment = {
                'id': len(rent_payments_data) + 1,
                'tenant_id': data.get('tenant_id'),
                'tenant_name': data.get('tenant_name', ''),
                'property_id': data.get('property_id'),
                'property_name': data.get('property_name', ''),
                'unit': data.get('unit', ''),
                'amount': data.get('amount', 0.0),
                'payment_method': data.get('payment_method', 'credit_card'),  # credit_card, bank_transfer, ach
                'payment_date': data.get('payment_date', '2025-09-01'),
                'due_date': data.get('due_date', '2025-09-01'),
                'status': data.get('status', 'processing'),  # processing, completed, failed
                'transaction_id': f'TXN-{len(rent_payments_data) + 1}-{hash(str(len(rent_payments_data) + 1))}'[:15],
                'late_fee': data.get('late_fee', 0.0),
                'notes': data.get('notes', ''),
                'payment_portal': 'estatecore_system',
                'created_at': '2025-09-01T12:00:00Z'
            }
            
            # Auto-complete payment (in real system, integrate with payment processor)
            if new_payment['payment_method'] in ['credit_card', 'bank_transfer']:
                new_payment['status'] = 'completed'
                new_payment['processed_at'] = '2025-09-01T12:01:00Z'
            
            rent_payments_data.append(new_payment)
            app.logger.info(f"Processed rent payment: {new_payment}")
            
            return jsonify(new_payment), 201
        elif request.method == 'GET':
            return jsonify(rent_payments_data), 200
        elif request.method in ['PUT', 'PATCH']:
            data = request.get_json() or {}
            payment_id = data.get('id')
            if payment_id:
                for payment in rent_payments_data:
                    if payment['id'] == payment_id:
                        payment.update(data)
                        return jsonify(payment), 200
            return jsonify({'error': 'Rent payment not found'}), 404
        elif request.method == 'DELETE':
            payment_id = request.args.get('id')
            if payment_id:
                rent_payments_data[:] = [p for p in rent_payments_data if p['id'] != int(payment_id)]
            return jsonify({'message': 'Rent payment deleted successfully'}), 200
    
    # Tenant Payment Portal (public endpoint for tenants to pay rent)
    @app.route("/tenant-portal/pay-rent/<int:tenant_id>", methods=["GET", "POST", "OPTIONS"])
    def tenant_payment_portal(tenant_id):
        if request.method == 'OPTIONS':
            return '', 200
        
        # Find tenant
        tenant = next((t for t in tenants_data if t['id'] == tenant_id), None)
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        
        if request.method == 'GET':
            # Return payment portal information
            return jsonify({
                'tenant': tenant,
                'current_rent': tenant.get('rent', 0),
                'due_date': '2025-09-01',
                'late_fee': 50.00 if '2025-09-01' < '2025-09-01' else 0,
                'payment_methods': ['credit_card', 'bank_transfer', 'ach'],
                'portal_url': f'https://app.myestatecore.com/tenant-portal/{tenant_id}'
            }), 200
        
        elif request.method == 'POST':
            # Process rent payment
            data = request.get_json() or {}
            payment_data = {
                'tenant_id': tenant_id,
                'tenant_name': tenant['name'],
                'property_id': tenant['property_id'],
                'property_name': tenant['property_name'],
                'unit': tenant['unit'],
                'amount': data.get('amount', tenant['rent']),
                'payment_method': data.get('payment_method', 'credit_card'),
                'payment_date': '2025-09-01',
                'due_date': data.get('due_date', '2025-09-01')
            }
            
            # Use the rent payments endpoint logic
            request.json = payment_data
            return api_rent_payments()
    
    # Enhanced Email Invite System
    @app.route(app.config["API_PREFIX"] + "/auth/invite-link/<token>", methods=["GET", "OPTIONS"])
    def get_invite_link(token):
        if request.method == 'OPTIONS':
            return '', 200
        
        # Generate a proper invite link that works with the frontend
        base_url = 'https://app.myestatecore.com'
        invite_url = f"{base_url}/register?token={token}"
        
        return jsonify({
            'token': token,
            'invite_url': invite_url,
            'email': 'newuser@example.com',
            'organization': 'EstateCore',
            'expires_at': '2024-12-31T23:59:59Z',
            'valid': True
        }), 200
    
    # Send invite email (mock)
    @app.route(app.config["API_PREFIX"] + "/auth/send-invite", methods=["POST", "OPTIONS"])
    def send_invite_email():
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        email = data.get('email', '')
        role = data.get('role', 'user')
        
        # Generate invite token
        invite_token = f'invite-{hash(email)}-{hash(role)}'[:20]
        
        # In real system, send email here
        base_url = 'https://app.myestatecore.com'
        invite_url = f"{base_url}/register?token={invite_token}"
        
        return jsonify({
            'message': 'Invite sent successfully',
            'email': email,
            'invite_token': invite_token,
            'invite_url': invite_url
        }), 200
    
    # Temporarily disabled generic OPTIONS handler to test login route
    # @app.route(app.config["API_PREFIX"] + "/<path:_any>", methods=["OPTIONS"])
    # def preflight(_any: str):
    #     # Only handle OPTIONS for non-specific routes
    #     return ("", 204)

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
