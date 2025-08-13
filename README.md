# ERP Flask Backend

Un système ERP (Enterprise Resource Planning) moderne développé avec Flask, offrant une architecture modulaire et évolutive.

##  Architecture

Le projet suit une architecture modulaire avec les composants suivants :

```
erp_backend/
├── app.py                 # Point d'entrée de l'application
├── config.py             # Configuration de l'application
├── requirements.txt      # Dépendances Python
├
│── core/           # Composants centraux
│   	├── database.py  # Configuration de la base de données
│   	├── extensions.py # Extensions Flask
│       └── utils.py     # Utilitaires communs
|── modules/         # Modules métier
│       ├── auth/        # Authentification et gestion des utilisateurs
│       ├── rh/          # Ressources Humaines
│       ├── paie/        # Paie et comptabilité
│       ├── stock/       # Gestion des stocks
│       └── ventes/      # Gestion des ventes
```

##  Installation

### Prérequis

- Python 3.8+
- PostgreSQL
- pip

### Étapes d'installation

1. **Cloner le projet**
   ```bash
   git clone <repository-url>
   cd erp-project
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer la base de données PostgreSQL**
   ```bash
   # Créer une base de données PostgreSQL
   createdb erp_db
   ```

5. **Configurer les variables d'environnement**
   Créer un fichier `.env` à la racine du projet :
   ```env
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=erp_db
   DB_USER=postgres
   DB_PASSWORD=your-password
   ```


6. **Lancer l'application**
   ```bash
   flask run
   ```

L'API sera accessible sur `http://localhost:5000`

##  Modules disponibles

###  Module d'authentification (`/api/auth`)

**Routes principales :**
- `POST /api/auth/register` - Inscription d'un nouvel utilisateur
- `POST /api/auth/login` - Connexion utilisateur
- `POST /api/auth/logout` - Déconnexion utilisateur
- `GET /api/auth/profile` - Profil utilisateur
- `PUT /api/auth/profile` - Mise à jour du profil
- `POST /api/auth/change-password` - Changement de mot de passe

**Routes d'administration :**
- `GET /api/auth/users` - Liste des utilisateurs
- `PUT /api/auth/users/<id>` - Mise à jour d'un utilisateur
- `POST /api/auth/users/<id>/activate` - Activer un utilisateur
- `POST /api/auth/users/<id>/deactivate` - Désactiver un utilisateur

###  Module RH (Ressources Humaines)

**Fonctionnalités :**
- Gestion des employés
- Gestion des départements
- Gestion des congés
- Suivi des présences
- Gestion des contrats

###  Module Paie

**Fonctionnalités :**
- Calcul des salaires
- Gestion des primes
- Gestion des charges sociales
- Génération des bulletins de paie

###  Module Stock

**Fonctionnalités :**
- Gestion des produits
- Gestion des fournisseurs
- Suivi des stocks
- Gestion des commandes
- Alertes de stock

###  Module Ventes

**Fonctionnalités :**
- Gestion des clients
- Gestion des devis
- Gestion des commandes
- Suivi des ventes
- Rapports de vente

##  Configuration

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `FLASK_ENV` | Environnement Flask | `development` |
| `SECRET_KEY` | Clé secrète Flask | `dev-secret-key` |
| `DB_HOST` | Hôte PostgreSQL | `localhost` |
| `DB_PORT` | Port PostgreSQL | `5432` |
| `DB_NAME` | Nom de la base de données | `erp_db` |
| `DB_USER` | Utilisateur PostgreSQL | `postgres` |
| `DB_PASSWORD` | Mot de passe PostgreSQL | `password` |
| `CORS_ORIGINS` | Origines CORS autorisées | `http://localhost:3000` |

### Environnements

- **Development** : Mode développement avec debug activé
- **Production** : Mode production optimisé
- **Testing** : Mode test avec base de données de test

##  Sécurité

- **Authentification Flask-Login** : Sessions sécurisées avec cookies
- **Hachage des mots de passe** : Bcrypt avec 12 rounds
- **Validation des données** : Marshmallow schemas
- **CORS** : Configuration des origines autorisées
- **Gestion des erreurs** : Réponses d'erreur standardisées
- **Protection des sessions** : Configuration forte des cookies

##  Exemples d'utilisation

### Créer un utilisateur
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "password123",
    "confirm_password": "password123",
  }'
```

### Se connecter
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "john_doe",
    "password": "password123",
  }'
```

### Accéder à une route protégée
```bash
curl -X GET http://localhost:5000/api/auth/profile \
  -b cookies.txt
```

### Se déconnecter
```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -b cookies.txt
```

##  Tests

```bash
# Lancer les tests
python -m pytest

# Avec couverture
python -m pytest --cov=backend
```

##  Base de données

### Modèles principaux

- **User** : Utilisateurs du système (avec Flask-Login UserMixin)
- **UserSession** : Sessions utilisateur pour réinitialisation de mot de passe
- **Department** : Départements de l'entreprise
- **Employee** : Employés
- **Leave** : Congés
- **Attendance** : Présences

### Migrations

```bash
# Créer une nouvelle migration
flask db migrate -m "Description de la migration"

# Appliquer les migrations
flask db upgrade

# Annuler la dernière migration
flask db downgrade
```

##  Déploiement

### Production avec Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (à venir)

```bash
docker build -t erp-flask .
docker run -p 5000:5000 erp-flask
```

##  Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

##  Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
## CECI EST UNE PREMIERE BASE POUR LE BACK 

## 📞 Support

Pour toute question ou problème, veuillez ouvrir une issue sur GitHub.
