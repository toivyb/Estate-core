# routes/auth.py
from flask import Blueprint, request, jsonify
from secrets import token_urlsafe
from datetime import datetime
import os

# Single blueprint for all API routes under /api
auth_bp = Blueprint("auth", __name__, url_prefix="/api")

# ---------------- In-memory stores (DEV only) ----------------
_USERS = [
    {"id": 1, "email": "admin@example.com", "name": "Admin", "role": "super_admin", "status": "active"},
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


# ---------------- Health ----------------
@auth_bp.get("/health")
def health():
    return jsonify(ok=True)


# ---------------- Auth (stub) ----------------
@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    if not email or not password:
        return jsonify(message="Missing credentials"), 400
    _record("login", actor=email)
    # TODO: replace with real JWT/session
    return jsonify(access_token="TEST_TOKEN", user={"email": email, "role": "super_admin", "name": "Admin"})


@auth_bp.get("/me")
def me():
    # TODO: read real identity from token
    return jsonify({"email": "admin@example.com", "role": "super_admin"})


# ---------------- Dashboard ----------------
@auth_bp.get("/dashboard/metrics")
def dashboard_metrics():
    # TODO: In a real implementation, get role from JWT token
    # For now, return comprehensive metrics for all users
    
    return jsonify(
        {
            "totals": {
                "tenants": len(_TENANTS),
                "users": len(_USERS),
                "properties": len(_PROPERTIES),
            },
            "incomeVsCost": {"income": 25000, "cost": 18000, "net": 7000},
        }
    )

@auth_bp.get("/dashboard/metrics/<role>")
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
def feature_flags_list():
    return jsonify([{"name": k, "enabled": v} for k, v in _FLAGS.items()])


@auth_bp.patch("/feature-flags/<name>")
def feature_flags_toggle(name):
    data = request.get_json() or {}
    enabled = bool(data.get("enabled"))
    _FLAGS[name] = enabled
    _record("flag.toggle", actor="admin@example.com", target=name, meta={"enabled": enabled})
    return jsonify({"name": name, "enabled": enabled})


# ---------------- Users + Invites ----------------
@auth_bp.get("/users")
def users_list():
    return jsonify(_USERS)


@auth_bp.post("/users")
def users_create():
    global _NEXT_UID
    data = request.get_json() or {}

    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip() or (email.split("@")[0] if email else "")
    role = (data.get("role") or "user").strip().lower()

    if not email:
        return jsonify(message="email required"), 400
    if any(u["email"] == email for u in _USERS):
        return jsonify(message="email already exists"), 409

    uid = _NEXT_UID
    _NEXT_UID += 1
    user = {"id": uid, "email": email, "name": name, "role": role, "status": "invited"}
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
    
    _record("user.create", actor="admin@example.com", target=email, meta={"id": uid, "email_sent": email_sent})
    out = dict(user)
    out["invite_url"] = invite_url
    out["email_sent"] = email_sent
    return jsonify(out), 201


@auth_bp.put("/users/<int:user_id>")
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
    d = request.get_json() or {}
    name = (d.get("name") or "").strip()
    domain = (d.get("domain") or "").strip().lower()
    if not name:
        return jsonify(message="name required"), 400
    tid = _NEXT_TID
    _NEXT_TID += 1
    t = {"id": tid, "name": name, "domain": domain, "status": "active"}
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


# ---------------- Properties ----------------
@auth_bp.get("/properties")
def properties_list():
    return jsonify(_PROPERTIES)


@auth_bp.post("/properties")
def properties_create():
    global _NEXT_PID
    d = request.get_json() or {}
    item = {"id": _NEXT_PID, "name": d.get("name", ""), "address": d.get("address", "")}
    _NEXT_PID += 1
    _PROPERTIES.append(item)
    _record("property.create", actor="admin@example.com", target=item["name"])
    return jsonify(item), 201


@auth_bp.put("/properties/<int:item_id>")
def properties_update(item_id: int):
    d = request.get_json() or {}
    for it in _PROPERTIES:
        if it["id"] == item_id:
            it["name"] = d.get("name", it["name"])
            it["address"] = d.get("address", it["address"])
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

# ---------------- Audit ----------------
@auth_bp.get("/audit")
def audit_list():
    try:
        limit = max(1, min(500, int(request.args.get("limit", "100"))))
    except ValueError:
        limit = 100
    # newest first
    return jsonify(list(reversed(_AUDIT[-limit:])))
