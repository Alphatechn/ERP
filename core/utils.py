from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if permission not in claims.get('permissions', []):
                return {'error': 'Permission denied'}, 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator