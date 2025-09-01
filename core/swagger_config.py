# config/swagger_config.py
from flasgger import Swagger

# Configuration Swagger/OpenAPI
SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"  # URL pour accéder à Swagger UI
}

# Template de documentation Swagger
SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "ERP System API",
        "description": "API complète pour le système ERP avec gestion d'authentification étendue",
        "version": "2.0.0",
        "contact": {
            "name": "Support API",
            "email": "support@erp.com"
        }
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http", "https"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
        }
    },
    "security": [{"Bearer": []}],
    "tags": [
        {
            "name": "Authentication",
            "description": "Endpoints pour l'authentification et la gestion des utilisateurs"
        },
        {
            "name": "Administration", 
            "description": "Endpoints réservés aux administrateurs"
        },
        {
            "name": "RH",
            "description": "Endpoints pour les responsables RH"
        },
        {
            "name": "Magasin",
            "description": "Endpoints pour les magasiniers"
        },
        {
            "name": "Comptabilité",
            "description": "Endpoints pour les comptables"
        },
        {
            "name": "Système",
            "description": "Endpoints système et health checks"
        }
    ]
}

def init_swagger(app):
    """Initialise Swagger avec la configuration personnalisée"""
    swagger = Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)
    return swagger