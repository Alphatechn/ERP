
from flask import Blueprint
from flask_restful import Api
from .resources import (
    RegisterResource, LoginResource, LogoutResource, ProfileResource,
    UsersByTypeResource, UserPromoteResource, UserTypesResource,
    TestTokenResource, HealthResource, AdminUsersResource,
    HREmployeesResource, WarehouseInventoryResource,
    AccountingReportsResource, InitSystemResource
)

# Créer le blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# la documentation du blueprint
auth_bp.__doc__ = """
Blueprint pour l'authentification étendue

Ce module gère :
- L'authentification JWT avec types d'utilisateurs
- La gestion des permissions par rôles
- Les opérations spécifiques par type (admin, RH, magasinier, comptable)
- La documentation Swagger complète
"""


api = Api(auth_bp)

# === ROUTES BASIQUES ===
api.add_resource(RegisterResource, '/register')
api.add_resource(LoginResource, '/login')
api.add_resource(LogoutResource, '/logout')
api.add_resource(ProfileResource, '/profile')

# === ROUTES DE GESTION DES UTILISATEURS (Admin) ===
api.add_resource(UsersByTypeResource, '/users/by-type')
api.add_resource(UserPromoteResource, '/users/promote')
api.add_resource(UserTypesResource, '/user-types')

# === ROUTES DE TEST ET HEALTH ===
api.add_resource(HealthResource, '/health')
api.add_resource(TestTokenResource, '/test-token')

# === ROUTES MÉTIER SPÉCIFIQUES PAR TYPE ===
api.add_resource(AdminUsersResource, '/admin/users')
api.add_resource(HREmployeesResource, '/hr/employees')
api.add_resource(WarehouseInventoryResource, '/warehouse/inventory')
api.add_resource(AccountingReportsResource, '/accounting/reports')

# === ROUTE D'INITIALISATION ===
api.add_resource(InitSystemResource, '/init-system')