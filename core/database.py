from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Initialiser les rôles et permissions par défaut
        from ..modules.auth.services import AuthService
        AuthService.init_default_roles_and_permissions()