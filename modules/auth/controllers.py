from flask import request, jsonify
from .services import ExtendedAuthService
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from datetime import datetime
from core.database import db
from .models import User, Administrateur, ResponsableRH, Magasinier, Comptable

class ExtendedAuthController:
    @staticmethod
    def register():
        """Enregistrement étendu avec support des différents types d'utilisateurs"""
        try:
            verify_jwt_in_request()

            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validation des champs requis
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'{field} is required'}), 400
            
            user_type = data.get('user_type', 'user').lower()
            
            # Dispatcher vers la méthode appropriée selon le type
            if user_type == 'administrateur':
                user = ExtendedAuthService.register_administrateur(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    niveau_acces=data.get('niveau_acces', 'complet'),
                    ip_autorisees=data.get('ip_autorisees')
                )
            elif user_type == 'responsable_rh':
                user = ExtendedAuthService.register_responsable_rh(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    departement=data.get('departement'),
                    certification_rh=data.get('certification_rh')
                )
            elif user_type == 'magasinier':
                user = ExtendedAuthService.register_magasinier(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    entrepot_assigne=data.get('entrepot_assigne'),
                    niveau_autorisation=data.get('niveau_autorisation', 'lecture')
                )
            elif user_type == 'comptable':
                user = ExtendedAuthService.register_comptable(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    numero_ordre=data.get('numero_ordre'),
                    specialite=data.get('specialite')
                )
            else:
                # Utilisateur standard
                user = ExtendedAuthService.register_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    role_name=data.get('role', 'user'),
                    user_type='user'
                )
            
            return jsonify({
                'message': f'{user_type.capitalize()} created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'user_type': user.user_type,
                    'role': user.role_ref.name if user.role_ref else 'user'
                }
            }), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"[REGISTER_ERROR] {str(e)}")
            return jsonify({'error': 'Invalid or expired token'}), 500

    @staticmethod
    def login():
        """Login étendu avec informations spécifiques au type d'utilisateur"""
        try:
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            
            data = request.get_json()

            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            if not data.get('username') or not data.get('password'):
                return jsonify({'error': 'Username and password are required'}), 400
            
            result = ExtendedAuthService.login_user(
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
        """Déconnexion avec support des types étendus"""
        try:
            verify_jwt_in_request()
            
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Invalid authorization header'}), 400
            
            raw_token = auth_header.split(' ')[1]
            claims = get_jwt()
            username = claims.get('username', 'unknown')
            user_type = claims.get('user_type', 'user')
            
            success, message = ExtendedAuthService.logout_user(raw_token)
            
            if success:
                return jsonify({
                    'message': message,
                    'logged_out_user': username,
                    'user_type': user_type
                }), 200
            else:
                return jsonify({'error': message}), 400
            
        except Exception as e:
            print(f"[LOGOUT_ERROR] {str(e)}")
            return jsonify({'error': 'Invalid or expired token'}), 401

    @staticmethod
    def profile():
        """Profil étendu avec informations spécifiques au type d'utilisateur"""
        try:
            verify_jwt_in_request()
            
            user_id = int(get_jwt_identity())
            user = ExtendedAuthService.get_user_by_id(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            claims = get_jwt()
            permissions = claims.get('permissions', [])
            
            # Informations de base
            profile_data = {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'noms': user.noms,
                    'prenoms': user.prenoms,
                    'telephone': user.telephone,
                    'role': user.role_ref.name if user.role_ref else 'user',
                    'user_type': user.user_type,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat()
                },
                'permissions': permissions,
                'token_info': {
                    'role': claims.get('role'),
                    'email': claims.get('email'),
                    'user_type': claims.get('user_type')
                }
            }
            
            # Ajouter des informations spécifiques selon le type
            if isinstance(user, Administrateur):
                profile_data['admin_info'] = {
                    'niveau_acces': user.niveau_acces,
                    'derniere_connexion_admin': user.derniere_connexion_admin.isoformat() if user.derniere_connexion_admin else None,
                    'ip_autorisees': user.ip_autorisees
                }
            elif isinstance(user, ResponsableRH):
                profile_data['rh_info'] = {
                    'departement': user.departement,
                    'certification_rh': user.certification_rh,
                    'date_certification': user.date_certification.isoformat() if user.date_certification else None
                }
            elif isinstance(user, Magasinier):
                profile_data['warehouse_info'] = {
                    'entrepot_assigne': user.entrepot_assigne,
                    'niveau_autorisation': user.niveau_autorisation,
                    'formations_securite': user.formations_securite
                }
            elif isinstance(user, Comptable):
                profile_data['accounting_info'] = {
                    'numero_ordre': user.numero_ordre,
                    'specialite': user.specialite,
                    'certification_comptable': user.certification_comptable
                }
            
            return jsonify(profile_data), 200
            
        except Exception as e:
            print(f"[PROFILE_ERROR] {str(e)}")
            return jsonify({'error': 'Invalid token'}), 401

    @staticmethod
    def update_profile():
        """Mise à jour du profil avec support des champs spécifiques"""
        try:
            verify_jwt_in_request()
            
            user_id = int(get_jwt_identity())
            user = ExtendedAuthService.get_user_by_id(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Mise à jour des champs de base
            if 'noms' in data:
                user.noms = data['noms']
            if 'prenoms' in data:
                user.prenoms = data['prenoms']
            if 'telephone' in data:
                user.telephone = data['telephone']
            if 'email' in data and data['email'] != user.email:
                # Vérifier que le nouvel email n'existe pas
                if User.query.filter_by(email=data['email']).first():
                    return jsonify({'error': 'Email already exists'}), 400
                user.email = data['email']
            
            # Mise à jour des champs spécifiques selon le type
            if isinstance(user, Administrateur):
                if 'niveau_acces' in data:
                    user.niveau_acces = data['niveau_acces']
                if 'ip_autorisees' in data:
                    user.ip_autorisees = data['ip_autorisees']
                    
            elif isinstance(user, ResponsableRH):
                if 'departement' in data:
                    user.departement = data['departement']
                if 'certification_rh' in data:
                    user.certification_rh = data['certification_rh']
                    
            elif isinstance(user, Magasinier):
                if 'entrepot_assigne' in data:
                    user.entrepot_assigne = data['entrepot_assigne']
                if 'niveau_autorisation' in data:
                    user.niveau_autorisation = data['niveau_autorisation']
                    
            elif isinstance(user, Comptable):
                if 'numero_ordre' in data:
                    user.numero_ordre = data['numero_ordre']
                if 'specialite' in data:
                    user.specialite = data['specialite']
            
            db.session.commit()
            
            return jsonify({
                'message': 'Profile updated successfully',
                'user_type': user.user_type
            }), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"[UPDATE_PROFILE_ERROR] {str(e)}")
            return jsonify({'error': 'Failed to update profile'}), 500

    @staticmethod
    def get_users_by_type():
        """Récupère tous les utilisateurs d'un type donné (admin only)"""
        try:
            verify_jwt_in_request()
            
            claims = get_jwt()
            if not claims.get('permissions') or 'manage_users' not in claims.get('permissions', []):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            user_type = request.args.get('type', '').lower()
            if not user_type:
                return jsonify({'error': 'User type parameter is required'}), 400
            
            users = ExtendedAuthService.get_users_by_type(user_type)
            
            users_data = []
            for user in users:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'user_type': user.user_type,
                    'role': user.role_ref.name if user.role_ref else 'user',
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat()
                }
                
                # Ajouter des infos spécifiques selon le type
                if isinstance(user, Administrateur):
                    user_data['niveau_acces'] = user.niveau_acces
                elif isinstance(user, ResponsableRH):
                    user_data['departement'] = user.departement
                elif isinstance(user, Magasinier):
                    user_data['entrepot_assigne'] = user.entrepot_assigne
                elif isinstance(user, Comptable):
                    user_data['specialite'] = user.specialite
                
                users_data.append(user_data)
            
            return jsonify({
                'message': f'Users of type {user_type} retrieved',
                'count': len(users_data),
                'users': users_data
            }), 200
            
        except Exception as e:
            print(f"[GET_USERS_BY_TYPE_ERROR] {str(e)}")
            return jsonify({'error': 'Failed to retrieve users'}), 500

    @staticmethod
    def promote_user():
        """Promeut un utilisateur vers un nouveau type (admin only)"""
        try:
            verify_jwt_in_request()
            
            claims = get_jwt()
            if not claims.get('permissions') or 'manage_users' not in claims.get('permissions', []):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            user_id = data.get('user_id')
            new_user_type = data.get('new_user_type', '').lower()
            type_specific_data = data.get('type_specific_data', {})
            
            if not user_id or not new_user_type:
                return jsonify({'error': 'user_id and new_user_type are required'}), 400
            
            updated_user = ExtendedAuthService.promote_user_to_type(
                user_id=user_id,
                new_user_type=new_user_type,
                **type_specific_data
            )
            
            return jsonify({
                'message': f'User promoted to {new_user_type} successfully',
                'user': {
                    'id': updated_user.id,
                    'username': updated_user.username,
                    'user_type': updated_user.user_type,
                    'role': updated_user.role_ref.name if updated_user.role_ref else 'user'
                }
            }), 200
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"[PROMOTE_USER_ERROR] {str(e)}")
            return jsonify({'error': 'Failed to promote user'}), 500

    @staticmethod
    def get_user_types():
        """Retourne la liste des types d'utilisateurs disponibles"""
        try:
            user_types = [
                {
                    'type': 'user',
                    'name': 'Utilisateur Standard',
                    'description': 'Utilisateur de base avec permissions limitées'
                },
                {
                    'type': 'administrateur',
                    'name': 'Administrateur',
                    'description': 'Gestion complète des utilisateurs et du système'
                },
                {
                    'type': 'responsable_rh',
                    'name': 'Responsable RH',
                    'description': 'Gestion des employés et des ressources humaines'
                },
                {
                    'type': 'magasinier',
                    'name': 'Magasinier',
                    'description': 'Gestion des stocks et opérations d\'entrepôt'
                },
                {
                    'type': 'comptable',
                    'name': 'Comptable',
                    'description': 'Gestion comptable et financière'
                }
            ]
            
            return jsonify({
                'message': 'Available user types',
                'user_types': user_types
            }), 200
            
        except Exception as e:
            print(f"[GET_USER_TYPES_ERROR] {str(e)}")
            return jsonify({'error': 'Failed to retrieve user types'}), 500

    @staticmethod
    def my_sessions():
        """Sessions de l'utilisateur connecté - hérite de l'ancien contrôleur"""
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
            
            sessions_info = ExtendedAuthService.get_user_active_sessions(user_id)
            
            if not sessions_info:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({
                'message': 'Sessions information retrieved',
                'sessions': sessions_info
            }), 200
            
        except Exception as e:
            return jsonify({'error': 'Invalid token'}), 401