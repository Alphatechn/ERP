# File: core/extensions.py (Updated)
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

# Initialisation des extensions
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
api = Api()

def setup_jwt_callbacks(jwt):
    """Configuration complète des callbacks JWT"""
    from flask import jsonify
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Vérifie si un token est dans la blacklist"""
        try:
            jti = jwt_payload.get('jti')
            if not jti:
                return False
            
            # Importer ici pour éviter les imports circulaires
            from modules.auth.services import ExtendedAuthService
            is_revoked = ExtendedAuthService.is_token_revoked(jti)
            if is_revoked:
                print(f"🚫 Token {jti[:8]}... est révoqué")
            return is_revoked
        except Exception as e:
            print(f"❌ Erreur check_revoked: {str(e)}")
            return False  # En cas d'erreur, ne pas bloquer

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Appelé quand un token révoqué est utilisé"""
        jti = jwt_payload.get('jti', 'unknown')
        print(f"🚫 Tentative d'usage d'un token révoqué: {jti[:8]}...")
        return {
            'error': 'Token has been revoked',
            'message': 'Please login again to get a new token'
        }, 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Appelé quand un token expiré est utilisé"""
        return {
            'error': 'Token has expired',
            'message': 'Please login again to get a new token'
        }, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        """Appelé quand le token est malformé"""
        print(f"🚫 Token invalide: {error_string}")
        return {
            'error': 'Invalid token format',
            'message': 'Please provide a valid token'
        }, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        """Appelé quand aucun token n'est fourni"""
        return {
            'error': 'Authorization token required',
            'message': 'Please provide a valid token in Authorization header'
        }, 401