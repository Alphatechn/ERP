from flask_login import LoginManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate

# Initialisation des extensions
login_manager = LoginManager()
cors = CORS()
bcrypt = Bcrypt()
ma = Marshmallow()
migrate = Migrate()

def init_extensions(app):
    """Initialise toutes les extensions Flask"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    cors.init_app(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']))
    bcrypt.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, app.db)
