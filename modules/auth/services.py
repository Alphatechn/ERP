
from datetime import datetime
from core.database import db
from flask_jwt_extended import create_access_token, decode_token
from werkzeug.security import generate_password_hash
from core.database import db
from .models import (
    User, Role, Permission, TokenBlacklist, 
    Administrateur, ResponsableRH, Magasinier, Comptable,
    UserFactory, UserTypePermission
)
from datetime import datetime, timedelta
import os

class ExtendedAuthService:
    @staticmethod
    def register_user(username, email, password, role_name='user', user_type='user', **extra_data):
        """
        Enregistre un utilisateur avec un type spécifique
        
        Args:
            username (str): Nom d'utilisateur
            email (str): Email
            password (str): Mot de passe
            role_name (str): Nom du rôle
            user_type (str): Type d'utilisateur (user, administrateur, etc.)
            **extra_data: Données spécifiques au type d'utilisateur
        """
        # Vérifications de base
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already exists")
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already exists")
        
        # Trouver le rôle
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            raise ValueError(f"Role {role_name} does not exist")
        
        # Créer l'utilisateur du bon type avec la factory
        user_data = {
            'username': username,
            'email': email,
            'role_id': role.id,
            **extra_data
        }
        
        user = UserFactory.create_user(user_type, **user_data)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"[USER_CREATED] {user_type.capitalize()} {username} créé avec succès")
        return user

    @staticmethod
    def register_administrateur(username, email, password, niveau_acces='complet', ip_autorisees=None):
        """Crée un administrateur avec ses attributs spécifiques"""
        return ExtendedAuthService.register_user(
            username=username,
            email=email,
            password=password,
            role_name='admin',
            user_type='administrateur',
            niveau_acces=niveau_acces,
            ip_autorisees=ip_autorisees or '[]'
        )

    @staticmethod
    def register_responsable_rh(username, email, password, departement=None, certification_rh=None):
        """Crée un responsable RH avec ses attributs spécifiques"""
        return ExtendedAuthService.register_user(
            username=username,
            email=email,
            password=password,
            role_name='hr',
            user_type='responsable_rh',
            departement=departement,
            certification_rh=certification_rh
        )

    @staticmethod
    def register_magasinier(username, email, password, entrepot_assigne=None, niveau_autorisation='lecture'):
        """Crée un magasinier avec ses attributs spécifiques"""
        return ExtendedAuthService.register_user(
            username=username,
            email=email,
            password=password,
            role_name='warehouse',
            user_type='magasinier',
            entrepot_assigne=entrepot_assigne,
            niveau_autorisation=niveau_autorisation
        )

    @staticmethod
    def register_comptable(username, email, password, numero_ordre=None, specialite=None):
        """Crée un comptable avec ses attributs spécifiques"""
        return ExtendedAuthService.register_user(
            username=username,
            email=email,
            password=password,
            role_name='accountant',
            user_type='comptable',
            numero_ordre=numero_ordre,
            specialite=specialite
        )

    @staticmethod
    def login_user(username, password):
        """Login avec informations étendues selon le type d'utilisateur"""
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password) or not user.is_active:
            return None
        
        # Récupérer les permissions du rôle
        permissions = [p.code for p in user.role_ref.permissions] if user.role_ref else []
        
        # Informations spécifiques selon le type d'utilisateur
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role_ref.name if user.role_ref else 'user',
            'permissions': permissions,
            'user_type': user.user_type,
            'noms': user.noms,
            'prenoms': user.prenoms,
            'telephone': user.telephone
        }
        
        # Ajouter des informations spécifiques selon le type
        if isinstance(user, Administrateur):
            user_info.update({
                'niveau_acces': user.niveau_acces,
                'derniere_connexion_admin': user.derniere_connexion_admin.isoformat() if user.derniere_connexion_admin else None
            })
            # Mettre à jour la dernière connexion admin
            user.derniere_connexion_admin = datetime.utcnow()
            
        elif isinstance(user, ResponsableRH):
            user_info.update({
                'departement': user.departement,
                'certification_rh': user.certification_rh
            })
            
        elif isinstance(user, Magasinier):
            user_info.update({
                'entrepot_assigne': user.entrepot_assigne,
                'niveau_autorisation': user.niveau_autorisation
            })
            
        elif isinstance(user, Comptable):
            user_info.update({
                'numero_ordre': user.numero_ordre,
                'specialite': user.specialite
            })
        
        # Créer le token avec les claims étendus
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'role': user.role_ref.name if user.role_ref else 'user',
                'permissions': permissions,
                'email': user.email,
                'username': user.username,
                'user_type': user.user_type
            },
            expires_delta=timedelta(hours=24)
        )
        
        # Commit des changements (comme dernière connexion)
        db.session.commit()
        
        return {
            'access_token': access_token,
            'user_info': user_info
        }

    @staticmethod
    def get_user_by_id(user_id):
        """Récupère un utilisateur avec son type correct"""
        return User.query.get(user_id)

    @staticmethod
    def get_users_by_type(user_type):
        """Récupère tous les utilisateurs d'un type donné"""
        return User.query.filter_by(user_type=user_type).all()

    @staticmethod
    def promote_user_to_type(user_id, new_user_type, **type_specific_data):
        """
        Promeut un utilisateur vers un nouveau type
        
        Args:
            user_id (int): ID de l'utilisateur
            new_user_type (str): Nouveau type d'utilisateur
            **type_specific_data: Données spécifiques au nouveau type
        """
        # Récupérer l'utilisateur existant
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Vérifier si c'est un changement de type valide
        if user.user_type == new_user_type:
            return user  # Pas de changement nécessaire
        
        # Sauvegarder les données de base
        base_data = {
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash,
            'role_id': user.role_id,
            'created_at': user.created_at,
            'is_active': user.is_active,
            'noms': user.noms,
            'prenoms': user.prenoms,
            'telephone': user.telephone
        }
        
        # Supprimer l'ancien utilisateur
        db.session.delete(user)
        db.session.flush()  # Flush pour libérer l'ID
        
        # Créer le nouveau utilisateur avec le bon type
        new_user_data = {**base_data, **type_specific_data}
        new_user = UserFactory.create_user(new_user_type, **new_user_data)
        new_user.id = user_id  # Conserver le même ID
        
        db.session.add(new_user)
        db.session.commit()
        
        print(f"[USER_PROMOTED] User {user.username} promoted from {user.user_type} to {new_user_type}")
        return new_user

    @staticmethod
    def init_extended_roles_and_permissions():
        """Initialise les rôles étendus pour les différents types d'utilisateurs"""
        print("\n=== Initialisation du système étendu ===")
        
        # Permissions étendues
        extended_permissions = [
            ('manage_users', 'Gérer les utilisateurs'),
            ('view_reports', 'Voir les rapports'),
            ('manage_payroll', 'Gérer la paie'),
            ('manage_inventory', 'Gérer l\'inventaire'),
            ('manage_hr', 'Gestion RH avancée'),
            ('manage_accounting', 'Gestion comptable avancée'),
            ('warehouse_operations', 'Opérations d\'entrepôt'),
            ('super_admin', 'Accès complet au système'),
        ]

        # Créer les permissions
        for code, name in extended_permissions:
            if not Permission.query.filter_by(code=code).first():
                db.session.add(Permission(code=code, name=name))
                print(f"[+] Permission créée: {code}")

        # Rôles étendus
        extended_roles = [
            ('super_admin', 'Super Administrateur', ['super_admin'] + [p[0] for p in extended_permissions]),
            ('admin', 'Administrateur', ['manage_users', 'view_reports', 'manage_payroll']),
            ('hr', 'Ressources Humaines', ['manage_users', 'view_reports', 'manage_hr']),
            ('accountant', 'Comptable', ['manage_payroll', 'manage_accounting', 'view_reports']),
            ('warehouse', 'Magasinier', ['manage_inventory', 'warehouse_operations', 'view_reports']),
            ('user', 'Utilisateur standard', []),
        ]

        # Créer les rôles
        for name, desc, perm_codes in extended_roles:
            if not Role.query.filter_by(name=name).first():
                role = Role(name=name, description=desc)
                if perm_codes:
                    role.permissions = Permission.query.filter(Permission.code.in_(perm_codes)).all()
                db.session.add(role)
                print(f"[+] Rôle créé: {name}")

        db.session.commit()

        # Créer des utilisateurs de test pour chaque type
        test_users = [
            ('super_admin', 'superadmin', 'admin@erp.com', 'admin123', 'administrateur'),
            ('hr', 'rh_manager', 'rh@erp.com', 'rh123', 'responsable_rh'),
            ('warehouse', 'warehouse_user', 'magasin@erp.com', 'mag123', 'magasinier'),
            ('accountant', 'comptable_user', 'compta@erp.com', 'compta123', 'comptable')
        ]
        
        for role_name, username, email, password, user_type in test_users:
            if not User.query.filter_by(username=username).first():
                try:
                    if user_type == 'administrateur':
                        user = ExtendedAuthService.register_administrateur(username, email, password)
                    elif user_type == 'responsable_rh':
                        user = ExtendedAuthService.register_responsable_rh(
                            username, email, password, 
                            departement="Direction RH"
                        )
                    elif user_type == 'magasinier':
                        user = ExtendedAuthService.register_magasinier(
                            username, email, password,
                            entrepot_assigne="Entrepôt Principal",
                            niveau_autorisation="ecriture"
                        )
                    elif user_type == 'comptable':
                        user = ExtendedAuthService.register_comptable(
                            username, email, password,
                            specialite="Comptabilité générale"
                        )
                    
                    print(f"[+] Utilisateur test créé: {username} ({user_type})")
                except Exception as e:
                    print(f"[!] Erreur création {username}: {str(e)}")
        
        print("=== Initialisation étendue terminée ===\n")

    # Méthodes héritées de l'ancien service
    @staticmethod
    def logout_user(raw_token):
        """Hérite de la fonctionnalité de logout"""
        try:
            decoded_token = decode_token(raw_token)
            
            jti = decoded_token['jti']
            user_id = int(decoded_token['sub'])
            expires_at = datetime.fromtimestamp(decoded_token['exp'])
            
            existing_blacklist = TokenBlacklist.query.filter_by(jti=jti).first()
            if existing_blacklist:
                return False, "Token already revoked"
            
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            blacklisted_token = TokenBlacklist(
                jti=jti,
                user_id=user_id,
                expires_at=expires_at
            )
            
            db.session.add(blacklisted_token)
            db.session.commit()
            
            print(f"[LOGOUT] Token {jti[:8]}... révoqué pour {user.username} ({user.user_type})")
            
            return True, f"Successfully logged out {user.user_type} {user.username}"
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Erreur lors du logout: {str(e)}")
            return False, f"Error during logout: {str(e)}"

    @staticmethod
    def is_token_revoked(jti):
        """Vérifie si un token est révoqué"""
        return TokenBlacklist.query.filter_by(jti=jti).first() is not None

    @staticmethod
    def cleanup_expired_tokens():
        """Nettoie les tokens expirés"""
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
                print(f"[CLEANUP] {count} tokens expirés supprimés")
            
            return count
            
        except Exception as e:
            print(f"[ERROR] Erreur cleanup: {str(e)}")
            db.session.rollback()
            return 0