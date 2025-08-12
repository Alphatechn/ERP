from flask_migrate import Migrate, upgrade, init, migrate
from app import create_app, db

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # Initialiser les migrations si ce n'est pas déjà fait
        try:
            init()
        except:
            pass
        
        # Créer une migration
        migrate()
        
        # Appliquer les migrations
        upgrade() 