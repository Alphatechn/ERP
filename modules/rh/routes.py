from flask import Blueprint, jsonify
from .controllers import (
    PersonnelController, CongeController, PayrollController, ReferentielController, DocumentController, AbsenceController, ContratController, 
    RubriqueController
)
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from datetime import datetime

personnel_bp = Blueprint('personnel', __name__, url_prefix='/api/personnel')


# === ROUTES BASIQUES PERSONNEL ===

@personnel_bp.route('/create', methods=['POST'])
def create_personnel():
    """
    Crée un nouveau personnel
    Headers: Authorization: Bearer <token>
    
    Body JSON:
    {
        "matricule": "string (optionnel)",
        "nom": "string",
        "prenom": "string", 
        "civilite": "M.|Mme|Mlle",
        "sexe": "M|F",
        "telephone": "string",
        "adresse": "string",
        "categorie": "string",
        "date_embauche": "YYYY-MM-DD",
        "service_id": int,
        "poste_id": int,
        // Options pour création compte utilisateur:
        "create_user_account": bool,
        "user_data": {
            "username": "string",
            "email": "string", 
            "password": "string",
            "role": "string",
            "user_type": "string"
        },
        "contrat_data": {
            "type": "CDI|CDD|Stage|Consultant",
            "date_debut": "YYYY-MM-DD",
            "date_fin": "YYYY-MM-DD (optionnel)",
            "salaire_base": float
        }
    }
    
    Nécessite: permission 'manage_hr'
    """
    return PersonnelController.create_personnel()

@personnel_bp.route('/list', methods=['GET'])
def get_personnel_list():
    verify_jwt_in_request()
    """
    Récupère la liste du personnel avec filtres et pagination
    Headers: Authorization: Bearer <token>
    
    Query Params:
    - service_id: int (filtrer par service)
    - poste_id: int (filtrer par poste)
    - status: string (actif, congé, suspendu, démissionné)
    - categorie: string (Cadre, Employé, Ouvrier)
    - search: string (recherche nom, prénom, matricule)
    - page: int (défaut: 1)
    - per_page: int (défaut: 20)
    
    Nécessite: permission 'view_personnel' ou 'manage_hr'
    """
    return PersonnelController.get_personnel_list()

@personnel_bp.route('/<int:personnel_id>', methods=['GET'])
def get_personnel_details(personnel_id):
    """
    Récupère les détails complets d'un personnel
    Headers: Authorization: Bearer <token>
    
    Retourne: Informations personnelles, contrat actuel, service, poste, statistiques
    
    Nécessite: permission 'view_personnel' ou 'manage_hr'
    """
    return PersonnelController.get_personnel_details(personnel_id)

@personnel_bp.route('/<int:personnel_id>/update', methods=['PUT'])
def update_personnel(personnel_id):
    """
    Met à jour les informations d'un personnel
    Headers: Authorization: Bearer <token>
    
    Body JSON: Champs à mettre à jour (nom, prenom, civilite, sexe, telephone, 
               adresse, categorie, service_id, poste_id, status)
    
    Nécessite: permission 'manage_hr'
    """
    return PersonnelController.update_personnel(personnel_id)

@personnel_bp.route('/<int:personnel_id>/delete', methods=['DELETE'])
def delete_personnel(personnel_id):
    """
    Supprime un personnel (soft delete)
    Headers: Authorization: Bearer <token>
    
    Nécessite: permission 'manage_hr' ET niveau_acces 'complet' (administrateur)
    """
    return PersonnelController.delete_personnel(personnel_id)


# === ROUTES GESTION DES DOCUMENTS ===

@personnel_bp.route('/<int:personnel_id>/documents/upload', methods=['POST'])
def upload_document(personnel_id):
    """
    Upload un document pour un personnel
    Headers: Authorization: Bearer <token>
    
    Form Data:
    - file: fichier à uploader
    - libelle: string (libellé du document)
    
    Nécessite: permission 'manage_hr'
    """
    verify_jwt_in_request()
    return DocumentController.upload_document(personnel_id)

@personnel_bp.route('/<int:personnel_id>/documents', methods=['GET'])
def get_personnel_documents(personnel_id):
    """
    Récupère tous les documents d'un personnel
    Headers: Authorization: Bearer <token>
    
    Nécessite: permission 'view_personnel' ou 'manage_hr'
    """
    verify_jwt_in_request()
    return DocumentController.get_personnel_documents(personnel_id)

@personnel_bp.route('/documents/<int:document_id>/delete', methods=['DELETE'])
def delete_document(document_id):
    """
    Supprime un document
    Headers: Authorization: Bearer <token>
    
    Nécessite: permission 'manage_hr'
    """
    verify_jwt_in_request()
    return DocumentController.delete_document(document_id)


# === ROUTES GESTION DES CONGÉS ===

@personnel_bp.route('/conges/create', methods=['POST'])
def create_conge():
    verify_jwt_in_request()
    """
    Crée une nouvelle demande de congé
    Headers: Authorization: Bearer <token>
    
    Body JSON:
    {
        "personnel_id": int,
        "type_conge": "string (Annuel, Maladie, Maternité, etc.)",
        "date_debut": "YYYY-MM-DD",
        "date_fin": "YYYY-MM-DD"
    }
    
    Nécessite: permission 'manage_hr' ou utilisateur peut créer sa propre demande
    """
    return CongeController.create_conge()

@personnel_bp.route('/conges/<int:conge_id>/approve', methods=['PUT'])
def approve_conge(conge_id):
    """
    Approuve une demande de congé
    Headers: Authorization: Bearer <token>
    
    Nécessite: permission 'manage_hr' ET user_type 'responsable_rh' ou 'administrateur'
    """
    return CongeController.approve_conge(conge_id)

@personnel_bp.route('/conges/<int:conge_id>/reject', methods=['PUT'])
def reject_conge(conge_id):
    """
    Rejette une demande de congé
    Headers: Authorization: Bearer <token>
    
    Body JSON:
    {
        "motif": "string (optionnel)"
    }
    
    Nécessite: permission 'manage_hr' ET user_type 'responsable_rh' ou 'administrateur'
    """
    return CongeController.reject_conge(conge_id)

@personnel_bp.route('/conges/personnel/<int:personnel_id>', methods=['GET'])
def get_conges_personnel(personnel_id):
    """
    Récupère les congés d'un personnel
    Headers: Authorization: Bearer <token>
    
    Query Params:
    - annee: int (filtrer par année)
    
    Nécessite: permission 'view_personnel' ou utilisateur peut voir ses propres congés
    """
    return CongeController.get_conges_personnel(personnel_id)

@personnel_bp.route('/conges/pending', methods=['GET'])
def get_conges_en_attente():
    """
    Récupère toutes les demandes de congé en attente
    Headers: Authorization: Bearer <token>
    
    Nécessite: permission 'manage_hr' ET user_type 'responsable_rh' ou 'administrateur'
    """
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        
        # Vérification des permissions
        if claims.get('user_type') not in ['responsable_rh', 'administrateur']:
            return jsonify({'error': 'Access restricted to HR managers and administrators'}), 403
            
        if 'manage_hr' not in claims.get('permissions', []):
            return jsonify({'error': 'Insufficient HR permissions'}), 403
        
        from .services import CongeService
        conges = CongeService.get_conges_en_attente()
        
        conges_data = []
        for conge in conges:
            conges_data.append({
                'id': conge.id,
                'personnel': {
                    'id': conge.personnel_ref.id,
                    'matricule': conge.personnel_ref.matricule,
                    'nom_complet': conge.personnel_ref.nom_complet,
                    'service': conge.personnel_ref.service_ref.libelle
                },
                'type_conge': conge.type_conge,
                'date_debut': conge.date_debut.isoformat(),
                'date_fin': conge.date_fin.isoformat(),
                'nb_jours': conge.nb_jours,
                'status': conge.status
            })
        
        return jsonify({
            'success': True,
            'message': f'{len(conges_data)} demandes en attente',
            'data': conges_data,
            'reviewed_by': claims.get('username')
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve pending leave requests: {str(e)}'
        }), 500

# === ROUTES GESTION DES ABSENCES ===

@personnel_bp.route('/absences/create', methods=['POST'])
def create_absence():
    """
    Enregistre une nouvelle absence
    Headers: Authorization: Bearer <token>
    
    Body JSON:
    {
        "personnel_id": int,
        "libelle": "string",
        "date_debut": "YYYY-MM-DD",
        "date_fin": "YYYY-MM-DD",
        "motif": "string (optionnel)",
        "justifiee": bool
    }
    
    Nécessite: permission 'manage_hr'
    """
    verify_jwt_in_request()
    return AbsenceController.create_absence()

@personnel_bp.route('/absences/personnel/<int:personnel_id>', methods=['GET'])
def get_absences_personnel(personnel_id):
    """
    Récupère les absences d'un personnel
    Headers: Authorization: Bearer <token>
    
    Query Params:
    - date_debut: YYYY-MM-DD (période de filtrage)
    - date_fin: YYYY-MM-DD (période de filtrage)
    
    Nécessite: permission 'view_personnel' ou 'manage_hr'
    """
    verify_jwt_in_request()
    return AbsenceController.get_absences_personnel(personnel_id)

@personnel_bp.route('/absences/rapport', methods=['GET'])
def get_rapport_absences():
    """
    Génère un rapport d'absences
    Headers: Authorization: Bearer <token>
    
    Query Params:
    - service_id: int (filtrer par service)
    - mois_annee: string (format: YYYY-MM)
    
    Nécessite: permission 'manage_hr'
    """
    verify_jwt_in_request()
    return AbsenceController.get_rapport_absences()

# === ROUTES GESTION DES CONTRATS ===

@personnel_bp.route('/contrats/create', methods=['POST'])
def create_contrat():
    """
    Crée un nouveau contrat
    Headers: Authorization: Bearer <token>
    
    Body JSON:
    {
        "personnel_id": int,
        "type": "CDI|CDD|Stage|Consultant",
        "date_debut": "YYYY-MM-DD",
        "date_fin": "YYYY-MM-DD (optionnel pour CDI)",
        "salaire_base": float
    }
    
    Nécessite: permission 'manage_hr' ET user_type 'responsable_rh' ou 'administrateur'
    """
    verify_jwt_in_request()
    claims = get_jwt()
    
    if claims.get('user_type') not in ['responsable_rh', 'administrateur']:
        return jsonify({'error': 'Access restricted to HR managers and administrators'}), 403
        
    if 'manage_hr' not in claims.get('permissions', []):
        return jsonify({'error': 'Insufficient HR permissions'}), 403
    
    return ContratController.create_contrat()

@personnel_bp.route('/contrats/personnel/<int:personnel_id>', methods=['GET'])
def get_contrats_personnel(personnel_id):
    """
    Récupère tous les contrats d'un personnel
    Headers: Authorization: Bearer <token>
    
    Nécessite: permission 'view_personnel' ou 'manage_hr'
    """
    verify_jwt_in_request()
    return ContratController.get_contrats_personnel(personnel_id)

@personnel_bp.route('/contrats/expires', methods=['GET'])
def get_contrats_expires():
    """
    Récupère les contrats qui arrivent à expiration (dans les 30 jours)
    Headers: Authorization: Bearer <token>
    
    Nécessite: permission 'manage_hr'
    """
    verify_jwt_in_request()
    claims = get_jwt()
    
    if 'manage_hr' not in claims.get('permissions', []):
        return jsonify({'error': 'Insufficient HR permissions'}), 403
    
    return ContratController.get_contrats_expires()

# === ROUTES GESTION DES RUBRIQUES DE PAIE ===

@personnel_bp.route('/rubriques/create', methods=['POST'])
def create_rubrique():
    """
    Crée une nouvelle rubrique de paie
    Headers: Authorization: Bearer <token>
    
    Body JSON:
    {
        "libelle": "string",
        "type": "gain|retenue|information",
        "mode_p": "fixe|variable|%",
        "valeur": float
    }
    
    Nécessite: user_type 'comptable' ou 'administrateur' ET permission 'manage_accounting'
    """
    verify_jwt_in_request()
    claims = get_jwt()
    
    if claims.get('user_type') not in ['comptable', 'administrateur']:
        return jsonify({'error': 'Access restricted to accountants and administrators'}), 403
        
    if 'manage_accounting' not in claims.get('permissions', []):
        return jsonify({'error': 'Insufficient accounting permissions'}), 403
    
    return RubriqueController.create_rubrique()

@personnel_bp.route('/rubriques/assign-poste', methods=['POST'])
def assign_rubrique_to_poste():
    """
    Assigne une rubrique à un poste
    Headers: Authorization: Bearer <token>
    
    Body JSON:
    {
        "poste_id": int,
        "rubrique_id": int,
        "montant": float
    }
    
    Nécessite: user_type 'comptable' ou 'administrateur' ET permission 'manage_accounting'
    """
    verify_jwt_in_request()
    claims = get_jwt()
    
    if claims.get('user_type') not in ['comptable', 'administrateur']:
        return jsonify({'error': 'Access restricted to accountants and administrators'}), 403
        
    if 'manage_accounting' not in claims.get('permissions', []):
        return jsonify({'error': 'Insufficient accounting permissions'}), 403
    
    return RubriqueController.assign_rubrique_to_poste()

@personnel_bp.route('/rubriques/poste/<int:poste_id>', methods=['GET'])
def get_poste_rubriques(poste_id):
    """
    Récupère les rubriques assignées à un poste
    Headers: Authorization: Bearer <token>
    
    Nécessite: permission 'manage_accounting' ou 'view_personnel'
    """
    verify_jwt_in_request()
    return RubriqueController.get_poste_rubriques(poste_id)


# === ROUTES GESTION DE LA PAIE ===

@personnel_bp.route('/payroll/exercice/create', methods=['POST'])
def create_exercice():
    verify_jwt_in_request()
    """
    Crée un nouvel exercice comptable
    Headers: Authorization: Bearer <token>
    
    Body JSON:
    {
        "mois_annee": "string (format: YYYY-MM)"
    }
    
    Nécessite: user_type 'comptable' ou 'administrateur' ET permission 'manage_accounting'
    """
    return PayrollController.create_exercice()

@personnel_bp.route('/payroll/process', methods=['POST'])
def process_payroll():
    """
    Traite la paie pour un exercice donné
    Headers: Authorization: Bearer <token>
    
    Body JSON:
    {
        "exercice_id": int,
        "personnel_ids": [int] (optionnel, tous si non spécifié)
    }
    
    Nécessite: user_type 'comptable' ou 'administrateur' ET permission 'manage_accounting'
    """
    return PayrollController.process_payroll()

@personnel_bp.route('/payroll/bulletin/<int:personnel_id>/<int:exercice_id>', methods=['GET'])
def get_bulletin_paie(personnel_id, exercice_id):
    """
    Récupère le bulletin de paie d'un personnel pour un exercice
    Headers: Authorization: Bearer <token>
    
    Nécessite: permission 'manage_accounting' ou utilisateur peut voir son propre bulletin
    """
    return PayrollController.get_bulletin_paie(personnel_id, exercice_id)

@personnel_bp.route('/payroll/report/<int:exercice_id>', methods=['GET'])
def get_rapport_paie(exercice_id):
    """
    Génère un rapport de paie pour un exercice
    Headers: Authorization: Bearer <token>
    Query Params:
    - service_id: int (filtrer par service)
    Nécessite: user_type 'comptable' ou 'administrateur' ET permission 'manage_accounting'
    """
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        
        # Vérification des permissions
        if claims.get('user_type') not in ['comptable', 'administrateur']:
            return jsonify({'error': 'Access restricted to accountants and administrators'}), 403
        if 'manage_accounting' not in claims.get('permissions', []):
            return jsonify({'error': 'Insufficient accounting permissions'}), 403
        
        # Import déplacé en haut pour éviter les erreurs
        from .services import PayrollService
        from flask import request
        
        # Récupération des paramètres de requête
        service_id = request.args.get('service_id', type=int)
        
        # CORRECTION: Passer service_id au service si fourni
        if service_id:
            rapport = PayrollService.get_rapport_paie(exercice_id, service_id=service_id)
        else:
            rapport = PayrollService.get_rapport_paie(exercice_id)
        
        # CORRECTION: Vérifier que le rapport n'est pas None
        if not rapport:
            return jsonify({
                'success': False,
                'error': 'No payroll data found for this exercise'
            }), 404
        
        # CORRECTION: Gestion flexible de la structure de retour
        exercice_info = rapport['exercice']
        if hasattr(exercice_info, 'id'):  # Si c'est un objet SQLAlchemy
            exercice_data = {
                'id': exercice_info.id,
                'mois_annee': exercice_info.mois_annee,
                'status': exercice_info.status
            }
        else:  # Si c'est déjà un dictionnaire
            exercice_data = exercice_info
        
        # CORRECTION: Utiliser des noms de clés cohérents
        response_data = {
            'exercice': exercice_data,
            'lignes': rapport.get('personnel_data', rapport.get('lignes', [])),
            'totaux': rapport.get('totaux', {}),
            'filters_applied': {
                'service_id': service_id
            } if service_id else {}
        }
        
        return jsonify({
            'success': True,
            'message': 'Payroll report generated successfully',
            'data': response_data,
            'generated_by': claims.get('username'),
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except ValueError as ve:
        # Erreurs de validation (exercice inexistant, etc.)
        return jsonify({
            'success': False,
            'error': str(ve)
        }), 400
        
    except PermissionError as pe:
        # Erreurs de permissions
        return jsonify({
            'success': False,
            'error': str(pe)
        }), 403
        
    except Exception as e:
        # Log l'erreur pour debugging
        print(f"[PAYROLL_REPORT_ERROR] Exercice {exercice_id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': f'Failed to generate payroll report: {str(e)}'
        }), 500

@personnel_bp.route('/payroll/exercice/<int:exercice_id>/close', methods=['PUT'])
def close_exercice(exercice_id):
    """
    Clôture un exercice comptable
    Headers: Authorization: Bearer <token>
    
    Nécessite: user_type 'comptable' ou 'administrateur' ET permission 'manage_accounting'
    """
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        user_id = get_jwt_identity()
        
        if claims.get('user_type') not in ['comptable', 'administrateur']:
            return jsonify({'error': 'Access restricted to accountants and administrators'}), 403
            
        if 'manage_accounting' not in claims.get('permissions', []):
            return jsonify({'error': 'Insufficient accounting permissions'}), 403
        
        from .services import PayrollService
        
        exercice = PayrollService.close_exercice(exercice_id, user_id)
        
        return jsonify({
            'success': True,
            'message': 'Exercice clôturé avec succès',
            'data': {
                'id': exercice.id,
                'mois_annee': exercice.mois_annee,
                'status': exercice.status
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400


# === ROUTES RÉFÉRENTIELS ===

@personnel_bp.route('/referentiels/services', methods=['GET'])
def get_services():
    """
    Récupère la liste des services/départements
    Headers: Authorization: Bearer <token>
    
    Accessible à tous les utilisateurs connectés
    """
    return ReferentielController.get_services()

@personnel_bp.route('/referentiels/postes', methods=['GET'])
def get_postes():
    """
    Récupère la liste des postes/fonctions
    Headers: Authorization: Bearer <token>
    
    Accessible à tous les utilisateurs connectés
    """
    return ReferentielController.get_postes()

@personnel_bp.route('/referentiels/exercices', methods=['GET'])
def get_exercices():
    """
    Récupère la liste des exercices comptables
    Headers: Authorization: Bearer <token>
    
    Nécessite: permission 'manage_accounting' ou 'view_personnel'
    """
    return ReferentielController.get_exercices()

@personnel_bp.route('/referentiels/rubriques', methods=['GET'])
def get_rubriques():
    """
    Récupère la liste des rubriques de paie
    Headers: Authorization: Bearer <token>
    
    Query Params:
    - type: string (gain, retenue, information)
    
    Nécessite: permission 'manage_accounting'
    """
    return ReferentielController.get_rubriques()

# === ROUTES SPÉCIALISÉES PAR TYPE D'UTILISATEUR ===

@personnel_bp.route('/hr/dashboard', methods=['GET'])
def hr_dashboard():
    """
    [RESPONSABLE RH] Dashboard avec statistiques RH
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
        
        from .models import Personnel, Conge
        from core.database import db
        
        # Statistiques RH
        stats = {
            'total_personnel': Personnel.query.filter_by(status='actif').count(),
            'nouveaux_ce_mois': Personnel.query.filter(
                Personnel.status == 'actif',
                db.extract('month', Personnel.date_embauche) == datetime.now().month,
                db.extract('year', Personnel.date_embauche) == datetime.now().year
            ).count(),
            'conges_en_attente': Conge.query.filter_by(status='demande').count(),
            'conges_approuves_ce_mois': Conge.query.filter(
                Conge.status == 'approuve',
                db.extract('month', Conge.date_debut) == datetime.now().month
            ).count()
        }
        
        return jsonify({
            'message': 'HR Dashboard data retrieved',
            'stats': stats,
            'hr_manager': claims.get('username'),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'HR dashboard failed: {str(e)}'}), 500

@personnel_bp.route('/accounting/payroll-summary', methods=['GET'])
def accounting_payroll_summary():
    """
    [COMPTABLE] Résumé des paies et exercices
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
        
        from .models import Exercice, Payer, Personnel
        from core.database import db
        
        # Statistiques comptables
        stats = {
            'exercices_ouverts': Exercice.query.filter_by(status='ouvert').count(),
            'exercices_clos': Exercice.query.filter_by(status='clos').count(),
            'dernier_exercice': Exercice.query.order_by(Exercice.mois_annee.desc()).first(),
            'total_paies_traitees': db.session.query(Payer.personnel_id).distinct().count(),
            'montant_total_paies': db.session.query(db.func.sum(Payer.montant)).scalar() or 0
        }
        
        # Formater le dernier exercice
        if stats['dernier_exercice']:
            stats['dernier_exercice'] = {
                'id': stats['dernier_exercice'].id,
                'mois_annee': stats['dernier_exercice'].mois_annee,
                'status': stats['dernier_exercice'].status
            }
        
        return jsonify({
            'message': 'Accounting payroll summary retrieved',
            'stats': stats,
            'comptable': claims.get('username'),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Accounting summary failed: {str(e)}'}), 500

# === ROUTES DE TEST ET HEALTH ===

@personnel_bp.route('/health', methods=['GET'])
def health():
    """Check de santé du module personnel"""
    return {
        'status': 'Personnel module running',
        'timestamp': datetime.utcnow().isoformat(),
        'features': [
            'Personnel management',
            'Leave management', 
            'Payroll processing',
            'Contract management'
        ]
    }, 200

@personnel_bp.route('/test-permissions', methods=['GET'])
def test_permissions():
    """
    Test des permissions du module personnel
    Headers: Authorization: Bearer <token>
    """
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        user_id = get_jwt_identity()
        
        # Analyser les permissions personnel
        permissions = claims.get('permissions', [])
        personnel_permissions = [p for p in permissions if 'hr' in p or 'accounting' in p or 'personnel' in p]
        
        return jsonify({
            'message': 'Personnel permissions analyzed',
            'user_id': user_id,
            'username': claims.get('username'),
            'user_type': claims.get('user_type', 'user'),
            'all_permissions': permissions,
            'personnel_permissions': personnel_permissions,
            'can_manage_hr': 'manage_hr' in permissions,
            'can_manage_accounting': 'manage_accounting' in permissions,
            'can_view_personnel': 'view_personnel' in permissions
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Permission test failed: {str(e)}'}), 401

# === ROUTE D'INITIALISATION ===

@personnel_bp.route('/init-personnel-system', methods=['POST'])
def init_personnel_system():
    """
    Initialise le système de gestion du personnel avec données de test
    ⚠️  À utiliser uniquement en développement
    """
    try:
        from .services import PersonnelInitService
        success = PersonnelInitService.init_personnel_system()
        
        if success:
            return jsonify({
                'message': 'Personnel management system initialized successfully',
                'components_created': [
                    'Services/Départements',
                    'Postes/Fonctions',
                    'Rubriques de paie',
                    'Structure de base'
                ],
                'warning': 'This is for development only'
            }), 200
        else:
            return jsonify({
                'error': 'Personnel system initialization failed'
            }), 500
        
    except Exception as e:
        return jsonify({
            'error': f'Initialization failed: {str(e)}'
        }), 500