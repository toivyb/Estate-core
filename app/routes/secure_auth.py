from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import re
from .. import db
from ..models import User
from ..security.auth_enhancement import (
    SecurityEnforcer, validate_input_data, sanitize_input
)

bp = Blueprint("secure_auth", __name__)


@bp.post("/auth/login")
@SecurityEnforcer.rate_limit(max_requests=5, window_minutes=15)
@sanitize_input()
@validate_input_data(
    required_fields=['email', 'password'],
    max_length={'email': 255, 'password': 255}
)
def secure_login():
    """Enhanced secure login with rate limiting and security logging"""
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({
            "error": "invalid_credentials",
            "message": "Invalid email or password"
        }), 401
    
    # Check if account is locked
    if SecurityEnforcer.is_account_locked(email, ip_address):
        SecurityEnforcer.log_security_event(
            'account_locked_attempt',
            ip_address=ip_address,
            details=f'Login attempt on locked account: {email}'
        )
        return jsonify({
            "error": "account_locked",
            "message": "Account temporarily locked due to multiple failed login attempts"
        }), 423
    
    try:
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Track failed attempt even if user doesn't exist
            SecurityEnforcer.track_failed_login(email, ip_address)
            SecurityEnforcer.log_security_event(
                'login_failed_user_not_found',
                ip_address=ip_address,
                details=f'Login attempt for non-existent user: {email}'
            )
            return jsonify({
                "error": "invalid_credentials",
                "message": "Invalid email or password"
            }), 401
        
        # Check if user is active
        if not getattr(user, 'is_active', True):
            SecurityEnforcer.track_failed_login(email, ip_address)
            SecurityEnforcer.log_security_event(
                'login_failed_inactive_user',
                user_id=user.id,
                ip_address=ip_address,
                details=f'Login attempt for inactive user: {email}'
            )
            return jsonify({
                "error": "account_disabled",
                "message": "Your account has been disabled. Please contact support."
            }), 401
        
        # Verify password
        if not user.check_password(password):
            failed_count = SecurityEnforcer.track_failed_login(email, ip_address)
            SecurityEnforcer.log_security_event(
                'login_failed_wrong_password',
                user_id=user.id,
                ip_address=ip_address,
                details=f'Failed login attempt #{failed_count} for user: {email}'
            )
            return jsonify({
                "error": "invalid_credentials",
                "message": "Invalid email or password"
            }), 401
        
        # Successful login - clear failed attempts
        SecurityEnforcer.clear_failed_attempts(email, ip_address)
        
        # Update last login
        user.last_login = datetime.utcnow()
        user.last_login_ip = ip_address
        db.session.commit()
        
        # Create tokens
        user_claims = {
            "email": user.email,
            "role": getattr(user, "role", "user"),
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=user_claims,
            expires_delta=timedelta(hours=1)  # Shorter expiry for security
        )
        
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=30)
        )
        
        # Log successful login
        SecurityEnforcer.log_security_event(
            'login_successful',
            user_id=user.id,
            ip_address=ip_address,
            details=f'Successful login for user: {email}'
        )
        
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": getattr(user, "role", "user"),
                "last_login": user.last_login.isoformat() if user.last_login else None
            },
            "expires_in": 3600  # 1 hour in seconds
        }), 200
        
    except Exception as e:
        SecurityEnforcer.log_security_event(
            'login_system_error',
            ip_address=ip_address,
            details=f'System error during login: {str(e)}'
        )
        return jsonify({
            "error": "system_error",
            "message": "An error occurred during login. Please try again."
        }), 500


@bp.post("/auth/refresh")
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        
        # Validate user still exists and is active
        user = User.query.get(current_user_id)
        if not user or not getattr(user, 'is_active', True):
            SecurityEnforcer.log_security_event(
                'token_refresh_failed_invalid_user',
                user_id=current_user_id,
                ip_address=request.remote_addr
            )
            return jsonify({
                "error": "invalid_user",
                "message": "User not found or inactive"
            }), 401
        
        # Create new access token
        user_claims = {
            "email": user.email,
            "role": getattr(user, "role", "user")
        }
        
        new_access_token = create_access_token(
            identity=str(user.id),
            additional_claims=user_claims,
            expires_delta=timedelta(hours=1)
        )
        
        SecurityEnforcer.log_security_event(
            'token_refreshed',
            user_id=user.id,
            ip_address=request.remote_addr
        )
        
        return jsonify({
            "access_token": new_access_token,
            "expires_in": 3600
        }), 200
        
    except Exception as e:
        SecurityEnforcer.log_security_event(
            'token_refresh_system_error',
            ip_address=request.remote_addr,
            details=str(e)
        )
        return jsonify({
            "error": "refresh_failed",
            "message": "Failed to refresh token"
        }), 500


@bp.post("/auth/change-password")
@jwt_required()
@sanitize_input()
@validate_input_data(
    required_fields=['current_password', 'new_password'],
    max_length={'current_password': 255, 'new_password': 255}
)
def change_password():
    """Change user password with security validation"""
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                "error": "user_not_found",
                "message": "User not found"
            }), 404
        
        # Verify current password
        if not user.check_password(current_password):
            SecurityEnforcer.log_security_event(
                'password_change_failed_wrong_current',
                user_id=user.id,
                ip_address=request.remote_addr
            )
            return jsonify({
                "error": "invalid_password",
                "message": "Current password is incorrect"
            }), 401
        
        # Validate new password strength
        is_strong, message = SecurityEnforcer.require_strong_password(new_password)
        if not is_strong:
            return jsonify({
                "error": "weak_password",
                "message": message
            }), 400
        
        # Check if new password is different from current
        if check_password_hash(user.password_hash, new_password):
            return jsonify({
                "error": "same_password",
                "message": "New password must be different from current password"
            }), 400
        
        # Update password
        user.set_password(new_password)
        user.password_changed_at = datetime.utcnow()
        db.session.commit()
        
        SecurityEnforcer.log_security_event(
            'password_changed',
            user_id=user.id,
            ip_address=request.remote_addr
        )
        
        return jsonify({
            "message": "Password changed successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        SecurityEnforcer.log_security_event(
            'password_change_system_error',
            user_id=current_user_id if 'current_user_id' in locals() else None,
            ip_address=request.remote_addr,
            details=str(e)
        )
        return jsonify({
            "error": "system_error",
            "message": "Failed to change password"
        }), 500


@bp.post("/auth/logout")
@jwt_required()
def logout():
    """Logout user (in a full implementation, this would blacklist the token)"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # In a production system, you would:
        # 1. Add the token to a blacklist stored in Redis
        # 2. Set token expiry to immediate
        # 3. Clear any session data
        
        SecurityEnforcer.log_security_event(
            'user_logout',
            user_id=current_user_id,
            ip_address=request.remote_addr
        )
        
        return jsonify({
            "message": "Logged out successfully"
        }), 200
        
    except Exception as e:
        SecurityEnforcer.log_security_event(
            'logout_system_error',
            ip_address=request.remote_addr,
            details=str(e)
        )
        return jsonify({
            "error": "logout_failed",
            "message": "Failed to logout"
        }), 500


@bp.get("/auth/me")
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user or not getattr(user, 'is_active', True):
            return jsonify({
                "error": "user_not_found",
                "message": "User not found or inactive"
            }), 404
        
        return jsonify({
            "id": user.id,
            "email": user.email,
            "role": getattr(user, "role", "user"),
            "last_login": user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None,
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else None
        }), 200
        
    except Exception as e:
        SecurityEnforcer.log_security_event(
            'get_user_info_error',
            user_id=current_user_id if 'current_user_id' in locals() else None,
            ip_address=request.remote_addr,
            details=str(e)
        )
        return jsonify({
            "error": "system_error",
            "message": "Failed to get user information"
        }), 500


@bp.get("/auth/security-status")
@jwt_required()
def get_security_status():
    """Get security status for current user"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                "error": "user_not_found",
                "message": "User not found"
            }), 404
        
        # Calculate days since password change
        days_since_password_change = None
        if hasattr(user, 'password_changed_at') and user.password_changed_at:
            days_since_password_change = (datetime.utcnow() - user.password_changed_at).days
        
        # Check for recent failed login attempts
        ip_address = request.remote_addr
        recent_failed_attempts = len(failed_login_attempts.get(f"{user.email}:{ip_address}", []))
        
        return jsonify({
            "user_id": user.id,
            "email": user.email,
            "last_login": user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None,
            "days_since_password_change": days_since_password_change,
            "recent_failed_attempts": recent_failed_attempts,
            "password_change_recommended": days_since_password_change and days_since_password_change > 90,
            "account_status": "active" if getattr(user, 'is_active', True) else "inactive"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "system_error",
            "message": "Failed to get security status"
        }), 500