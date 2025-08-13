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