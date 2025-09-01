from functools import wraps
from flask import jsonify, request, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
import hashlib
import time
import redis
from ..models import User
from .. import db

# Rate limiting storage (in production, use Redis)
# For now, we'll use a simple in-memory store
rate_limit_store = {}
failed_login_attempts = {}

class SecurityEnforcer:
    """Enhanced security enforcement for authentication and authorization"""
    
    @staticmethod
    def rate_limit(max_requests=5, window_minutes=15):
        """Rate limiting decorator"""
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Get client identifier
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                key = f"rate_limit:{client_ip}:{f.__name__}"
                
                current_time = time.time()
                window_start = current_time - (window_minutes * 60)
                
                # Clean old entries and count current requests
                if key in rate_limit_store:
                    rate_limit_store[key] = [
                        timestamp for timestamp in rate_limit_store[key] 
                        if timestamp > window_start
                    ]
                else:
                    rate_limit_store[key] = []
                
                # Check if limit exceeded
                if len(rate_limit_store[key]) >= max_requests:
                    return jsonify({
                        "error": "rate_limit_exceeded",
                        "message": f"Too many requests. Try again in {window_minutes} minutes."
                    }), 429
                
                # Add current request
                rate_limit_store[key].append(current_time)
                
                return f(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def track_failed_login(email, ip_address):
        """Track failed login attempts"""
        key = f"{email}:{ip_address}"
        current_time = time.time()
        
        if key not in failed_login_attempts:
            failed_login_attempts[key] = []
        
        # Clean old attempts (older than 1 hour)
        hour_ago = current_time - 3600
        failed_login_attempts[key] = [
            timestamp for timestamp in failed_login_attempts[key] 
            if timestamp > hour_ago
        ]
        
        # Add current attempt
        failed_login_attempts[key].append(current_time)
        
        return len(failed_login_attempts[key])
    
    @staticmethod
    def is_account_locked(email, ip_address, max_attempts=5):
        """Check if account is locked due to failed attempts"""
        key = f"{email}:{ip_address}"
        
        if key not in failed_login_attempts:
            return False
        
        current_time = time.time()
        hour_ago = current_time - 3600
        
        # Clean old attempts
        failed_login_attempts[key] = [
            timestamp for timestamp in failed_login_attempts[key] 
            if timestamp > hour_ago
        ]
        
        return len(failed_login_attempts[key]) >= max_attempts
    
    @staticmethod
    def clear_failed_attempts(email, ip_address):
        """Clear failed login attempts after successful login"""
        key = f"{email}:{ip_address}"
        if key in failed_login_attempts:
            del failed_login_attempts[key]
    
    @staticmethod
    def require_strong_password(password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"
    
    @staticmethod
    def log_security_event(event_type, user_id=None, ip_address=None, details=None):
        """Log security events for auditing"""
        from ..models import SecurityLog  # Import here to avoid circular imports
        
        try:
            log_entry = SecurityLog(
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                details=details,
                timestamp=datetime.utcnow()
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            # Don't let logging errors break the application
            current_app.logger.error(f"Failed to log security event: {str(e)}")


def enhanced_jwt_required(f):
    """Enhanced JWT validation with security logging"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            
            # Get user info from token
            current_user_id = get_jwt_identity()
            claims = get_jwt()
            
            # Validate user still exists and is active
            user = User.query.get(current_user_id)
            if not user or not getattr(user, 'is_active', True):
                SecurityEnforcer.log_security_event(
                    'invalid_token_attempt',
                    user_id=current_user_id,
                    ip_address=request.remote_addr,
                    details='User not found or inactive'
                )
                return jsonify({"error": "invalid_token", "message": "User not found or inactive"}), 401
            
            # Check if token is blacklisted (implement token blacklist if needed)
            # This would require storing blacklisted tokens in Redis/database
            
            return f(*args, **kwargs)
            
        except Exception as e:
            SecurityEnforcer.log_security_event(
                'jwt_validation_failed',
                ip_address=request.remote_addr,
                details=str(e)
            )
            return jsonify({"error": "invalid_token", "message": "Token validation failed"}), 401
    
    return wrapper


def require_role_enhanced(allowed_roles):
    """Enhanced role checking with security logging"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                
                claims = get_jwt() or {}
                user_role = claims.get("role")
                current_user_id = get_jwt_identity()
                
                if user_role not in allowed_roles:
                    SecurityEnforcer.log_security_event(
                        'unauthorized_access_attempt',
                        user_id=current_user_id,
                        ip_address=request.remote_addr,
                        details=f'Required roles: {allowed_roles}, User role: {user_role}'
                    )
                    return jsonify({
                        "error": "insufficient_permissions",
                        "message": "You don't have permission to access this resource"
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                SecurityEnforcer.log_security_event(
                    'authorization_check_failed',
                    ip_address=request.remote_addr,
                    details=str(e)
                )
                return jsonify({"error": "authorization_failed", "message": "Authorization check failed"}), 500
        
        return wrapper
    return decorator


def validate_input_data(required_fields=None, optional_fields=None, max_length=None):
    """Input validation decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            errors = []
            
            # Check required fields
            if required_fields:
                for field in required_fields:
                    if field not in data or data[field] is None or str(data[field]).strip() == '':
                        errors.append(f"{field} is required")
            
            # Check field lengths
            if max_length:
                for field, max_len in max_length.items():
                    if field in data and isinstance(data[field], str) and len(data[field]) > max_len:
                        errors.append(f"{field} must be less than {max_len} characters")
            
            # Check for unexpected fields (optional security measure)
            allowed_fields = set((required_fields or []) + (optional_fields or []))
            if allowed_fields:
                unexpected_fields = set(data.keys()) - allowed_fields
                if unexpected_fields:
                    errors.append(f"Unexpected fields: {', '.join(unexpected_fields)}")
            
            if errors:
                return jsonify({
                    "error": "validation_error",
                    "message": "Invalid input data",
                    "errors": errors
                }), 400
            
            return f(*args, **kwargs)
        
        return wrapper
    return decorator


def sanitize_input():
    """Input sanitization decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            
            # Sanitize string inputs
            def sanitize_string(value):
                if isinstance(value, str):
                    # Remove potential XSS patterns
                    value = value.strip()
                    # Remove script tags and other dangerous HTML
                    import re
                    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
                    value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
                    value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
                return value
            
            # Recursively sanitize data
            def sanitize_data(obj):
                if isinstance(obj, dict):
                    return {key: sanitize_data(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [sanitize_data(item) for item in obj]
                elif isinstance(obj, str):
                    return sanitize_string(obj)
                return obj
            
            request.json = sanitize_data(data) if data else {}
            
            return f(*args, **kwargs)
        
        return wrapper
    return decorator


# Create security log model
class SecurityLog:
    """Model for security event logging"""
    def __init__(self):
        pass
    
    # This would be implemented as a proper SQLAlchemy model
    # For now, we'll log to application logs