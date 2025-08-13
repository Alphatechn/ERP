from flask import request, jsonify
from .services import AuthService

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
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            if not data.get('username') or not data.get('password'):
                return jsonify({'error': 'Username and password are required'}), 400
            
            token = AuthService.login_user(
                username=data['username'],
                password=data['password']
            )
            
            if not token:
                return jsonify({'error': 'Invalid credentials'}), 401
                
            return jsonify({'access_token': token}), 200
            
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
