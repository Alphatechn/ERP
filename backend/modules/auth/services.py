from datetime import datetime, timedelta
import secrets
from typing import Optional, Dict, Any
from flask import current_app
from flask_login import login_user, logout_user, current_user
from backend.cores.database import db
from backend.modules.auth.models import User, UserSession
from backend.cores.utils import validate_email, validate_phone

class AuthService:
    """Service pour la gestion de l'authentification"""
    
    @staticmethod
    def register_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enregistre un nouvel utilisateur"""
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(username=user_data['username']).first():
            raise ValueError("Ce nom d'utilisateur existe déjà")
        
        if User.query.filter_by(email=user_data['email']).first():
            raise ValueError("Cet email existe déjà")
        
        # Créer l'utilisateur
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            phone=user_data.get('phone'),
            role=user_data.get('role', 'user')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return {
            'message': 'Utilisateur créé avec succès',
            'user': user.to_dict()
        }
    
    @staticmethod
    def authenticate_user(username: str, password: str, remember: bool = False) -> Optional[Dict[str, Any]]:
        """Authentifie un utilisateur"""
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return None
        
        if not user.is_active:
            raise ValueError("Compte désactivé")
        
        # Mettre à jour la dernière connexion
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Connecter l'utilisateur avec Flask-Login
        login_user(user, remember=remember)
        
        return {
            'message': 'Connexion réussie',
            'user': user.to_dict()
        }
    
    @staticmethod
    def logout_user() -> Dict[str, Any]:
        """Déconnecte l'utilisateur actuel"""
        if current_user.is_authenticated:
            logout_user()
            return {'message': 'Déconnexion réussie'}
        return {'message': 'Aucun utilisateur connecté'}
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Récupère un utilisateur par son nom d'utilisateur"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Récupère un utilisateur par son email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def update_user(user_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un utilisateur"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        # Mettre à jour les champs autorisés
        allowed_fields = ['first_name', 'last_name', 'phone', 'role']
        for field in allowed_fields:
            if field in update_data:
                setattr(user, field, update_data[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {
            'message': 'Utilisateur mis à jour avec succès',
            'user': user.to_dict()
        }
    
    @staticmethod
    def change_password(user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change le mot de passe d'un utilisateur"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        if not user.check_password(current_password):
            raise ValueError("Mot de passe actuel incorrect")
        
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {'message': 'Mot de passe changé avec succès'}
    
    @staticmethod
    def deactivate_user(user_id: int) -> Dict[str, Any]:
        """Désactive un utilisateur"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {'message': 'Utilisateur désactivé avec succès'}
    
    @staticmethod
    def activate_user(user_id: int) -> Dict[str, Any]:
        """Active un utilisateur"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {'message': 'Utilisateur activé avec succès'}
    
    @staticmethod
    def get_all_users(page: int = 1, per_page: int = 20, search: str = None) -> Dict[str, Any]:
        """Récupère tous les utilisateurs avec pagination"""
        query = User.query
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'users': [user.to_dict() for user in pagination.items],
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
    
    @staticmethod
    def create_password_reset_session(email: str) -> Dict[str, Any]:
        """Crée une session de réinitialisation de mot de passe"""
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("Aucun utilisateur trouvé avec cet email")
        
        # Générer un ID de session unique
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Créer une session de réinitialisation
        reset_session = UserSession(
            user_id=user.id,
            session_id=session_id,
            expires_at=expires_at
        )
        
        db.session.add(reset_session)
        db.session.commit()
        
        return {
            'message': 'Session de réinitialisation créée',
            'session_id': session_id,
            'expires_at': expires_at.isoformat()
        }
    
    @staticmethod
    def reset_password_with_session(session_id: str, new_password: str) -> Dict[str, Any]:
        """Réinitialise le mot de passe avec une session"""
        session = UserSession.query.filter_by(session_id=session_id).first()
        if not session:
            raise ValueError("Session invalide")
        
        if session.is_expired():
            db.session.delete(session)
            db.session.commit()
            raise ValueError("Session expirée")
        
        user = session.user
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        
        # Supprimer la session
        db.session.delete(session)
        db.session.commit()
        
        return {'message': 'Mot de passe réinitialisé avec succès'}
