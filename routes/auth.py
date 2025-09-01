# routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, get_jwt
from werkzeug.security import check_password_hash, generate_password_hash
from secrets import token_urlsafe
from datetime import datetime, timedelta
import os
from functools import wraps
import re

# Single blueprint for all API routes under /api
auth_bp = Blueprint("auth", __name__, url_prefix="/api")

# ---------------- In-memory stores (DEV only) ----------------
# Initial admin user with hashed password
_USERS = [
    {
        "id": 1, 
        "email": "admin@example.com", 
        "name": "Admin", 
        "role": "super_admin", 
        "status": "active",
        "password_hash": generate_password_hash("SecureAdmin123!"),
        "created_at": datetime.utcnow().isoformat(),
        "last_login": None,
        "failed_attempts": 0,
        "locked_until": None
    },
]
_NEXT_UID = 2

_FLAGS = {
    "ai_lease_scoring": True,
    "maintenance_prediction": True,
}

_INVITES = {}  # token -> {"user_id": int, "email": str, "created_at": str}

_TENANTS = []
_NEXT_TID = 1

_PROPERTIES = []
_NEXT_PID = 1

_APARTMENTS = []
_NEXT_AID = 1

_LEASES = []
_NEXT_LID = 1

_WORKORDERS = []
_NEXT_WID = 1

_PAYMENTS = []
_NEXT_PAYID = 1

_AUDIT = []          # each: {"ts","actor","action","target","meta"}
_MAX_AUDIT = 5000

FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://127.0.0.1:5173")


# ---------------- Helpers ----------------
def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _invite_url(token: str) -> str:
    return f"{FRONTEND_BASE_URL}/register?token={token}"


def _record(action: str, actor: str = "system", target: str = "", meta: dict = None):
    _AUDIT.append(
        {"ts": _now_iso(), "actor": actor, "action": action, "target": target, "meta": meta or {}}
    )
    # keep last N
    if len(_AUDIT) > _MAX_AUDIT:
        del _AUDIT[: len(_AUDIT) - _MAX_AUDIT]


# ---------------- Security Helpers ----------------
def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is valid"


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_account_locked(user: dict) -> bool:
    """Check if account is locked due to failed attempts"""
    if not user.get('locked_until'):
        return False
    locked_until = datetime.fromisoformat(user['locked_until'].replace('Z', '+00:00'))
    return datetime.utcnow() < locked_until.replace(tzinfo=None)


def lock_account(user: dict):
    """Lock account for 15 minutes after failed attempts"""
    user['failed_attempts'] = user.get('failed_attempts', 0) + 1
    if user['failed_attempts'] >= 5:
        user['locked_until'] = (datetime.utcnow() + timedelta(minutes=15)).isoformat() + 'Z'


def reset_failed_attempts(user: dict):
    """Reset failed login attempts on successful login"""
    user['failed_attempts'] = 0
    user['locked_until'] = None
    user['last_login'] = _now_iso()


def require_role(*allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')
            if user_role not in allowed_roles:
                return jsonify(message="Insufficient permissions"), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_input(data: str, max_length: int = 255) -> str:
    """Sanitize user input"""
    if not isinstance(data, str):
        return ""
    # Remove potential XSS characters
    data = re.sub(r'[<>"\'\/]', '', data)
    return data.strip()[:max_length]


# ---------------- Health ----------------
@auth_bp.get("/health")
def health():
    return jsonify(ok=True)


# DEVELOPMENT ONLY - Remove in production
@auth_bp.get("/dev/credentials")
def dev_credentials():
    """Development endpoint to get login credentials"""
    if os.environ.get("FLASK_ENV") != "development":
        return jsonify(message="Not available in production"), 404
    
    return jsonify({
        "message": "Development login credentials",
        "email": "admin@example.com", 
        "password": "SecureAdmin123!",
        "note": "Change password after first login"
    })


@auth_bp.post("/dev/reset-admin")  
def dev_reset_admin():
    """Development endpoint to reset admin password"""
    if os.environ.get("FLASK_ENV") != "development":
        return jsonify(message="Not available in production"), 404
    
    data = request.get_json() or {}
    new_password = data.get("password", "SecureAdmin123!")
    
    # Find admin user and reset password
    for user in _USERS:
        if user["email"] == "admin@example.com":
            user["password_hash"] = generate_password_hash(new_password)
            user["failed_attempts"] = 0
            user["locked_until"] = None
            _record("dev.password_reset", actor="system", target="admin@example.com")
            return jsonify({
                "message": "Admin password reset successfully",
                "email": "admin@example.com",
                "new_password": new_password
            })
    
    return jsonify(message="Admin user not found"), 404


# ---------------- Auth (secure) ----------------
@auth_bp.route("/login", methods=["OPTIONS"])
def login_options():
    """Handle CORS preflight requests for login"""
    response = jsonify()
    origin = request.headers.get('Origin')
    # Allow specific origins or all origins for development
    if origin:
        response.headers.add("Access-Control-Allow-Origin", origin)
    else:
        response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, ngrok-skip-browser-warning")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = sanitize_input(data.get("email", "")).lower()
    password = data.get("password", "")
    
    # Input validation
    if not email or not password:
        return jsonify(message="Email and password are required"), 400
    
    if not validate_email(email):
        return jsonify(message="Invalid email format"), 400
    
    # Find user
    user = next((u for u in _USERS if u["email"] == email), None)
    if not user:
        _record("login.failed", actor=email, meta={"reason": "user_not_found"})
        return jsonify(message="Invalid credentials"), 401
    
    # Check if account is locked
    if is_account_locked(user):
        _record("login.blocked", actor=email, meta={"reason": "account_locked"})
        return jsonify(message="Account temporarily locked due to failed login attempts"), 423
    
    # Check if account is active
    if user.get("status") != "active":
        _record("login.failed", actor=email, meta={"reason": "inactive_account"})
        return jsonify(message="Account is not active"), 401
    
    # Verify password
    if not check_password_hash(user.get("password_hash", ""), password):
        lock_account(user)
        _record("login.failed", actor=email, meta={
            "reason": "invalid_password",
            "failed_attempts": user.get("failed_attempts", 0)
        })
        return jsonify(message="Invalid credentials"), 401
    
    # Successful login
    reset_failed_attempts(user)
    
    # Create JWT token with expiration
    additional_claims = {
        "role": user["role"],
        "user_id": user["id"],
        "name": user["name"]
    }
    
    access_token = create_access_token(
        identity=email,
        additional_claims=additional_claims,
        expires_delta=timedelta(hours=8)
    )
    
    _record("login.success", actor=email, meta={"role": user["role"]})
    
    response = jsonify(
        access_token=access_token,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    )
    
    # Add CORS headers for production access
    origin = request.headers.get('Origin')
    if origin:
        response.headers.add("Access-Control-Allow-Origin", origin)
    else:
        response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    
    return response


@auth_bp.get("/me")
@jwt_required()
def me():
    current_user_email = get_jwt_identity()
    claims = get_jwt()
    
    user = next((u for u in _USERS if u["email"] == current_user_email), None)
    if not user:
        return jsonify(message="User not found"), 404
    
    return jsonify({
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "last_login": user.get("last_login")
    })


@auth_bp.post("/logout")
@jwt_required()
def logout():
    current_user_email = get_jwt_identity()
    _record("logout", actor=current_user_email)
    return jsonify(message="Successfully logged out")


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    data = request.get_json() or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    
    if not current_password or not new_password:
        return jsonify(message="Current and new passwords are required"), 400
    
    # Validate new password
    is_valid, msg = validate_password(new_password)
    if not is_valid:
        return jsonify(message=msg), 400
    
    current_user_email = get_jwt_identity()
    user = next((u for u in _USERS if u["email"] == current_user_email), None)
    
    if not user or not check_password_hash(user.get("password_hash", ""), current_password):
        _record("password_change.failed", actor=current_user_email, meta={"reason": "invalid_current_password"})
        return jsonify(message="Current password is incorrect"), 401
    
    # Update password
    user["password_hash"] = generate_password_hash(new_password)
    _record("password_change.success", actor=current_user_email)
    
    return jsonify(message="Password updated successfully")


# ---------------- Dashboard ----------------
@auth_bp.get("/dashboard/metrics")
@jwt_required()
def dashboard_metrics():
    claims = get_jwt()
    user_role = claims.get('role')
    current_user_email = get_jwt_identity()
    
    _record("dashboard.view", actor=current_user_email, meta={"role": user_role})
    
    # Base metrics available to all roles
    base_metrics = {
        "totals": {
            "tenants": len(_TENANTS),
            "users": len(_USERS),
            "properties": len(_PROPERTIES),
        },
        "incomeVsCost": {"income": 25000, "cost": 18000, "net": 7000},
    }
    
    # Add role-specific metrics
    if user_role == "super_admin":
        base_metrics["admin"] = {
            "workorders": len(_WORKORDERS),
            "payments": len(_PAYMENTS),
            "audit_events": len(_AUDIT)
        }
    
    return jsonify(base_metrics)

@auth_bp.get("/dashboard/metrics/<role>")
@jwt_required()
def dashboard_metrics_by_role(role):
    """Role-specific dashboard metrics"""
    
    if role == "super_admin":
        return jsonify({
            "totals": {
                "tenants": len(_TENANTS),
                "users": len(_USERS),
                "properties": len(_PROPERTIES),
                "workOrders": len(_WORKORDERS),
                "payments": len(_PAYMENTS)
            },
            "incomeVsCost": {"income": 25000, "cost": 18000, "net": 7000},
            "systemHealth": {
                "status": "operational",
                "uptime": "99.9%",
                "lastIncident": None
            }
        })
    
    elif role == "property_manager":
        # Filter data for specific manager - in real app, use user ID to filter
        return jsonify({
            "properties": [
                {"id": 1, "name": "Sunset Apartments", "units": 24, "occupied": 22},
                {"id": 2, "name": "Park View Complex", "units": 18, "occupied": 16}
            ],
            "totals": {
                "units": 42,
                "occupied": 38,
                "occupancyRate": 90.5,
                "monthlyRevenue": 35000
            },
            "pendingMaintenance": 5
        })
    
    elif role == "tenant":
        # Return tenant-specific data - in real app, filter by tenant ID
        return jsonify({
            "lease": {
                "property": "Sunset Apartments",
                "unit": "204",
                "rentAmount": 1250,
                "dueDate": "2024-09-01",
                "leaseEnd": "2025-08-31"
            },
            "payments": {
                "nextDue": 1250,
                "daysUntilDue": 5,
                "lastPayment": "2024-08-01"
            },
            "maintenance": {
                "active": 1,
                "pending": 0,
                "completed": 3
            }
        })
    
    else:
        # Basic user - minimal info
        return jsonify({
            "message": "Welcome to EstateCore",
            "accountStatus": "active",
            "lastLogin": _now_iso()
        })


# ---------------- Feature Flags ----------------
@auth_bp.get("/feature-flags")
@jwt_required()
def feature_flags_list():
    return jsonify([{"name": k, "enabled": v} for k, v in _FLAGS.items()])


@auth_bp.patch("/feature-flags/<name>")
@require_role("super_admin")
def feature_flags_toggle(name):
    data = request.get_json() or {}
    enabled = bool(data.get("enabled"))
    
    # Sanitize flag name
    name = sanitize_input(name, 50)
    if not name:
        return jsonify(message="Invalid flag name"), 400
    
    _FLAGS[name] = enabled
    current_user_email = get_jwt_identity()
    _record("flag.toggle", actor=current_user_email, target=name, meta={"enabled": enabled})
    return jsonify({"name": name, "enabled": enabled})


# ---------------- Users + Invites ----------------
@auth_bp.get("/users")
@require_role("super_admin", "property_manager")
def users_list():
    # Return user data without sensitive fields
    safe_users = []
    for user in _USERS:
        safe_user = {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "status": user["status"],
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login")
        }
        safe_users.append(safe_user)
    return jsonify(safe_users)


@auth_bp.post("/users")
@require_role("super_admin")
def users_create():
    global _NEXT_UID
    data = request.get_json() or {}

    email = sanitize_input(data.get("email", "")).lower()
    name = sanitize_input(data.get("name", "")) or (email.split("@")[0] if email else "")
    role = sanitize_input(data.get("role", "user")).lower()
    
    # Validate inputs
    if not email:
        return jsonify(message="Email is required"), 400
    if not validate_email(email):
        return jsonify(message="Invalid email format"), 400
    if not name:
        return jsonify(message="Name is required"), 400
    if role not in ["super_admin", "property_manager", "admin", "user", "tenant"]:
        return jsonify(message="Invalid role"), 400
    if any(u["email"] == email for u in _USERS):
        return jsonify(message="Email already exists"), 409

    uid = _NEXT_UID
    _NEXT_UID += 1
    # Property assignment for managers/admins
    property_ids = data.get("property_ids", [])
    if role in ["property_manager", "admin"] and not property_ids:
        # Default to first property if none specified
        if _PROPERTIES:
            property_ids = [_PROPERTIES[0]["id"]]
    
    user = {
        "id": uid, 
        "email": email, 
        "name": name, 
        "role": role, 
        "status": "invited",
        "created_at": _now_iso(),
        "failed_attempts": 0,
        "locked_until": None,
        "last_login": None,
        "password_hash": None,
        "property_ids": property_ids  # Properties this user manages/has access to
    }
    _USERS.append(user)

    token = token_urlsafe(16)
    _INVITES[token] = {"user_id": uid, "email": email, "created_at": _now_iso()}
    invite_url = _invite_url(token)

    # Send invitation email
    from estatecore_backend.app.utils.email_sms import send_email
    subject = "Welcome to EstateCore - Complete Your Registration"
    body = f"""Hello {name},

You've been invited to join EstateCore as a {role}.

Please click the link below to complete your registration:
{invite_url}

This invitation will expire in 7 days.

Best regards,
The EstateCore Team
"""
    
    email_sent = send_email(email, subject, body)
    
    current_user_email = get_jwt_identity()
    _record("user.create", actor=current_user_email, target=email, meta={"id": uid, "email_sent": email_sent})
    out = dict(user)
    out["invite_url"] = invite_url
    out["email_sent"] = email_sent
    return jsonify(out), 201


@auth_bp.put("/users/<int:user_id>")
@require_role("super_admin")
def users_update(user_id: int):
    data = request.get_json() or {}
    for u in _USERS:
        if u["id"] == user_id:
            before = dict(u)
            u["name"] = data.get("name", u["name"])
            u["role"] = data.get("role", u["role"])
            u["status"] = data.get("status", u["status"])
            _record("user.update", actor="admin@example.com", target=u["email"], meta={"before": before, "after": u})
            return jsonify(u)
    return jsonify(message="not found"), 404


@auth_bp.delete("/users/<int:user_id>")
@require_role("super_admin")
def users_delete(user_id: int):
    # remove user and any invites
    for u in list(_USERS):
        if u["id"] == user_id:
            _USERS.remove(u)
            for t, info in list(_INVITES.items()):
                if info.get("user_id") == user_id:
                    _INVITES.pop(t, None)
            _record("user.delete", actor="admin@example.com", target=u["email"], meta={"id": user_id})
            return jsonify(ok=True)
    return jsonify(message="not found"), 404


@auth_bp.post("/users/<int:user_id>/invite")
def users_invite(user_id: int):
    user = next((u for u in _USERS if u["id"] == user_id), None)
    if not user:
        return jsonify(message="not found"), 404
    token = token_urlsafe(16)
    _INVITES[token] = {"user_id": user_id, "email": user["email"], "created_at": _now_iso()}
    user["status"] = "invited"
    url = _invite_url(token)
    
    # Send invitation email
    from estatecore_backend.app.utils.email_sms import send_email
    subject = "EstateCore Invitation - Complete Your Registration"
    body = f"""Hello {user["name"]},

You've been invited to join EstateCore as a {user["role"]}.

Please click the link below to complete your registration:
{url}

This invitation will expire in 7 days.

Best regards,
The EstateCore Team
"""
    
    email_sent = send_email(user["email"], subject, body)
    
    _record("user.invite", actor="admin@example.com", target=user["email"], meta={"url": url, "email_sent": email_sent})
    return jsonify({"invite_url": url, "user": user, "email_sent": email_sent})


@auth_bp.get("/invites/<token>")
def invite_info(token: str):
    info = _INVITES.get(token)
    if not info:
        return jsonify(message="invalid or expired invite"), 404
    user = next((u for u in _USERS if u["id"] == info["user_id"]), None)
    if not user:
        return jsonify(message="user missing"), 404
    return jsonify({"email": info["email"], "user_id": user["id"], "status": user["status"]})


@auth_bp.post("/invites/<token>/accept")
def invite_accept(token: str):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    password = (data.get("password") or "").strip()  # TODO hash/store in real app

    info = _INVITES.pop(token, None)
    if not info:
        return jsonify(message="invalid or expired invite"), 404
    user = next((u for u in _USERS if u["id"] == info["user_id"]), None)
    if not user:
        return jsonify(message="user missing"), 404
    if name:
        user["name"] = name
    # password ignored in stub
    user["status"] = "active"
    _record("user.accept_invite", actor=user["email"], target=user["email"])
    return jsonify({"ok": True, "user": user})


# ---------------- Tenants (Clients) ----------------
@auth_bp.get("/tenants")
def tenants_list():
    return jsonify(_TENANTS)


@auth_bp.post("/tenants")
def tenants_create():
    global _NEXT_TID
    
    # Handle both JSON and form data (for file uploads)
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        d = request.form.to_dict()
        file = request.files.get('lease_document')
        
        # Validate required lease agreement fields
        required_fields = ['name', 'lease_start_date', 'lease_end_date', 'lease_amount', 'security_deposit']
        for field in required_fields:
            if not d.get(field):
                return jsonify(message=f"{field} is required"), 400
                
        if not file:
            return jsonify(message="lease_document is required"), 400
            
        # Save file (simplified - in production, use proper file storage)
        file_path = f"lease_{_NEXT_TID}_{file.filename}"
    else:
        d = request.get_json() or {}
        file_path = None
        
    name = (d.get("name") or "").strip()
    if not name:
        return jsonify(message="name required"), 400
        
    tid = _NEXT_TID
    _NEXT_TID += 1
    
    t = {
        "id": tid, 
        "name": name, 
        "email": d.get("email", ""),
        "phone": d.get("phone", ""),
        "address": d.get("address", ""),
        "emergency_contact_name": d.get("emergency_contact_name", ""),
        "emergency_contact_phone": d.get("emergency_contact_phone", ""),
        "emergency_contact_address": d.get("emergency_contact_address", ""),
        
        # Lease agreement fields
        "lease_start_date": d.get("lease_start_date", ""),
        "lease_end_date": d.get("lease_end_date", ""),
        "lease_amount": d.get("lease_amount", 0),
        "security_deposit": d.get("security_deposit", 0),
        "lease_document_path": file_path,
        
        "status": "active"
    }
    _TENANTS.append(t)
    _record("tenant.create", actor="admin@example.com", target=name, meta={"id": tid})
    return jsonify(t), 201


@auth_bp.put("/tenants/<int:tenant_id>")
def tenants_update(tenant_id: int):
    d = request.get_json() or {}
    for t in _TENANTS:
        if t["id"] == tenant_id:
            before = dict(t)
            t["name"] = d.get("name", t["name"])
            t["domain"] = (d.get("domain", t["domain"]) or "").lower()
            t["status"] = d.get("status", t["status"])
            _record("tenant.update", actor="admin@example.com", target=t["name"], meta={"before": before, "after": t})
            return jsonify(t)
    return jsonify(message="not found"), 404


@auth_bp.delete("/tenants/<int:tenant_id>")
def tenants_delete(tenant_id: int):
    for t in list(_TENANTS):
        if t["id"] == tenant_id:
            _TENANTS.remove(t)
            _record("tenant.delete", actor="admin@example.com", target=t["name"], meta={"id": tenant_id})
            return jsonify(ok=True)
    return jsonify(message="not found"), 404

@auth_bp.get("/tenants/<int:tenant_id>/lease-document")
def tenant_lease_document(tenant_id: int):
    for t in _TENANTS:
        if t["id"] == tenant_id:
            if t.get("lease_document_path"):
                # In a real application, you would serve the actual file
                # For now, return a mock response
                return jsonify({"message": f"Lease document for {t['name']}", "path": t["lease_document_path"]})
            else:
                return jsonify(message="No lease document found"), 404
    return jsonify(message="Tenant not found"), 404


# ---------------- Properties ----------------
@auth_bp.get("/properties")
def properties_list():
    # Enrich properties with their apartments
    enriched_properties = []
    for prop in _PROPERTIES:
        enriched_prop = prop.copy()
        enriched_prop["apartments"] = [apt for apt in _APARTMENTS if apt["property_id"] == prop["id"]]
        enriched_properties.append(enriched_prop)
    return jsonify(enriched_properties)


@auth_bp.post("/properties")
def properties_create():
    global _NEXT_PID, _NEXT_AID
    d = request.get_json() or {}
    
    # Create the property
    property_item = {
        "id": _NEXT_PID, 
        "name": d.get("name", ""), 
        "address": d.get("address", ""),
        "apartments": []
    }
    
    # Process apartments if provided
    apartments_data = d.get("apartments", [])
    for apt_data in apartments_data:
        apartment = {
            "id": _NEXT_AID,
            "property_id": _NEXT_PID,
            "unit_number": apt_data.get("unit_number", ""),
            "bedrooms": apt_data.get("bedrooms", 0),
            "bathrooms": apt_data.get("bathrooms", 0),
            "rent_amount": apt_data.get("rent_amount", 0),
            "status": apt_data.get("status", "available"),  # available, occupied, maintenance
            "tenant_id": None
        }
        _APARTMENTS.append(apartment)
        property_item["apartments"].append(apartment)
        _NEXT_AID += 1
    
    _NEXT_PID += 1
    _PROPERTIES.append(property_item)
    _record("property.create", actor="admin@example.com", target=property_item["name"])
    return jsonify(property_item), 201


@auth_bp.put("/properties/<int:item_id>")
def properties_update(item_id: int):
    d = request.get_json() or {}
    for it in _PROPERTIES:
        if it["id"] == item_id:
            it["name"] = d.get("name", it["name"])
            it["address"] = d.get("address", it["address"])
            it["apt_number"] = d.get("apt_number", it.get("apt_number", ""))
            _record("property.update", actor="admin@example.com", target=str(item_id))
            return jsonify(it)
    return jsonify(message="not found"), 404


@auth_bp.delete("/properties/<int:item_id>")
def properties_delete(item_id: int):
    for i, it in enumerate(_PROPERTIES):
        if it["id"] == item_id:
            _PROPERTIES.pop(i)
            _record("property.delete", actor="admin@example.com", target=str(item_id))
            return jsonify(ok=True)
    return jsonify(message="not found"), 404


# ---------------- Apartments ----------------
@auth_bp.get("/apartments")
def apartments_list():
    return jsonify(_APARTMENTS)

@auth_bp.get("/apartments/available")
def apartments_available():
    available = [apt for apt in _APARTMENTS if apt["status"] == "available"]
    # Enrich with property info
    for apt in available:
        property_info = next((p for p in _PROPERTIES if p["id"] == apt["property_id"]), None)
        if property_info:
            apt["property_name"] = property_info["name"]
            apt["property_address"] = property_info["address"]
    return jsonify(available)

@auth_bp.put("/apartments/<int:apt_id>/assign")
def apartment_assign_tenant(apt_id: int):
    d = request.get_json() or {}
    tenant_id = d.get("tenant_id")
    
    if not tenant_id:
        return jsonify(message="tenant_id required"), 400
    
    # Find apartment
    for apt in _APARTMENTS:
        if apt["id"] == apt_id:
            apt["tenant_id"] = tenant_id
            apt["status"] = "occupied"
            _record("apartment.assign", actor="admin@example.com", target=f"apt:{apt_id},tenant:{tenant_id}")
            return jsonify(apt)
    
    return jsonify(message="apartment not found"), 404

@auth_bp.put("/apartments/<int:apt_id>/unassign")
def apartment_unassign_tenant(apt_id: int):
    # Find apartment
    for apt in _APARTMENTS:
        if apt["id"] == apt_id:
            old_tenant = apt["tenant_id"]
            apt["tenant_id"] = None
            apt["status"] = "available"
            _record("apartment.unassign", actor="admin@example.com", target=f"apt:{apt_id},was_tenant:{old_tenant}")
            return jsonify(apt)
    
    return jsonify(message="apartment not found"), 404


# ---------------- Leases ----------------
@auth_bp.get("/leases")
def leases_list():
    return jsonify(_LEASES)


@auth_bp.post("/leases")
def leases_create():
    global _NEXT_LID
    d = request.get_json() or {}
    item = {
        "id": _NEXT_LID,
        "tenant": d.get("tenant", ""),
        "property": d.get("property", ""),
        "start_date": d.get("start_date", ""),
        "end_date": d.get("end_date", ""),
        "rent": d.get("rent", 0),
    }
    _NEXT_LID += 1
    _LEASES.append(item)
    _record("lease.create", actor="admin@example.com", target=item["tenant"])
    return jsonify(item), 201


@auth_bp.put("/leases/<int:item_id>")
def leases_update(item_id: int):
    d = request.get_json() or {}
    for it in _LEASES:
        if it["id"] == item_id:
            for k in ["tenant", "property", "start_date", "end_date", "rent"]:
                if k in d:
                    it[k] = d[k]
            _record("lease.update", actor="admin@example.com", target=str(item_id))
            return jsonify(it)
    return jsonify(message="not found"), 404


@auth_bp.delete("/leases/<int:item_id>")
def leases_delete(item_id: int):
    for i, it in enumerate(_LEASES):
        if it["id"] == item_id:
            _LEASES.pop(i)
            _record("lease.delete", actor="admin@example.com", target=str(item_id))
            return jsonify(ok=True)
    return jsonify(message="not found"), 404


# ---------------- Work Orders ----------------
@auth_bp.get("/workorders")
def workorders_list():
    return jsonify(_WORKORDERS)


@auth_bp.post("/workorders")
def workorders_create():
    global _NEXT_WID
    d = request.get_json() or {}
    item = {
        "id": _NEXT_WID,
        "title": d.get("title", ""),
        "status": d.get("status", "open"),
        "priority": d.get("priority", "normal"),
    }
    _NEXT_WID += 1
    _WORKORDERS.append(item)
    _record("workorder.create", actor="admin@example.com", target=item["title"])
    return jsonify(item), 201


@auth_bp.put("/workorders/<int:item_id>")
def workorders_update(item_id: int):
    d = request.get_json() or {}
    for it in _WORKORDERS:
        if it["id"] == item_id:
            for k in ["title", "status", "priority"]:
                if k in d:
                    it[k] = d[k]
            _record("workorder.update", actor="admin@example.com", target=str(item_id))
            return jsonify(it)
    return jsonify(message="not found"), 404


@auth_bp.delete("/workorders/<int:item_id>")
def workorders_delete(item_id: int):
    for i, it in enumerate(_WORKORDERS):
        if it["id"] == item_id:
            _WORKORDERS.pop(i)
            _record("workorder.delete", actor="admin@example.com", target=str(item_id))
            return jsonify(ok=True)
    return jsonify(message="not found"), 404


# ---------------- Payments ----------------
@auth_bp.get("/payments")
def payments_list():
    return jsonify(_PAYMENTS)


@auth_bp.post("/payments")
def payments_create():
    global _NEXT_PAYID
    d = request.get_json() or {}
    item = {
        "id": _NEXT_PAYID,
        "tenant": d.get("tenant", ""),
        "amount": d.get("amount", 0),
        "date": d.get("date", ""),
        "method": d.get("method", "card"),
    }
    _NEXT_PAYID += 1
    _PAYMENTS.append(item)
    _record("payment.create", actor="admin@example.com", target=item["tenant"], meta={"amount": item["amount"]})
    return jsonify(item), 201


@auth_bp.put("/payments/<int:item_id>")
def payments_update(item_id: int):
    d = request.get_json() or {}
    for it in _PAYMENTS:
        if it["id"] == item_id:
            for k in ["tenant", "amount", "date", "method"]:
                if k in d:
                    it[k] = d[k]
            _record("payment.update", actor="admin@example.com", target=str(item_id))
            return jsonify(it)
    return jsonify(message="not found"), 404


@auth_bp.delete("/payments/<int:item_id>")
def payments_delete(item_id: int):
    for i, it in enumerate(_PAYMENTS):
        if it["id"] == item_id:
            _PAYMENTS.pop(i)
            _record("payment.delete", actor="admin@example.com", target=str(item_id))
            return jsonify(ok=True)
    return jsonify(message="not found"), 404


# ---------------- Rent Management ----------------
_RENT = [
    {
        "id": 1,
        "tenant_id": 101,
        "property_id": 201,
        "unit": "A1",
        "amount": "1200.00",
        "due_date": "2024-09-01",
        "status": "unpaid",
        "notes": "Monthly rent"
    },
    {
        "id": 2,
        "tenant_id": 102,
        "property_id": 201,
        "unit": "B2", 
        "amount": "1500.00",
        "due_date": "2024-09-01",
        "status": "paid",
        "notes": "Monthly rent"
    }
]
_NEXT_RID = 3

@auth_bp.route("/rent", methods=["GET"])
def rent_list():
    return jsonify({"rent_records": _RENT})

@auth_bp.post("/rent")
def rent_create():
    data = request.get_json() or {}
    global _NEXT_RID
    new_record = {
        "id": _NEXT_RID,
        "tenant_id": data.get("tenant_id"),
        "property_id": data.get("property_id"),
        "unit": data.get("unit", ""),
        "amount": data.get("amount"),
        "due_date": data.get("due_date"),
        "status": "unpaid",
        "notes": data.get("notes", "")
    }
    _RENT.append(new_record)
    _NEXT_RID += 1
    _record("rent.create", actor="admin@example.com", target=str(new_record["id"]))
    return jsonify(new_record), 201

@auth_bp.put("/rent/<int:rent_id>")
def rent_update(rent_id):
    data = request.get_json() or {}
    for i, rent in enumerate(_RENT):
        if rent["id"] == rent_id:
            _RENT[i].update(data)
            _record("rent.update", actor="admin@example.com", target=str(rent_id))
            return jsonify(_RENT[i])
    return jsonify(message="not found"), 404

@auth_bp.delete("/rent/<int:rent_id>")
def rent_delete(rent_id):
    global _RENT
    _RENT = [r for r in _RENT if r["id"] != rent_id]
    _record("rent.delete", actor="admin@example.com", target=str(rent_id))
    return jsonify(message="deleted")

@auth_bp.post("/rent/<int:rent_id>/mark_paid")
def rent_mark_paid(rent_id):
    for rent in _RENT:
        if rent["id"] == rent_id:
            rent["status"] = "paid"
            _record("rent.mark_paid", actor="admin@example.com", target=str(rent_id))
            return jsonify(rent)
    return jsonify(message="not found"), 404

@auth_bp.post("/rent/<int:rent_id>/mark_unpaid")
def rent_mark_unpaid(rent_id):
    for rent in _RENT:
        if rent["id"] == rent_id:
            rent["status"] = "unpaid"
            _record("rent.mark_unpaid", actor="admin@example.com", target=str(rent_id))
            return jsonify(rent)
    return jsonify(message="not found"), 404

@auth_bp.get("/rent/<int:rent_id>/pdf")
def rent_pdf(rent_id):
    return jsonify(message=f"PDF receipt for rent {rent_id} would be generated")

# ---------------- Password Reset ----------------
_RESET_TOKENS = {}  # email -> {"token": str, "expires": datetime, "used": bool}

@auth_bp.post("/auth/forgot-password")
def forgot_password():
    """Send password reset instructions to user email"""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    
    if not email or not validate_email(email):
        return jsonify(message="Please provide a valid email address"), 400
    
    # Check if user exists
    user = None
    for u in _USERS:
        if u["email"].lower() == email:
            user = u
            break
    
    if not user:
        # For security, always return success even if user doesn't exist
        return jsonify(message="If an account with this email exists, reset instructions have been sent"), 200
    
    # Generate reset token
    reset_token = token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
    
    _RESET_TOKENS[email] = {
        "token": reset_token,
        "expires": expires,
        "used": False
    }
    
    _record("password.reset_requested", actor=email, target=email)
    
    # In production, you would send an email here
    # For development, log the reset link
    reset_url = f"http://localhost:5173/reset-password?token={reset_token}&email={email}"
    current_app.logger.info(f"Password reset link for {email}: {reset_url}")
    
    return jsonify({
        "message": "Password reset instructions have been sent to your email",
        "dev_reset_url": reset_url if os.environ.get("FLASK_ENV") == "development" else None
    }), 200

@auth_bp.post("/auth/reset-password")
def reset_password():
    """Reset password using token"""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    token = data.get("token", "").strip()
    new_password = data.get("password", "").strip()
    
    if not email or not token or not new_password:
        return jsonify(message="Email, token, and new password are required"), 400
    
    # Validate new password
    valid, msg = validate_password(new_password)
    if not valid:
        return jsonify(message=msg), 400
    
    # Check if reset token exists and is valid
    reset_data = _RESET_TOKENS.get(email)
    if not reset_data:
        return jsonify(message="Invalid or expired reset token"), 400
    
    if reset_data["used"]:
        return jsonify(message="Reset token has already been used"), 400
    
    if datetime.utcnow() > reset_data["expires"]:
        del _RESET_TOKENS[email]
        return jsonify(message="Reset token has expired"), 400
    
    if reset_data["token"] != token:
        return jsonify(message="Invalid reset token"), 400
    
    # Find and update user password
    user = None
    for u in _USERS:
        if u["email"].lower() == email:
            user = u
            break
    
    if not user:
        return jsonify(message="User not found"), 404
    
    # Update password
    user["password_hash"] = generate_password_hash(new_password)
    user["failed_attempts"] = 0
    user["locked_until"] = None
    
    # Mark token as used
    _RESET_TOKENS[email]["used"] = True
    
    _record("password.reset_completed", actor=email, target=email)
    
    return jsonify(message="Password has been reset successfully"), 200

@auth_bp.get("/auth/validate-reset-token")
def validate_reset_token():
    """Validate if a reset token is valid"""
    email = request.args.get("email", "").strip().lower()
    token = request.args.get("token", "").strip()
    
    if not email or not token:
        return jsonify(valid=False, message="Email and token are required"), 400
    
    reset_data = _RESET_TOKENS.get(email)
    if not reset_data:
        return jsonify(valid=False, message="Invalid token"), 200
    
    if reset_data["used"]:
        return jsonify(valid=False, message="Token has been used"), 200
    
    if datetime.utcnow() > reset_data["expires"]:
        del _RESET_TOKENS[email]
        return jsonify(valid=False, message="Token has expired"), 200
    
    if reset_data["token"] != token:
        return jsonify(valid=False, message="Invalid token"), 200
    
    return jsonify(valid=True, message="Token is valid"), 200

# ---------------- Registration/Invite Handling ----------------
@auth_bp.get("/auth/invite/<token>")
def get_invite_info(token):
    """Get invitation information from token"""
    invite = _INVITES.get(token)
    if not invite:
        return jsonify(valid=False, message="Invalid or expired invitation"), 404
    
    user = None
    for u in _USERS:
        if u["id"] == invite["user_id"]:
            user = u
            break
    
    if not user:
        return jsonify(valid=False, message="User not found"), 404
    
    if user["status"] == "active":
        return jsonify(valid=False, message="Invitation already used"), 400
    
    return jsonify({
        "valid": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    }), 200

@auth_bp.post("/auth/register/<token>")
def register_with_invite(token):
    """Complete registration with invitation token"""
    invite = _INVITES.get(token)
    if not invite:
        return jsonify(message="Invalid or expired invitation"), 404
    
    data = request.get_json() or {}
    password = data.get("password", "").strip()
    
    if not password:
        return jsonify(message="Password is required"), 400
    
    # Validate password
    valid, msg = validate_password(password)
    if not valid:
        return jsonify(message=msg), 400
    
    # Find user
    user = None
    for u in _USERS:
        if u["id"] == invite["user_id"]:
            user = u
            break
    
    if not user:
        return jsonify(message="User not found"), 404
    
    if user["status"] == "active":
        return jsonify(message="Account already activated"), 400
    
    # Update user with password and activate
    user["password_hash"] = generate_password_hash(password)
    user["status"] = "active"
    user["failed_attempts"] = 0
    user["locked_until"] = None
    user["last_login"] = _now_iso()
    
    # Remove used invitation
    del _INVITES[token]
    
    _record("user.register", actor=user["email"], target=user["email"], meta={"user_id": user["id"]})
    
    # Create access token
    additional_claims = {
        "role": user["role"],
        "status": user["status"],
        "name": user["name"]
    }
    access_token = create_access_token(
        identity=user["email"],
        additional_claims=additional_claims
    )
    
    return jsonify({
        "message": "Registration completed successfully",
        "access_token": access_token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "status": user["status"]
        }
    }), 201

# ---------------- Audit ----------------
@auth_bp.get("/audit")
def audit_list():
    try:
        limit = max(1, min(500, int(request.args.get("limit", "100"))))
    except ValueError:
        limit = 100
    # newest first
    return jsonify(list(reversed(_AUDIT[-limit:])))
