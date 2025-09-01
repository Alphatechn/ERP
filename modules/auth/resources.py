
from flask_restful import Resource, reqparse
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from flasgger import swag_from
from .services import ExtendedAuthService
from .models import User, Administrateur, ResponsableRH, Magasinier, Comptable
from core.utils import permission_required
from datetime import datetime

class RegisterResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', required=True, help='Username is required')
        self.parser.add_argument('email', required=True, help='Email is required')
        self.parser.add_argument('password', required=True, help='Password is required')
        self.parser.add_argument('user_type', default='user', help='User type')
        self.parser.add_argument('role', default='user', help='User role')
        
        # Champs spécifiques administrateur
        self.parser.add_argument('niveau_acces', help='Admin access level')
        self.parser.add_argument('ip_autorisees', help='Authorized IPs for admin')
        
        # Champs spécifiques RH
        self.parser.add_argument('departement', help='HR department')
        self.parser.add_argument('certification_rh', help='HR certification')
        
        # Champs spécifiques magasinier
        self.parser.add_argument('entrepot_assigne', help='Assigned warehouse')
        self.parser.add_argument('niveau_autorisation', default='lecture', help='Authorization level')
        
        # Champs spécifiques comptable
        self.parser.add_argument('numero_ordre', help='Accountant order number')
        self.parser.add_argument('specialite', help='Accounting specialty')

    @swag_from({
        'tags': ['Authentication'],
        'summary': 'Enregistrer un nouvel utilisateur',
        'description': 'Crée un utilisateur avec un type spécifique (user, administrateur, responsable_rh, magasinier, comptable)',
        'security': [{'Bearer': []}],
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'required': True,
                'schema': {
                    'type': 'object',
                    'required': ['username', 'email', 'password'],
                    'properties': {
                        'username': {'type': 'string', 'example': 'john_doe'},
                        'email': {'type': 'string', 'example': 'john@example.com'},
                        'password': {'type': 'string', 'example': 'password123'},
                        'user_type': {
                            'type': 'string',
                            'enum': ['user', 'administrateur', 'responsable_rh', 'magasinier', 'comptable'],
                            'default': 'user',
                            'example': 'user'
                        },
                        'role': {'type': 'string', 'default': 'user'},
                        # Champs spécifiques administrateur
                        'niveau_acces': {'type': 'string', 'enum': ['complet', 'partiel']},
                        'ip_autorisees': {'type': 'string', 'example': '["192.168.1.100"]'},
                        # Champs spécifiques RH
                        'departement': {'type': 'string', 'example': 'Direction RH'},
                        'certification_rh': {'type': 'string', 'example': 'CGRH Niveau 2'},
                        # Champs spécifiques magasinier
                        'entrepot_assigne': {'type': 'string', 'example': 'Entrepôt Central'},
                        'niveau_autorisation': {'type': 'string', 'enum': ['lecture', 'ecriture', 'supervision']},
                        # Champs spécifiques comptable
                        'numero_ordre': {'type': 'string', 'example': 'CMP2024001'},
                        'specialite': {'type': 'string', 'example': 'Comptabilité générale'}
                    }
                }
            }
        ],
        'responses': {
            201: {
                'description': 'Utilisateur créé avec succès',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'user': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'username': {'type': 'string'},
                                'email': {'type': 'string'},
                                'user_type': {'type': 'string'},
                                'role': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            400: {'description': 'Données invalides'},
            500: {'description': 'Erreur serveur'}
        }
    })

    @permission_required('manage_users')
    def post(self):
        """Enregistrement étendu avec support des différents types d'utilisateurs"""
        try:
            args = self.parser.parse_args()
            user_type = args['user_type'].lower()
            
            # Dispatcher vers la méthode appropriée selon le type
            if user_type == 'administrateur':
                user = ExtendedAuthService.register_administrateur(
                    username=args['username'],
                    email=args['email'],
                    password=args['password'],
                    niveau_acces=args.get('niveau_acces', 'complet'),
                    ip_autorisees=args.get('ip_autorisees')
                )
            elif user_type == 'responsable_rh':
                user = ExtendedAuthService.register_responsable_rh(
                    username=args['username'],
                    email=args['email'],
                    password=args['password'],
                    departement=args.get('departement'),
                    certification_rh=args.get('certification_rh')
                )
            elif user_type == 'magasinier':
                user = ExtendedAuthService.register_magasinier(
                    username=args['username'],
                    email=args['email'],
                    password=args['password'],
                    entrepot_assigne=args.get('entrepot_assigne'),
                    niveau_autorisation=args.get('niveau_autorisation', 'lecture')
                )
            elif user_type == 'comptable':
                user = ExtendedAuthService.register_comptable(
                    username=args['username'],
                    email=args['email'],
                    password=args['password'],
                    numero_ordre=args.get('numero_ordre'),
                    specialite=args.get('specialite')
                )
            else:
                # Utilisateur standard
                user = ExtendedAuthService.register_user(
                    username=args['username'],
                    email=args['email'],
                    password=args['password'],
                    role_name=args.get('role', 'user'),
                    user_type='user'
                )
            
            return {
                'message': f'{user_type.capitalize()} created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'user_type': user.user_type,
                    'role': user.role_ref.name if user.role_ref else 'user'
                }
            }, 201
            
        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            return {'error': 'Registration failed'}, 500

class LoginResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', required=True, help='Username is required')
        self.parser.add_argument('password', required=True, help='Password is required')

    @swag_from({
        'tags': ['Authentication'],
        'summary': 'Connexion utilisateur',
        'description': 'Authentifie un utilisateur et retourne un token JWT avec informations étendues selon le type',
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'required': True,
                'schema': {
                    'type': 'object',
                    'required': ['username', 'password'],
                    'properties': {
                        'username': {'type': 'string', 'example': 'john_doe'},
                        'password': {'type': 'string', 'example': 'password123'}
                    }
                }
            }
        ],
        'responses': {
            200: {
                'description': 'Connexion réussie',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'access_token': {'type': 'string'},
                        'user': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'username': {'type': 'string'},
                                'email': {'type': 'string'},
                                'role': {'type': 'string'},
                                'permissions': {'type': 'array', 'items': {'type': 'string'}},
                                'user_type': {'type': 'string'},
                                'noms': {'type': 'string'},
                                'prenoms': {'type': 'string'},
                                'telephone': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            401: {'description': 'Identifiants invalides'},
            500: {'description': 'Erreur de connexion'}
        }
    })    

    def post(self):
        """Login étendu avec informations spécifiques au type d'utilisateur"""
        try:
            args = self.parser.parse_args()
            
            result = ExtendedAuthService.login_user(
                username=args['username'],
                password=args['password']
            )
            
            if not result:
                return {'error': 'Invalid credentials'}, 401
            
            return {
                'message': 'Login successful',
                'access_token': result['access_token'],
                'user': result['user_info']
            }, 200
            
        except Exception as e:
            return {'error': 'Login failed'}, 500

class LogoutResource(Resource):

    @swag_from({
        'tags': ['Authentication'],
        'summary': 'Déconnexion utilisateur',
        'description': 'Révoque le token JWT en cours et déconnecte l\'utilisateur',
        'security': [{'Bearer': []}],
        'responses': {
            200: {
                'description': 'Déconnexion réussie',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'logged_out_user': {'type': 'string'},
                        'user_type': {'type': 'string'}
                    }
                }
            },
            400: {'description': 'Header d\'autorisation invalide'},
            401: {'description': 'Token invalide ou expiré'}
        }
    })

    def post(self):
        """Déconnexion avec support des types étendus"""
        try:
            verify_jwt_in_request()
            
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {'error': 'Invalid authorization header'}, 400
            
            raw_token = auth_header.split(' ')[1]
            claims = get_jwt()
            username = claims.get('username', 'unknown')
            user_type = claims.get('user_type', 'user')
            
            success, message = ExtendedAuthService.logout_user(raw_token)
            
            if success:
                return {
                    'message': message,
                    'logged_out_user': username,
                    'user_type': user_type
                }, 200
            else:
                return {'error': message}, 400
            
        except Exception as e:
            return {'error': 'Invalid or expired token'}, 401

class ProfileResource(Resource):

    @swag_from({
        'tags': ['Authentication'],
        'summary': 'Récupérer le profil utilisateur',
        'description': 'Récupère le profil complet avec informations spécifiques au type d\'utilisateur',
        'security': [{'Bearer': []}],
        'responses': {
            200: {
                'description': 'Profil récupéré avec succès',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'user': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'username': {'type': 'string'},
                                'email': {'type': 'string'},
                                'user_type': {'type': 'string'},
                                'role': {'type': 'string'},
                                'noms': {'type': 'string'},
                                'prenoms': {'type': 'string'},
                                'telephone': {'type': 'string'}
                            }
                        },
                        'permissions': {'type': 'array', 'items': {'type': 'string'}},
                        'admin_info': {'type': 'object'},
                        'rh_info': {'type': 'object'},
                        'warehouse_info': {'type': 'object'},
                        'accounting_info': {'type': 'object'}
                    }
                }
            },
            401: {'description': 'Token invalide'},
            404: {'description': 'Utilisateur non trouvé'}
        }
    })

    def get(self):
        """Profil étendu avec informations spécifiques au type d'utilisateur"""
        try:
            verify_jwt_in_request()
            
            user_id = int(get_jwt_identity())
            user = ExtendedAuthService.get_user_by_id(user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
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
            
            return profile_data, 200
            
        except Exception as e:
            return {'error': 'Invalid token'}, 401

    def put(self):
        """Mise à jour du profil avec support des champs spécifiques"""
        try:
            verify_jwt_in_request()
            
            user_id = int(get_jwt_identity())
            user = ExtendedAuthService.get_user_by_id(user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            parser = reqparse.RequestParser()
            parser.add_argument('noms')
            parser.add_argument('prenoms')
            parser.add_argument('telephone')
            parser.add_argument('email')
            
            # Champs spécifiques selon le type
            if isinstance(user, Administrateur):
                parser.add_argument('niveau_acces')
                parser.add_argument('ip_autorisees')
            elif isinstance(user, ResponsableRH):
                parser.add_argument('departement')
                parser.add_argument('certification_rh')
            elif isinstance(user, Magasinier):
                parser.add_argument('entrepot_assigne')
                parser.add_argument('niveau_autorisation')
            elif isinstance(user, Comptable):
                parser.add_argument('numero_ordre')
                parser.add_argument('specialite')
            
            args = parser.parse_args()
            
            # Mise à jour des champs de base
            for field in ['noms', 'prenoms', 'telephone']:
                if args[field] is not None:
                    setattr(user, field, args[field])
            
            if args['email'] and args['email'] != user.email:
                # Vérifier que le nouvel email n'existe pas
                if User.query.filter_by(email=args['email']).first():
                    return {'error': 'Email already exists'}, 400
                user.email = args['email']
            
            # Mise à jour des champs spécifiques selon le type
            if isinstance(user, Administrateur):
                if args.get('niveau_acces'):
                    user.niveau_acces = args['niveau_acces']
                if args.get('ip_autorisees'):
                    user.ip_autorisees = args['ip_autorisees']
                    
            elif isinstance(user, ResponsableRH):
                if args.get('departement'):
                    user.departement = args['departement']
                if args.get('certification_rh'):
                    user.certification_rh = args['certification_rh']
                    
            elif isinstance(user, Magasinier):
                if args.get('entrepot_assigne'):
                    user.entrepot_assigne = args['entrepot_assigne']
                if args.get('niveau_autorisation'):
                    user.niveau_autorisation = args['niveau_autorisation']
                    
            elif isinstance(user, Comptable):
                if args.get('numero_ordre'):
                    user.numero_ordre = args['numero_ordre']
                if args.get('specialite'):
                    user.specialite = args['specialite']
            
            from core.database import db
            db.session.commit()
            
            return {
                'message': 'Profile updated successfully',
                'user_type': user.user_type
            }, 200
            
        except Exception as e:
            from core.database import db
            db.session.rollback()
            return {'error': 'Failed to update profile'}, 500

class UsersByTypeResource(Resource):
    @permission_required('manage_users')
    def get(self):
        """Récupère tous les utilisateurs d'un type donné (admin only)"""
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('type', required=True, help='User type is required')
            args = parser.parse_args()
            
            user_type = args['type'].lower()
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
            
            return {
                'message': f'Users of type {user_type} retrieved',
                'count': len(users_data),
                'users': users_data
            }, 200
            
        except Exception as e:
            return {'error': 'Failed to retrieve users'}, 500

class UserPromoteResource(Resource):
    @permission_required('manage_users')
    def post(self):
        """Promeut un utilisateur vers un nouveau type (admin only)"""
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('user_id', type=int, required=True, help='User ID is required')
            parser.add_argument('new_user_type', required=True, help='New user type is required')
            parser.add_argument('type_specific_data', type=dict, default={})
            
            args = parser.parse_args()
            
            updated_user = ExtendedAuthService.promote_user_to_type(
                user_id=args['user_id'],
                new_user_type=args['new_user_type'].lower(),
                **args['type_specific_data']
            )
            
            return {
                'message': f'User promoted to {args["new_user_type"]} successfully',
                'user': {
                    'id': updated_user.id,
                    'username': updated_user.username,
                    'user_type': updated_user.user_type,
                    'role': updated_user.role_ref.name if updated_user.role_ref else 'user'
                }
            }, 200
            
        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            return {'error': 'Failed to promote user'}, 500

class UserTypesResource(Resource):
    def get(self):
        """Retourne la liste des types d'utilisateurs disponibles"""
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
        
        return {
            'message': 'Available user types',
            'user_types': user_types
        }, 200

class TestTokenResource(Resource):
    def get(self):
        """Test de validation de token avec informations étendues"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            user_id = get_jwt_identity()
            
            return {
                'message': 'Token is valid!',
                'user_id': user_id,
                'username': claims.get('username'),
                'user_type': claims.get('user_type', 'user'),
                'role': claims.get('role'),
                'permissions': claims.get('permissions', []),
                'jti': claims.get('jti', '')[:8] + '...'
            }, 200
        except Exception as e:
            return {'error': f'Token error: {str(e)}'}, 401

class HealthResource(Resource):

    @swag_from({
        'tags': ['Système'],
        'summary': 'Health check du service d\'authentification',
        'description': 'Vérifie l\'état du service d\'authentification étendu',
        'responses': {
            200: {
                'description': 'Service opérationnel',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string'},
                        'timestamp': {'type': 'string'},
                        'supported_user_types': {
                            'type': 'array',
                            'items': {'type': 'string'}
                        }
                    }
                }
            }
        }
    })

    def get(self):
        """Check de santé du module d'authentification étendu"""
        return {
            'status': 'Extended Auth module running',
            'timestamp': datetime.utcnow().isoformat(),
            'supported_user_types': ['user', 'administrateur', 'responsable_rh', 'magasinier', 'comptable']
        }, 200

# Ressources métier spécifiques par type d'utilisateur

class AdminUsersResource(Resource):

    @swag_from({
        'tags': ['Administration'],
        'summary': '[ADMIN] Récupérer tous les utilisateurs',
        'description': 'Récupère la liste complète des utilisateurs du système (administrateurs uniquement)',
        'security': [{'Bearer': []}],
        'responses': {
            200: {
                'description': 'Liste des utilisateurs récupérée',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'total_users': {'type': 'integer'},
                        'users': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'id': {'type': 'integer'},
                                    'username': {'type': 'string'},
                                    'email': {'type': 'string'},
                                    'user_type': {'type': 'string'},
                                    'role': {'type': 'string'},
                                    'is_active': {'type': 'boolean'}
                                }
                            }
                        }
                    }
                }
            },
            403: {'description': 'Accès réservé aux administrateurs'},
            500: {'description': 'Erreur système'}
        }
    })

    def get(self):
        """[ADMINISTRATEUR] Récupère tous les utilisateurs avec détails"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            # Vérification du type et des permissions
            if claims.get('user_type') != 'administrateur':
                return {'error': 'Access restricted to administrators'}, 403
                
            if 'manage_users' not in claims.get('permissions', []):
                return {'error': 'Insufficient permissions'}, 403
            
            users = User.query.all()
            
            users_data = []
            for user in users:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'user_type': user.user_type,
                    'role': user.role_ref.name if user.role_ref else 'user',
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat(),
                    'last_login': None  # À implémenter si besoin
                }
                users_data.append(user_data)
            
            return {
                'message': 'All users retrieved by administrator',
                'total_users': len(users_data),
                'users': users_data,
                'retrieved_by': claims.get('username')
            }, 200
            
        except Exception as e:
            return {'error': f'Admin operation failed: {str(e)}'}, 500

class HREmployeesResource(Resource):
    def get(self):
        """[RESPONSABLE RH] Récupère les informations des employés"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            if claims.get('user_type') != 'responsable_rh':
                return {'error': 'Access restricted to HR managers'}, 403
                
            if 'manage_hr' not in claims.get('permissions', []):
                return {'error': 'Insufficient HR permissions'}, 403
            
            # Logique RH - récupérer les employés (non-admin)
            employees = User.query.filter(User.user_type.in_(['user', 'magasinier', 'comptable'])).all()
            
            employees_data = []
            for emp in employees:
                emp_data = {
                    'id': emp.id,
                    'username': emp.username,
                    'noms': emp.noms,
                    'prenoms': emp.prenoms,
                    'email': emp.email,
                    'telephone': emp.telephone,
                    'user_type': emp.user_type,
                    'role': emp.role_ref.name if emp.role_ref else 'user',
                    'is_active': emp.is_active,
                    'created_at': emp.created_at.isoformat()
                }
                employees_data.append(emp_data)
            
            return {
                'message': 'Employees data retrieved by HR',
                'total_employees': len(employees_data),
                'employees': employees_data,
                'hr_manager': claims.get('username')
            }, 200
            
        except Exception as e:
            return {'error': f'HR operation failed: {str(e)}'}, 500

class WarehouseInventoryResource(Resource):
    def get(self):
        """[MAGASINIER] Récupère l'état de l'inventaire"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            if claims.get('user_type') != 'magasinier':
                return {'error': 'Access restricted to warehouse staff'}, 403
                
            if 'warehouse_operations' not in claims.get('permissions', []):
                return {'error': 'Insufficient warehouse permissions'}, 403
            
            # Simulation d'inventaire
            user_id = int(get_jwt_identity())
            magasinier = Magasinier.query.get(user_id)
            
            inventory_data = {
                'entrepot': magasinier.entrepot_assigne if magasinier else 'Non assigné',
                'niveau_autorisation': magasinier.niveau_autorisation if magasinier else 'lecture',
                'total_produits': 150,  # Simulation
                'alertes_stock_bas': 12,
                'mouvements_aujourd_hui': 28,
                'derniere_maj': datetime.utcnow().isoformat()
            }
            
            return {
                'message': 'Inventory data retrieved',
                'inventory': inventory_data,
                'magasinier': claims.get('username')
            }, 200
            
        except Exception as e:
            return {'error': f'Warehouse operation failed: {str(e)}'}, 500

class AccountingReportsResource(Resource):
    def get(self):
        """[COMPTABLE] Récupère les rapports comptables"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            if claims.get('user_type') != 'comptable':
                return {'error': 'Access restricted to accountants'}, 403
                
            if 'manage_accounting' not in claims.get('permissions', []):
                return {'error': 'Insufficient accounting permissions'}, 403
            
            # Simulation de données comptables
            user_id = int(get_jwt_identity())
            comptable = Comptable.query.get(user_id)
            
            reports_data = {
                'specialite': comptable.specialite if comptable else 'Générale',
                'numero_ordre': comptable.numero_ordre if comptable else 'N/A',
                'rapports_disponibles': [
                    'Bilan mensuel',
                    'Compte de résultat',
                    'Journal des ventes',
                    'Rapprochement bancaire'
                ],
                'derniers_traitements': 45,
                'en_attente_validation': 8,
                'derniere_cloture': '2024-07-31'
            }
            
            return {
                'message': 'Accounting reports retrieved',
                'reports': reports_data,
                'comptable': claims.get('username')
            }, 200
            
        except Exception as e:
            return {'error': f'Accounting operation failed: {str(e)}'}, 500

class InitSystemResource(Resource):

    @swag_from({
        'tags': ['Système'],
        'summary': 'Initialiser le système étendu',
        'description': 'Initialise les rôles, permissions et utilisateurs de test du système',
        'responses': {
            200: {
                'description': 'Système initialisé avec succès',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'users_created': {
                            'type': 'array',
                            'items': {'type': 'string'}
                        },
                        'warning': {'type': 'string'}
                    }
                }
            },
            500: {'description': 'Erreur d\'initialisation'}
        }
    })
    
    def post(self):
        """Initialise le système étendu avec rôles, permissions et utilisateurs de test"""
        try:
            ExtendedAuthService.init_extended_roles_and_permissions()
            
            return {
                'message': 'Extended authentication system initialized successfully',
                'users_created': [
                    'superadmin (administrateur)',
                    'rh_manager (responsable_rh)', 
                    'warehouse_user (magasinier)',
                    'comptable_user (comptable)'
                ],
                'warning': 'Change default passwords immediately in production'
            }, 200
            
        except Exception as e:
            return {'error': f'Initialization failed: {str(e)}'}, 500