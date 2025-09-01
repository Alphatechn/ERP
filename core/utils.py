# File: core/utils.py (Updated for Flask-RESTful)
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def permission_required(permission):
    """Décorateur pour vérifier les permissions avec Flask-RESTful"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                if permission not in claims.get('permissions', []):
                    return {'error': 'Permission denied'}, 403
                return f(*args, **kwargs)
            except Exception as e:
                return {'error': 'Invalid or expired token'}, 401
        return decorated_function
    return decorator