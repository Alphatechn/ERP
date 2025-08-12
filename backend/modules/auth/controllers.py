from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from marshmallow import ValidationError
from backend.modules.auth.services import AuthService
from backend.modules.auth.schemas import (
    UserCreateSchema, UserUpdateSchema, LoginSchema, 
    PasswordChangeSchema, PasswordResetSchema, PasswordResetConfirmSchema
)
from backend.cores.utils import handle_api_error

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Enregistre un nouvel utilisateur"""
    try:
        data = request.get_json()
        schema = UserCreateSchema()
        validated_data = schema.load(data)
        
        result = AuthService.register_user(validated_data)
        return jsonify(result), 201
        
    except ValidationError as e:
        return jsonify({'error': True, 'message': 'Données invalides', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': True, 'message': str(e)}), 400
    except Exception as e:
        return handle_api_error(e)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authentifie un utilisateur"""
    try:
        data = request.get_json()
        schema = LoginSchema()
        validated_data = schema.load(data)
        
        remember = request.get_json().get('remember', False)
        
        result = AuthService.authenticate_user(
            validated_data['username'], 
            validated_data['password'],
            remember=remember
        )
        
        if not result:
            return jsonify({'error': True, 'message': 'Identifiants invalides'}), 401
        
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({'error': True, 'message': 'Données invalides', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': True, 'message': str(e)}), 400
    except Exception as e:
        return handle_api_error(e)

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Déconnecte l'utilisateur"""
    try:
        result = AuthService.logout_user()
        return jsonify(result), 200
    except Exception as e:
        return handle_api_error(e)

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Récupère le profil de l'utilisateur connecté"""
    try:
        return jsonify({'user': current_user.to_dict()}), 200
    except Exception as e:
        return handle_api_error(e)

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Met à jour le profil de l'utilisateur connecté"""
    try:
        data = request.get_json()
        schema = UserUpdateSchema()
        validated_data = schema.load(data)
        
        result = AuthService.update_user(current_user.id, validated_data)
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({'error': True, 'message': 'Données invalides', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': True, 'message': str(e)}), 400
    except Exception as e:
        return handle_api_error(e)

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change le mot de passe de l'utilisateur connecté"""
    try:
        data = request.get_json()
        schema = PasswordChangeSchema()
        validated_data = schema.load(data)
        
        result = AuthService.change_password(
            current_user.id,
            validated_data['current_password'],
            validated_data['new_password']
        )
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({'error': True, 'message': 'Données invalides', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': True, 'message': str(e)}), 400
    except Exception as e:
        return handle_api_error(e)

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Demande de réinitialisation de mot de passe"""
    try:
        data = request.get_json()
        schema = PasswordResetSchema()
        validated_data = schema.load(data)
        
        result = AuthService.create_password_reset_session(validated_data['email'])
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({'error': True, 'message': 'Données invalides', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': True, 'message': str(e)}), 400
    except Exception as e:
        return handle_api_error(e)

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Réinitialise le mot de passe avec une session"""
    try:
        data = request.get_json()
        schema = PasswordResetConfirmSchema()
        validated_data = schema.load(data)
        
        result = AuthService.reset_password_with_session(
            validated_data['session_id'],
            validated_data['new_password']
        )
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({'error': True, 'message': 'Données invalides', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': True, 'message': str(e)}), 400
    except Exception as e:
        return handle_api_error(e)

# Routes d'administration (nécessitent des privilèges admin)
@auth_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """Récupère tous les utilisateurs (admin seulement)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'error': True, 'message': 'Accès non autorisé'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', None)
        
        result = AuthService.get_all_users(page, per_page, search)
        return jsonify(result), 200
        
    except Exception as e:
        return handle_api_error(e)

@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """Met à jour un utilisateur (admin seulement)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'error': True, 'message': 'Accès non autorisé'}), 403
        
        data = request.get_json()
        schema = UserUpdateSchema()
        validated_data = schema.load(data)
        
        result = AuthService.update_user(user_id, validated_data)
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({'error': True, 'message': 'Données invalides', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': True, 'message': str(e)}), 400
    except Exception as e:
        return handle_api_error(e)

@auth_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@login_required
def activate_user(user_id):
    """Active un utilisateur (admin seulement)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'error': True, 'message': 'Accès non autorisé'}), 403
        
        result = AuthService.activate_user(user_id)
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': True, 'message': str(e)}), 400
    except Exception as e:
        return handle_api_error(e)

@auth_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@login_required
def deactivate_user(user_id):
    """Désactive un utilisateur (admin seulement)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'error': True, 'message': 'Accès non autorisé'}), 403
        
        result = AuthService.deactivate_user(user_id)
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': True, 'message': str(e)}), 400
    except Exception as e:
        return handle_api_error(e)
