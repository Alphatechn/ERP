from flask import Blueprint, jsonify
from .controllers import AuthController
from flask_jwt_extended import verify_jwt_in_request

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    return AuthController.register()

@auth_bp.route('/login', methods=['POST'])
def login():
    return AuthController.login()

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Déconnecte l'utilisateur
    Nécessite: Authorization: Bearer <token>
    """
    return AuthController.logout()

@auth_bp.route('/profile', methods=['GET'])
def profile():
    """
    Récupère le profil utilisateur
    Nécessite: Authorization: Bearer <token>
    """
    return AuthController.profile()

@auth_bp.route('/sessions', methods=['GET'])
def my_sessions():
    """
    Récupère les infos sur les sessions de l'utilisateur
    Nécessite: Authorization: Bearer <token>
    """
    return AuthController.my_sessions()

@auth_bp.route('/health', methods=['GET'])
def health():
    return {
        'status': 'Auth module running',
        'timestamp': datetime.utcnow().isoformat()
    }, 200


@auth_bp.route('/test-token', methods=['GET'])
def test_token():
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        return jsonify({
            'message': 'Token is valid! 🎉',
            'user_id': get_jwt_identity(),
            'username': claims.get('username'),
            'jti': claims.get('jti', '')[:8] + '...'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Token error: {str(e)}'}), 401