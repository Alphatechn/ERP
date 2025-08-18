from flask import Blueprint, jsonify
from .controllers import ExtendedAuthController
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from datetime import datetime

extended_auth_bp = Blueprint('extended_auth', __name__, url_prefix='/api/auth')

# === ROUTES BASIQUES ===
@extended_auth_bp.route('/register', methods=['POST'])
def register():
    """
    Enregistrement étendu supportant différents types d'utilisateurs
    
    Body JSON:
    {
        "username": "string",
        "email": "string", 
        "password": "string",
        "user_type": "user|administrateur|responsable_rh|magasinier|comptable",
        // Champs spécifiques selon le type:
        // Administrateur:
        "niveau_acces": "complet|partiel",
        "ip_autorisees": "string",
        // ResponsableRH:
        "departement": "string",
        "certification_rh": "string",
        // Magasinier:
        "entrepot_assigne": "string",
        "niveau_autorisation": "lecture|ecriture|supervision",
        // Comptable:
        "numero_ordre": "string",
        "specialite": "string"
    }
    """
    return ExtendedAuthController.register()

@extended_auth_bp.route('/login', methods=['POST'])
def login():
    """
    Connexion avec retour d'informations étendues selon le type d'utilisateur
    
    Body JSON:
    {
        "username": "string",
        "password": "string"
    }
    """
    return ExtendedAuthController.login()

@extended_auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Déconnexion avec support des types étendus
    Headers: Authorization: Bearer <token>
    """
    return ExtendedAuthController.logout()

@extended_auth_bp.route('/profile', methods=['GET'])
def profile():
    """
    Profil utilisateur avec informations spécifiques au type
    Headers: Authorization: Bearer <token>
    """
    return ExtendedAuthController.profile()

@extended_auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """
    Mise à jour du profil avec champs spécifiques au type
    Headers: Authorization: Bearer <token>
    
    Body JSON: Champs à mettre à jour selon le type d'utilisateur
    """
    return ExtendedAuthController.update_profile()

# === ROUTES DE GESTION DES UTILISATEURS (Admin) ===
@extended_auth_bp.route('/users/by-type', methods=['GET'])
def get_users_by_type():
    """
    Récupère les utilisateurs par type (Admin only)
    Headers: Authorization: Bearer <token>
    Query Params: type=user|administrateur|responsable_rh|magasinier|comptable
    
    Nécessite: permission 'manage_users'
    """
    return ExtendedAuthController.get_users_by_type()

@extended_auth_bp.route('/users/promote', methods=['POST'])
def promote_user():
    """
    Promeut un utilisateur vers un nouveau type (Admin only)
    Headers: Authorization: Bearer <token>
    
    Body JSON:
    {
        "user_id": int,
        "new_user_type": "string",
        "type_specific_data": {
            // Données spécifiques au nouveau type
        }
    }
    
    Nécessite: permission 'manage_users'
    """
    return ExtendedAuthController.promote_user()

@extended_auth_bp.route('/user-types', methods=['GET'])
def get_user_types():
    """
    Retourne la liste des types d'utilisateurs disponibles avec descriptions
    """
    return ExtendedAuthController.get_user_types()

# === ROUTES DE SESSION (héritées) ===
@extended_auth_bp.route('/sessions', methods=['GET'])
def my_sessions():
    """
    Informations sur les sessions de l'utilisateur connecté
    Headers: Authorization: Bearer <token>
    """
    return ExtendedAuthController.my_sessions()

# === ROUTES DE TEST ET HEALTH ===
@extended_auth_bp.route('/health', methods=['GET'])
def health():
    """Check de santé du module d'authentification étendu"""
    return {
        'status': 'Extended Auth module running',
        'timestamp': datetime.utcnow().isoformat(),
        'supported_user_types': ['user', 'administrateur', 'responsable_rh', 'magasinier', 'comptable']
    }, 200

@extended_auth_bp.route('/test-token', methods=['GET'])
def test_token():
    """
    Test de validation de token avec informations étendues
    Headers: Authorization: Bearer <token>
    """
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        user_id = get_jwt_identity()
        
        return jsonify({
            'message': 'Token is valid! 🎉',
            'user_id': user_id,
            'username': claims.get('username'),
            'user_type': claims.get('user_type', 'user'),
            'role': claims.get('role'),
            'permissions': claims.get('permissions', []),
            'jti': claims.get('jti', '')[:8] + '...'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Token error: {str(e)}'}), 401

# === ROUTES MÉTIER SPÉCIFIQUES PAR TYPE ===

@extended_auth_bp.route('/admin/users', methods=['GET'])
def admin_get_all_users():
    """
    [ADMINISTRATEUR] Récupère tous les utilisateurs avec détails
    Headers: Authorization: Bearer <token>
    
    Nécessite: user_type='administrateur' ET permission 'manage_users'
    """
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        
        # Vérification du type et des permissions
        if claims.get('user_type') != 'administrateur':
            return jsonify({'error': 'Access restricted to administrators'}), 403
            
        if 'manage_users' not in claims.get('permissions', []):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        from .models import User
        users = User.query.all()
        
        users_data = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'role': user.role_ref.name if user.role_ref else 'user',
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat(),
                'last_login': None  # À implémenter si besoin
            }
            users_data.append(user_data)
        
        return jsonify({
            'message': 'All users retrieved by administrator',
            'total_users': len(users_data),
            'users': users_data,
            'retrieved_by': claims.get('username')
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Admin operation failed: {str(e)}'}), 500

@extended_auth_bp.route('/hr/employees', methods=['GET'])
def hr_get_employees():
    """
    [RESPONSABLE RH] Récupère les informations des employés
    Headers: Authorization: Bearer <token>
    
    Nécessite: user_type='responsable_rh' ET permission 'manage_hr'
    """
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        
        if claims.get('user_type') != 'responsable_rh':
            return jsonify({'error': 'Access restricted to HR managers'}), 403
            
        if 'manage_hr' not in claims.get('permissions', []):
            return jsonify({'error': 'Insufficient HR permissions'}), 403
        
        # Logique RH - récupérer les employés (non-admin)
        from .models import User
        employees = User.query.filter(User.user_type.in_(['user', 'magasinier', 'comptable'])).all()
        
        employees_data = []
        for emp in employees:
            emp_data = {
                'id': emp.id,
                'username': emp.username,
                'noms': emp.noms,
                'prenoms': emp.prenoms,
                'email': emp.email,
                'telephone': emp.telephone,
                'user_type': emp.user_type,
                'role': emp.role_ref.name if emp.role_ref else 'user',
                'is_active': emp.is_active,
                'created_at': emp.created_at.isoformat()
            }
            employees_data.append(emp_data)
        
        return jsonify({
            'message': 'Employees data retrieved by HR',
            'total_employees': len(employees_data),
            'employees': employees_data,
            'hr_manager': claims.get('username')
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'HR operation failed: {str(e)}'}), 500

@extended_auth_bp.route('/warehouse/inventory', methods=['GET'])
def warehouse_get_inventory():
    """
    [MAGASINIER] Récupère l'état de l'inventaire
    Headers: Authorization: Bearer <token>
    
    Nécessite: user_type='magasinier' ET permission 'warehouse_operations'
    """
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        
        if claims.get('user_type') != 'magasinier':
            return jsonify({'error': 'Access restricted to warehouse staff'}), 403
            
        if 'warehouse_operations' not in claims.get('permissions', []):
            return jsonify({'error': 'Insufficient warehouse permissions'}), 403
        
        # Simulation d'inventaire (à remplacer par vraie logique)
        user_id = int(get_jwt_identity())
        from .models import Magasinier
        magasinier = Magasinier.query.get(user_id)
        
        inventory_data = {
            'entrepot': magasinier.entrepot_assigne if magasinier else 'Non assigné',
            'niveau_autorisation': magasinier.niveau_autorisation if magasinier else 'lecture',
            'total_produits': 150,  # Simulation
            'alertes_stock_bas': 12,
            'mouvements_aujourd_hui': 28,
            'derniere_maj': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'message': 'Inventory data retrieved',
            'inventory': inventory_data,
            'magasinier': claims.get('username')
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Warehouse operation failed: {str(e)}'}), 500

@extended_auth_bp.route('/accounting/reports', methods=['GET'])
def accounting_get_reports():
    """
    [COMPTABLE] Récupère les rapports comptables
    Headers: Authorization: Bearer <token>
    
    Nécessite: user_type='comptable' ET permission 'manage_accounting'
    """
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        
        if claims.get('user_type') != 'comptable':
            return jsonify({'error': 'Access restricted to accountants'}), 403
            
        if 'manage_accounting' not in claims.get('permissions', []):
            return jsonify({'error': 'Insufficient accounting permissions'}), 403
        
        # Simulation de données comptables
        user_id = int(get_jwt_identity())
        from .models import Comptable
        comptable = Comptable.query.get(user_id)
        
        reports_data = {
            'specialite': comptable.specialite if comptable else 'Générale',
            'numero_ordre': comptable.numero_ordre if comptable else 'N/A',
            'rapports_disponibles': [
                'Bilan mensuel',
                'Compte de résultat',
                'Journal des ventes',
                'Rapprochement bancaire'
            ],
            'derniers_traitements': 45,
            'en_attente_validation': 8,
            'derniere_cloture': '2024-07-31'
        }
        
        return jsonify({
            'message': 'Accounting reports retrieved',
            'reports': reports_data,
            'comptable': claims.get('username')
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Accounting operation failed: {str(e)}'}), 500

# === ROUTE D'INITIALISATION ===
@extended_auth_bp.route('/init-system', methods=['POST'])
def init_extended_system():
    """
    Initialise le système étendu avec rôles, permissions et utilisateurs de test
    ⚠️  À utiliser uniquement en développement
    """
    try:
        from .services import ExtendedAuthService
        ExtendedAuthService.init_extended_roles_and_permissions()
        
        return jsonify({
            'message': 'Extended authentication system initialized successfully',
            'users_created': [
                'superadmin (administrateur)',
                'rh_manager (responsable_rh)', 
                'warehouse_user (magasinier)',
                'comptable_user (comptable)'
            ],
            'warning': 'Change default passwords immediately in production'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Initialization failed: {str(e)}'
        }), 500