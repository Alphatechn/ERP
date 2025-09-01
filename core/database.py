# File: core/database.py (Updated)
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialise la base de données"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Initialiser les rôles et permissions par défaut
        try:
            from modules.auth.services import ExtendedAuthService
            ExtendedAuthService.init_extended_roles_and_permissions()
            print("Système d'authentification initialisé")
        except Exception as e:
            print(f"Erreur initialisation auth: {e}")