from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash
from core.database import db
from .models import User, Role, Permission
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
        
        # Créer le token avec les claims étendus
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'role': user.role_ref.name if user.role_ref else 'user',
                'permissions': permissions,
                'email': user.email
            }
        )
        
        return {
            'access_token': access_token,
            'user_info': {
                'id': user.id,
                'username': user.username,
                'role': user.role_ref.name if user.role_ref else 'user',
                'permissions': permissions
            }
        }

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