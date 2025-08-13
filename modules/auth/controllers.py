from flask import request, jsonify
from .services import AuthService
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity, decode_token
from datetime import datetime
from core.database import db
from .models import User
class AuthController:
    @staticmethod
    def register():
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validation des champs requis
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'{field} is required'}), 400
            
            user = AuthService.register_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                role_name=data.get('role', 'user')
            )
            return jsonify({
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500

    @staticmethod
    def login():
        try:
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            
            data = request.get_json()

            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            if not data.get('username') or not data.get('password'):
                return jsonify({'error': 'Username and password are required'}), 400
            
            result = AuthService.login_user(
                username=data['username'],
                password=data['password']
            )
            
            if not result:
                return jsonify({'error': 'Invalid credentials'}), 401
            
            return jsonify({
                'message': 'Login successful',
                'access_token': result['access_token'],
                'user': result['user_info']
            }), 200
            
        except Exception as e:
            print(f"[LOGIN_ERROR] {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    @staticmethod
    def logout():
        """Déconnecte l'utilisateur en révoquant son token"""
        try:
            # Vérifier que le token est présent et valide
            verify_jwt_in_request()
            
            # Récupérer le token depuis le header Authorization
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Invalid authorization header'}), 400
            
            # Extraire le token (après "Bearer ")
            raw_token = auth_header.split(' ')[1]
            
            # Récupérer les infos utilisateur depuis le token
            claims = get_jwt()
            username = claims.get('username', 'unknown')
            
            # Révoquer le token
            success, message = AuthService.logout_user(raw_token)
            
            if success:
                return jsonify({
                    'message': message,
                    'logged_out_user': username
                }), 200
            else:
                return jsonify({'error': message}), 400
            
        except Exception as e:
            print(f"[LOGOUT_ERROR] {str(e)}")
            return jsonify({'error': 'Invalid or expired token'}), 401

    @staticmethod
    def profile():
        """Récupère le profil de l'utilisateur connecté"""
        try:
            verify_jwt_in_request()
            
            # Récupérer l'ID utilisateur depuis le token
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Récupérer les permissions depuis le token (plus rapide)
            claims = get_jwt()
            permissions = claims.get('permissions', [])
            
            return jsonify({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role_ref.name if user.role_ref else 'user',
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat()
                },
                'permissions': permissions,
                'token_info': {
                    'role': claims.get('role'),
                    'email': claims.get('email')
                }
            }), 200
            
        except Exception as e:
            print(f"[PROFILE_ERROR] {str(e)}")
            return jsonify({'error': 'Invalid token'}), 401

    @staticmethod
    def my_sessions():
        """Récupère les informations sur les sessions de l'utilisateur connecté"""
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
            
            sessions_info = AuthService.get_user_active_sessions(user_id)
            
            if not sessions_info:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({
                'message': 'Sessions information retrieved',
                'sessions': sessions_info
            }), 200
            
        except Exception as e:
            return jsonify({'error': 'Invalid token'}), 401