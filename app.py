from flask import Flask 
from backend.cores.database import init_db, db
from backend.cores.extensions import init_extensions, login_manager
from config import config
import os

def create_app(config_name=None):
    """Factory pattern pour créer l'application Flask"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialiser la base de données
    init_db(app)
    
    # Initialiser les extensions
    init_extensions(app)
    
    # User loader pour Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from backend.modules.auth.models import User
        return User.query.get(int(user_id))
    
    # Créer les tables si elles n'existent pas
    with app.app_context():
        db.create_all()
    
    # Importer et enregistrer les modules
    from backend.modules.auth.routes import auth_bp
    app.register_blueprint(auth_bp)
    
    # TODO: Enregistrer les autres modules quand ils seront créés
    # from backend.modules.rh.routes import rh_bp
    # app.register_blueprint(rh_bp)
    
    # from backend.modules.paie.routes import paie_bp
    # app.register_blueprint(paie_bp)
    
    # from backend.modules.stock.routes import stock_bp
    # app.register_blueprint(stock_bp)
    
    # from backend.modules.ventes.routes import ventes_bp
    # app.register_blueprint(ventes_bp)
    
    # Route de test
    @app.route('/')
    def index():
        return {
            'message': 'ERP Flask API',
            'version': '1.0.0',
            'status': 'running'
        }
    
    # Gestionnaire d'erreurs global
    @app.errorhandler(404)
    def not_found(error):
        return {'error': True, 'message': 'Route non trouvée'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': True, 'message': 'Erreur interne du serveur'}, 500
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
