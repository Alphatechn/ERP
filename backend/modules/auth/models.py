from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from backend.cores.database import db
from backend.cores.extensions import bcrypt

class User(db.Model, UserMixin):
    """Modèle utilisateur pour l'authentification"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='user')  # admin, manager, user
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    # Les relations avec d'autres modules seront ajoutées ici
    
    def __init__(self, username, email, password, first_name, last_name, **kwargs):
        self.username = username
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.first_name = first_name
        self.last_name = last_name
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Définit un nouveau mot de passe"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def get_id(self):
        """Retourne l'ID de l'utilisateur (requis par Flask-Login)"""
        return str(self.id)
    
    def is_authenticated(self):
        """Vérifie si l'utilisateur est authentifié"""
        return True
    
    def is_anonymous(self):
        """Vérifie si l'utilisateur est anonyme"""
        return False
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class UserSession(db.Model):
    """Modèle pour gérer les sessions utilisateur"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='sessions')
    
    def is_expired(self):
        """Vérifie si la session a expiré"""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'expires_at': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat()
        }
