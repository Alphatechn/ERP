from flask import Flask, jsonify
from config import Config
from core.database import db
from core.extensions import jwt, cors, setup_jwt_callbacks
from modules.auth.routes import auth_bp
from modules.rh.routes import personnel_bp
from modules.auth.services import ExtendedAuthService
from core.swagger_config import init_swagger

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    print("Configuration de l'application...")
    
    # Initialiser Swagger
    swagger = init_swagger(app)
    print("Swagger initialisé - Documentation disponible sur /docs/")


    # Initialiser les extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    
    # Configurer les callbacks JWT
    setup_jwt_callbacks(jwt)
    print("Extensions initialisées")
    
    # Route de test
    @app.route('/')
    def index():
        return jsonify({
            'message': 'ERP Backend API is running!',
            'version': '2.0.0',
            'framework': 'Flask-RESTful + Flasgger',
            'documentation': {
                'swagger_ui': '/docs/',
                'api_spec': '/apispec.json'
            },
            'endpoints': {
                'auth': '/api/auth/',
                'health': '/api/auth/health',
                'admin': '/api/auth/admin/',
                'hr': '/api/auth/hr/',
                'warehouse': '/api/auth/warehouse/',
                'accounting': '/api/auth/accounting/'
            },
            'features': [
                'JWT Authentication with extended user types',
                'Role-based permissions',
                'Swagger/OpenAPI documentation',
                'Multi-user type support (admin, hr, warehouse, accounting)'
            ]
        })

    # Route spécifique pour rediriger vers la documentation
    @app.route('/documentation')
    def documentation():
        return jsonify({
            'message': 'API Documentation available',
            'swagger_ui': '/docs/',
            'api_spec': '/apispec.json',
            'instructions': 'Visit /docs/ for interactive API documentation'
        })


    
    # Enregistrer les blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(personnel_bp)
    print("Blueprints enregistrés")
    
    # Initialiser la base de données
    with app.app_context():
        try:
            print("Création des tables...")
            db.create_all()
            print("Tables créées avec succès")
            
            # Initialiser les rôles et permissions par défaut
            ExtendedAuthService.init_extended_roles_and_permissions()
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la DB: {e}")
    
    print("Application créée avec succès!")
    return app

# Créer l'application
app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Démarrage du serveur ERP Flask...")
    print("📚 Documentation Swagger: http://localhost:5000/docs/")
    print("🏠 Page d'accueil: http://localhost:5000/")
    print("🔐 Authentification: http://localhost:5000/api/auth/")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
