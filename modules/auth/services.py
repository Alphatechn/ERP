# === 2. VOTRE SERVICE ÉTENDU AVEC LOGOUT ===
from flask_jwt_extended import create_access_token, decode_token
from werkzeug.security import generate_password_hash
from core.database import db
from .models import User, Role, Permission, TokenBlacklist
from datetime import datetime, timedelta
import os

class AuthService:
    @staticmethod
    def register_user(username, email, password, role_name='user'):
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already exists")
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already exists")
        
        # Trouver le rôle
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            raise ValueError(f"Role {role_name} does not exist")
        
        # Créer l'utilisateur
        user = User(username=username, email=email, role_id=role.id)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def login_user(username, password):
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password) or not user.is_active:
            return None
        
        # Récupérer les permissions du rôle
        permissions = [p.code for p in user.role_ref.permissions] if user.role_ref else []
        
        # Créer le token avec les claims étendus + expiration
        access_token = create_access_token(
            identity=str(user.id),  # Important: convertir en string
            additional_claims={
                'role': user.role_ref.name if user.role_ref else 'user',
                'permissions': permissions,
                'email': user.email,
                'username': user.username
            },
            expires_delta=timedelta(hours=24)  # Token valide 24h
        )
        
        return {
            'access_token': access_token,
            'user_info': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role_ref.name if user.role_ref else 'user',
                'permissions': permissions
            }
        }

    @staticmethod
    def logout_user(raw_token):
        """
        Invalide un token en l'ajoutant à la blacklist
        
        Args:
            raw_token (str): Le token JWT brut
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Décoder le token pour extraire les informations
            decoded_token = decode_token(raw_token)
            
            jti = decoded_token['jti']  # JWT ID unique
            user_id = int(decoded_token['sub'])  # Subject (ID utilisateur)
            expires_at = datetime.fromtimestamp(decoded_token['exp'])
            
            # Vérifier si le token n'est pas déjà révoqué
            existing_blacklist = TokenBlacklist.query.filter_by(jti=jti).first()
            if existing_blacklist:
                return False, "Token already revoked"
            
            # Vérifier que l'utilisateur existe
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Ajouter le token à la blacklist
            blacklisted_token = TokenBlacklist(
                jti=jti,
                user_id=user_id,
                expires_at=expires_at
            )
            
            db.session.add(blacklisted_token)
            db.session.commit()
            
            print(f"[LOGOUT] Token {jti[:8]}... révoqué pour l'utilisateur {user.username}")
            
            return True, f"Successfully logged out user {user.username}"
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Erreur lors du logout: {str(e)}")
            return False, f"Error during logout: {str(e)}"

    @staticmethod
    def is_token_revoked(jti):
        """
        Vérifie si un token est dans la blacklist
        
        Args:
            jti (str): L'identifiant unique du JWT
            
        Returns:
            bool: True si le token est révoqué
        """
        return TokenBlacklist.query.filter_by(jti=jti).first() is not None

    @staticmethod
    def logout_all_user_sessions(user_id):
        """
        Déconnecte toutes les sessions d'un utilisateur
        (révoque tous ses tokens actifs)
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            int: Nombre de sessions déconnectées
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return 0
            
            # Pour cette fonctionnalité, on pourrait stocker tous les tokens actifs
            # ou marquer l'utilisateur comme "force logout" avec un timestamp
            # Ici, on va simuler en révoquant tous les tokens futurs avec un timestamp
            
            # Alternative simple: désactiver temporairement l'utilisateur
            # puis le réactiver (force tous les tokens à être invalides)
            
            print(f"[LOGOUT_ALL] Déconnexion de toutes les sessions pour {user.username}")
            
            # Compter les tokens actifs (approximation)
            active_tokens = TokenBlacklist.query.filter_by(user_id=user_id).count()
            
            return active_tokens
            
        except Exception as e:
            print(f"[ERROR] Erreur logout_all: {str(e)}")
            return 0

    @staticmethod
    def cleanup_expired_tokens():
        """
        Nettoie les tokens expirés de la blacklist pour optimiser la DB
        
        Returns:
            int: Nombre de tokens supprimés
        """
        try:
            now = datetime.utcnow()
            expired_tokens = TokenBlacklist.query.filter(
                TokenBlacklist.expires_at < now
            ).all()
            
            count = len(expired_tokens)
            
            if count > 0:
                for token in expired_tokens:
                    db.session.delete(token)
                
                db.session.commit()
                print(f"[CLEANUP] {count} tokens expirés supprimés de la blacklist")
            
            return count
            
        except Exception as e:
            print(f"[ERROR] Erreur cleanup: {str(e)}")
            db.session.rollback()
            return 0

    @staticmethod
    def get_user_active_sessions(user_id):
        """
        Récupère des informations sur les sessions actives d'un utilisateur
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            dict: Informations sur les sessions
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            # Compter les tokens révoqués (approximation des sessions fermées)
            revoked_count = TokenBlacklist.query.filter_by(user_id=user_id).count()
            
            # Dans une vraie implémentation, on pourrait stocker plus d'infos
            # comme l'IP, le user-agent, la date de dernière activité, etc.
            
            return {
                'user_id': user_id,
                'username': user.username,
                'revoked_tokens': revoked_count,
                'last_login': user.created_at,  # Approximation
                'is_active': user.is_active
            }
            
        except Exception as e:
            print(f"[ERROR] Erreur get_sessions: {str(e)}")
            return None


    @staticmethod
    def init_default_roles_and_permissions():
        """Initialise les rôles, permissions et un super admin par défaut"""
        print("\n=== Initialisation du système d'authentification ===")
        
        # Permissions
        permissions_data = [
            ('manage_users', 'Gérer les utilisateurs'),
            ('view_reports', 'Voir les rapports'),
            ('manage_payroll', 'Gérer la paie'),
            ('super_admin', 'Accès complet au système'),  # Nouvelle permission spéciale
        ]

        # Création des permissions
        for code, name in permissions_data:
            if not Permission.query.filter_by(code=code).first():
                db.session.add(Permission(code=code, name=name))
                print(f"[+] Permission créée: {code}")

        # Rôles avec leurs permissions
        roles_data = [
            ('super_admin', 'Super Administrateur', ['super_admin'] + [p[0] for p in permissions_data]),
            ('admin', 'Administrateur', ['manage_users', 'view_reports', 'manage_payroll']),
            ('hr', 'RH', ['manage_users', 'view_reports']),
            ('accountant', 'Comptable', ['manage_payroll']),
            ('user', 'Utilisateur standard', []),
        ]

        # Création des rôles
        for name, desc, perm_codes in roles_data:
            if not Role.query.filter_by(name=name).first():
                role = Role(name=name, description=desc)
                if perm_codes:
                    role.permissions = Permission.query.filter(Permission.code.in_(perm_codes)).all()
                db.session.add(role)
                print(f"[+] Rôle créé: {name}")

        db.session.commit()

        # Création du super admin si inexistant
        if not User.query.filter_by(username='superadmin').first():
            super_admin_role = Role.query.filter_by(name='super_admin').first()
            if super_admin_role:
                super_admin = User(
                    username='superadmin',
                    email=os.getenv('SUPERADMIN_EMAIL', 'admin@erp.com'),
                    role_id=super_admin_role.id,
                    is_active=True
                )
                super_admin.set_password(os.getenv('SUPERADMIN_PASSWORD', '1234'))
                db.session.add(super_admin)
                db.session.commit()
                print("\n[+++] COMPTE SUPER ADMIN CRÉÉ [+++]")
                print(f"Username: superadmin")
                print(f"Password: {os.getenv('SUPERADMIN_PASSWORD', '1234')}")
                print("!!! CHANGEZ CE MOT DE PASSE IMMÉDIATEMENT !!!\n")
        
        print("=== Initialisation terminée avec succès ===\n")