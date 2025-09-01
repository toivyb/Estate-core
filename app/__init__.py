from flask import Flask, request
from flask_cors import CORS
from .extensions import db, jwt

# Import only the auth blueprint which contains most functionality
try:
    from estatecore_backend.routes.auth import auth_bp
except ImportError as e:
    print(f"Could not import auth_bp: {e}")
    auth_bp = None

def create_app():
    app = Flask(__name__)
    app.config.from_object("estatecore_backend.config.Config")  # make sure config exists

    # Configure CORS to handle all API routes and preflight requests
    CORS(app, 
         resources={
             r"/api/*": {
                 "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174"],
                 "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "ngrok-skip-browser-warning", "X-Requested-With"]
             }
         },
         supports_credentials=True)

    # Initialize extensions
    db.init_app(app)
    if jwt:
        jwt.init_app(app)

    # Register blueprints - auth blueprint has /api prefix built-in
    if auth_bp:
        app.register_blueprint(auth_bp)
        print("Successfully registered auth blueprint")
    else:
        print("Failed to register auth blueprint - not available")

    # Debug route to list all registered routes
    @app.route('/debug/routes')
    def list_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': rule.rule
            })
        return {'routes': routes}

    # Temporary direct login route for testing
    @app.route('/api/login', methods=['POST', 'OPTIONS'])
    def direct_login():
        if request.method == 'OPTIONS':
            # Handle CORS preflight
            response = app.response_class()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
            response.headers.add('Access-Control-Allow-Methods', "GET,POST,OPTIONS")
            return response
            
        # Simple login logic for testing
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')
        
        if email == 'admin@example.com' and password == 'SecureAdmin123!':
            return {
                'access_token': 'test-token-12345',
                'user': {
                    'id': 1,
                    'email': email,
                    'name': 'Admin User',
                    'role': 'super_admin'
                }
            }
        else:
            return {'message': 'Invalid credentials'}, 401

    # Dashboard metrics endpoint
    @app.route('/api/dashboard/metrics', methods=['GET', 'OPTIONS'])
    def dashboard_metrics():
        if request.method == 'OPTIONS':
            response = app.response_class()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
            response.headers.add('Access-Control-Allow-Methods', "GET,OPTIONS")
            return response
        
        return {
            'total_properties': 25,
            'total_units': 150,
            'occupied_units': 142,
            'vacant_units': 8,
            'occupancy_rate': 94.7,
            'total_tenants': 142,
            'monthly_revenue': 285000,
            'pending_maintenance': 12,
            'overdue_rent': 5
        }

    # Feature flags endpoint
    @app.route('/api/feature-flags', methods=['GET', 'OPTIONS'])
    def feature_flags():
        if request.method == 'OPTIONS':
            response = app.response_class()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
            response.headers.add('Access-Control-Allow-Methods', "GET,OPTIONS")
            return response
        
        return [
            {'name': 'advanced_analytics', 'enabled': True, 'description': 'Advanced analytics dashboard'},
            {'name': 'mobile_app', 'enabled': False, 'description': 'Mobile application features'},
            {'name': 'automated_billing', 'enabled': True, 'description': 'Automated billing system'}
        ]

    # Expiring leases endpoint
    @app.route('/api/leases/expiring', methods=['GET', 'OPTIONS'])
    def expiring_leases():
        if request.method == 'OPTIONS':
            response = app.response_class()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
            response.headers.add('Access-Control-Allow-Methods', "GET,OPTIONS")
            return response
        
        return [
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
        ]

    # Overdue rent records endpoint
    @app.route('/rent-records/overdue', methods=['GET', 'OPTIONS'])
    def overdue_rent():
        if request.method == 'OPTIONS':
            response = app.response_class()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
            response.headers.add('Access-Control-Allow-Methods', "GET,OPTIONS")
            return response
        
        return [
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
        ]

    return app
