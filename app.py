from flask import Flask, jsonify
from config import Config
from core.database import db
from core.extensions import jwt, cors
from modules.auth.routes import auth_bp
from modules.auth.services import AuthService

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    print("Configuration de l'application...")
    
    # Initialiser les extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    def setup_jwt_callbacks(app, jwt):
        """Configuration complète des callbacks JWT"""
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Vérifie si un token est dans la blacklist"""
        try:
            jti = jwt_payload.get('jti')
            if not jti:
                return False
            
            # Importer ici pour éviter les imports circulaires
            from modules.auth.services import AuthService
            is_revoked = AuthService.is_token_revoked(jti)
            
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
        
        return jsonify({
            'error': 'Token has been revoked',
            'message': 'Please login again to get a new token'
        }), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Appelé quand un token expiré est utilisé"""
        return jsonify({
            'error': 'Token has expired',
            'message': 'Please login again to get a new token'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        """Appelé quand le token est malformé"""
        print(f"🚫 Token invalide: {error_string}")
        return jsonify({
            'error': 'Invalid token format',
            'message': 'Please provide a valid token'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        """Appelé quand aucun token n'est fourni"""
        return jsonify({
            'error': 'Authorization token required',
            'message': 'Please provide a valid token in Authorization header'
        }), 401

    
    print("Extensions initialisées")
    
    # Route de test
    @app.route('/')
    def index():
        return jsonify({
            'message': 'ERP Backend API is running!',
            'version': '1.0.0',
            'endpoints': ['/api/auth/register', '/api/auth/login']
        })
    
    # Enregistrer les blueprints
    app.register_blueprint(auth_bp)
    print("Blueprints enregistrés")
    
    # Initialiser la base de données
    with app.app_context():
        try:
            print("Création des tables...")
            db.create_all()
            print("Tables créées avec succès")
            
            # Initialiser les rôles et permissions par défaut
            AuthService.init_default_roles_and_permissions()
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la DB: {e}")
    
    print("Application créée avec succès!")
    return app

# Créer l'application
app = create_app()

if __name__ == '__main__':
    print("Démarrage du serveur Flask...")
    app.run(debug=True, host='0.0.0.0', port=5000)