
from flask_restful import Resource, reqparse
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from datetime import datetime, date
from .services import (
    PersonnelService, DocumentService, CongeService, 
    AbsenceService, ContratService, PayrollService, RubriqueService
)
from .models import Personnel, Service, Poste, Exercice, Rubrique, Absence, Document
from core.utils import permission_required

class PersonnelResource(Resource):
    """Resource pour la gestion du personnel"""
    
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('matricule', help='Matricule du personnel')
        self.parser.add_argument('nom', required=True, help='Nom est requis')
        self.parser.add_argument('prenom', required=True, help='Prénom est requis')
        self.parser.add_argument('civilite', choices=['M.', 'Mme', 'Mlle'], help='Civilité (M.|Mme|Mlle)')
        self.parser.add_argument('sexe', choices=['M', 'F'], help='Sexe (M|F)')
        self.parser.add_argument('telephone', help='Téléphone')
        self.parser.add_argument('adresse', help='Adresse')
        self.parser.add_argument('categorie', help='Catégorie')
        self.parser.add_argument('date_embauche', required=True, help='Date d\'embauche est requise (YYYY-MM-DD)')
        self.parser.add_argument('service_id', type=int, required=True, help='ID du service est requis')
        self.parser.add_argument('poste_id', type=int, required=True, help='ID du poste est requis')
        self.parser.add_argument('create_user_account', type=bool, default=False, help='Créer un compte utilisateur')
        self.parser.add_argument('user_data', type=dict, help='Données utilisateur')
        self.parser.add_argument('contrat_data', type=dict, help='Données contrat')

    # @permission_required('manage_hr')
    def post(self):
        """Crée un nouveau personnel"""
        try:
            args = self.parser.parse_args()
            
            personnel_data = {
                'matricule': args['matricule'],
                'nom': args['nom'],
                'prenom': args['prenom'],
                'civilite': args['civilite'],
                'sexe': args['sexe'],
                'telephone': args['telephone'],
                'adresse': args['adresse'],
                'categorie': args['categorie'],
                'date_embauche': datetime.strptime(args['date_embauche'], '%Y-%m-%d').date(),
                'service_id': args['service_id'],
                'poste_id': args['poste_id']
            }
            
            result = PersonnelService.create_personnel(
                personnel_data=personnel_data,
                create_user_account=args['create_user_account'],
                user_data=args['user_data'],
                contrat_data=args['contrat_data']
            )
            
            return {
                'success': True,
                'message': 'Personnel créé avec succès',
                'data': {
                    'id': result['personnel'].id,
                    'matricule': result['personnel'].matricule,
                    'nom_complet': result['personnel'].nom_complet
                }
            }, 201
            
        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            return {'error': 'Échec de la création du personnel'}, 500

    @permission_required('view_personnel')
    def get(self):
        """Récupère la liste du personnel avec filtres"""
        try:
            # Récupérer les paramètres de filtrage
            filters = {}
            if request.args.get('service_id'):
                filters['service_id'] = int(request.args.get('service_id'))
            if request.args.get('poste_id'):
                filters['poste_id'] = int(request.args.get('poste_id'))
            if request.args.get('status'):
                filters['status'] = request.args.get('status')
            if request.args.get('categorie'):
                filters['categorie'] = request.args.get('categorie')
            if request.args.get('search'):
                filters['search'] = request.args.get('search')
            
            # Pagination
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            result = PersonnelService.get_personnel_list(
                filters=filters,
                page=page,
                per_page=per_page
            )
            
            # Formater les données
            personnels_data = []
            for personnel in result['personnels']:
                personnels_data.append({
                    'id': personnel.id,
                    'matricule': personnel.matricule,
                    'nom_complet': personnel.nom_complet,
                    'service': personnel.service_ref.libelle,
                    'poste': personnel.poste_ref.fonction,
                    'categorie': personnel.categorie,
                    'date_embauche': personnel.date_embauche.isoformat(),
                    'status': personnel.status
                })
            
            return {
                'success': True,
                'data': personnels_data,
                'pagination': {
                    'total': result['total'],
                    'pages': result['pages'],
                    'current_page': result['current_page'],
                    'per_page': result['per_page']
                }
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération du personnel'}, 500

class PersonnelDetailResource(Resource):
    """Resource pour les détails d'un personnel spécifique"""
    
    @permission_required('view_personnel')
    def get(self, personnel_id):
        """Récupère les détails d'un personnel"""
        try:
            result = PersonnelService.get_personnel_details(personnel_id)
            
            if not result:
                return {'error': 'Personnel introuvable'}, 404
            
            personnel_data = {
                'id': result['personnel'].id,
                'matricule': result['personnel'].matricule,
                'nom': result['personnel'].nom,
                'prenom': result['personnel'].prenom,
                'nom_complet': result['personnel'].nom_complet,
                'civilite': result['personnel'].civilite,
                'sexe': result['personnel'].sexe,
                'telephone': result['personnel'].telephone,
                'adresse': result['personnel'].adresse,
                'categorie': result['personnel'].categorie,
                'date_embauche': result['personnel'].date_embauche.isoformat(),
                'status': result['personnel'].status,
                'service': {
                    'id': result['service'].id,
                    'libelle': result['service'].libelle
                },
                'poste': {
                    'id': result['poste'].id,
                    'fonction': result['poste'].fonction
                },
                'contrat_actuel': {
                    'type': result['contrat_actuel'].type,
                    'salaire_base': result['contrat_actuel'].salaire_base
                } if result['contrat_actuel'] else None,
                'statistiques': {
                    'nb_conges_pris': result['nb_conges_pris'],
                    'nb_absences': result['nb_absences']
                }
            }
            
            return {
                'success': True,
                'data': personnel_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération des détails'}, 500

    @permission_required('manage_hr')
    def put(self, personnel_id):
        """Met à jour un personnel"""
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('nom')
            parser.add_argument('prenom')
            parser.add_argument('civilite', choices=['M.', 'Mme', 'Mlle'])
            parser.add_argument('sexe', choices=['M', 'F'])
            parser.add_argument('telephone')
            parser.add_argument('adresse')
            parser.add_argument('categorie')
            parser.add_argument('service_id', type=int)
            parser.add_argument('poste_id', type=int)
            parser.add_argument('status', choices=['actif', 'congé', 'suspendu', 'démissionné'])
            
            args = parser.parse_args()
            
            personnel = PersonnelService.update_personnel(personnel_id, args)
            
            return {
                'success': True,
                'message': 'Personnel mis à jour avec succès',
                'data': {
                    'id': personnel.id,
                    'nom_complet': personnel.nom_complet
                }
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la mise à jour du personnel'}, 500

    @permission_required('manage_hr')
    def delete(self, personnel_id):
        """Supprime un personnel"""
        try:
            PersonnelService.delete_personnel(personnel_id)
            
            return {
                'success': True,
                'message': 'Personnel supprimé avec succès'
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la suppression du personnel'}, 500

class CongeResource(Resource):
    """Resource pour la gestion des congés"""
    
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('personnel_id', type=int, required=True, help='ID du personnel est requis')
        self.parser.add_argument('type_conge', required=True, help='Type de congé est requis')
        self.parser.add_argument('date_debut', required=True, help='Date de début est requise (YYYY-MM-DD)')
        self.parser.add_argument('date_fin', required=True, help='Date de fin est requise (YYYY-MM-DD)')

    @permission_required('manage_hr')
    def post(self):
        """Crée une demande de congé"""
        try:
            args = self.parser.parse_args()
            
            conge = CongeService.create_demande_conge(
                personnel_id=args['personnel_id'],
                type_conge=args['type_conge'],
                date_debut=datetime.strptime(args['date_debut'], '%Y-%m-%d').date(),
                date_fin=datetime.strptime(args['date_fin'], '%Y-%m-%d').date()
            )
            
            return {
                'success': True,
                'message': 'Demande de congé créée avec succès',
                'data': {
                    'id': conge.id,
                    'type_conge': conge.type_conge,
                    'nb_jours': conge.nb_jours,
                    'status': conge.status
                }
            }, 201
            
        except Exception as e:
            return {'error': 'Échec de la création du congé'}, 500

class CongeApproveResource(Resource):
    """Resource pour l'approbation des congés"""
    
    @permission_required('manage_hr')
    def put(self, conge_id):
        """Approuve une demande de congé"""
        try:
            verify_jwt_in_request()
            approved_by_user_id = int(get_jwt_identity())
            
            conge = CongeService.approve_conge(conge_id, approved_by_user_id)
            
            return {
                'success': True,
                'message': 'Congé approuvé avec succès',
                'data': {
                    'id': conge.id,
                    'status': conge.status
                }
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de l\'approbation du congé'}, 500

class CongeRejectResource(Resource):
    """Resource pour le rejet des congés"""
    
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('motif', help='Motif du rejet')

    @permission_required('manage_hr')
    def put(self, conge_id):
        """Rejette une demande de congé"""
        try:
            verify_jwt_in_request()
            rejected_by_user_id = int(get_jwt_identity())
            args = self.parser.parse_args()
            
            conge = CongeService.reject_conge(conge_id, rejected_by_user_id, args.get('motif'))
            
            return {
                'success': True,
                'message': 'Congé rejeté avec succès',
                'data': {
                    'id': conge.id,
                    'status': conge.status
                }
            }, 200
            
        except Exception as e:
            return {'error': 'Échec du rejet du congé'}, 500

class PersonnelCongesResource(Resource):
    """Resource pour les congés d'un personnel"""
    
    @permission_required('view_personnel')
    def get(self, personnel_id):
        """Récupère les congés d'un personnel"""
        try:
            annee = request.args.get('annee')
            if annee:
                annee = int(annee)
            
            conges = CongeService.get_conges_personnel(personnel_id, annee)
            
            conges_data = []
            for conge in conges:
                conges_data.append({
                    'id': conge.id,
                    'type_conge': conge.type_conge,
                    'date_debut': conge.date_debut.isoformat(),
                    'date_fin': conge.date_fin.isoformat(),
                    'nb_jours': conge.nb_jours,
                    'status': conge.status
                })
            
            return {
                'success': True,
                'data': conges_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération des congés'}, 500

class PayrollExerciceResource(Resource):
    """Resource pour la gestion des exercices de paie"""
    
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('mois_annee', required=True, help='Mois-année est requis (YYYY-MM)')

    @permission_required('manage_accounting')
    def post(self):
        """Crée un nouvel exercice"""
        try:
            args = self.parser.parse_args()
            
            exercice = PayrollService.create_exercice(args['mois_annee'])
            
            return {
                'success': True,
                'message': 'Exercice créé avec succès',
                'data': {
                    'id': exercice.id,
                    'mois_annee': exercice.mois_annee,
                    'status': exercice.status
                }
            }, 201
            
        except Exception as e:
            return {'error': 'Échec de la création de l\'exercice'}, 500

class PayrollProcessResource(Resource):
    """Resource pour le traitement de la paie"""
    
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('exercice_id', type=int, required=True, help='ID de l\'exercice est requis')
        self.parser.add_argument('personnel_ids', type=list, location='json', help='Liste des IDs du personnel')

    @permission_required('manage_accounting')
    def post(self):
        """Traite la paie pour un exercice"""
        try:
            args = self.parser.parse_args()
            
            result = PayrollService.process_payroll(
                exercice_id=args['exercice_id'],
                personnel_ids=args['personnel_ids']
            )
            
            return {
                'success': True,
                'message': 'Traitement de la paie terminé',
                'data': result
            }, 200
            
        except Exception as e:
            return {'error': 'Échec du traitement de la paie'}, 500

class BulletinPaieResource(Resource):
    """Resource pour les bulletins de paie"""
    
    # @permission_required('view_personnel')
    def get(self, personnel_id, exercice_id):
        """Récupère le bulletin de paie"""
        try:
            bulletin = PayrollService.get_bulletin_paie(personnel_id, exercice_id)
            
            if not bulletin:
                return {'error': 'Bulletin de paie introuvable'}, 404
            
            bulletin_data = {
                'personnel': {
                    'matricule': bulletin['personnel'].matricule,
                    'nom_complet': bulletin['personnel'].nom_complet,
                    'service': bulletin['personnel'].service_ref.libelle,
                    'poste': bulletin['personnel'].poste_ref.fonction
                },
                'exercice': {
                    'mois_annee': bulletin['exercice'].mois_annee
                },
                'lignes': [
                    {
                        'rubrique': ligne['rubrique'].libelle,
                        'type': ligne['rubrique'].type,
                        'montant': ligne['montant']
                    }
                    for ligne in bulletin['lignes']
                ],
                'totaux': {
                    'total_gains': bulletin['total_gains'],
                    'total_retenues': bulletin['total_retenues'],
                    'net_payer': bulletin['net_payer']
                }
            }
            
            return {
                'success': True,
                'data': bulletin_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération du bulletin'}, 500

class ReferentielServicesResource(Resource):
    """Resource pour les services"""
    
    def get(self):
        """Récupère la liste des services"""
        try:
            services = Service.query.filter_by(status='actif').all()
            
            services_data = [
                {
                    'id': service.id,
                    'libelle': service.libelle,
                    'status': service.status
                }
                for service in services
            ]
            
            return {
                'success': True,
                'data': services_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération des services'}, 500

class ReferentielPostesResource(Resource):
    """Resource pour les postes"""
    
    def get(self):
        """Récupère la liste des postes"""
        try:
            postes = Poste.query.filter_by(status='actif').all()
            
            postes_data = [
                {
                    'id': poste.id,
                    'fonction': poste.fonction,
                    't_horaire': poste.t_horaire,
                    'status': poste.status
                }
                for poste in postes
            ]
            
            return {
                'success': True,
                'data': postes_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération des postes'}, 500

class ReferentielExercicesResource(Resource):
    """Resource pour les exercices"""
    
    def get(self):
        """Récupère la liste des exercices"""
        try:
            exercices = Exercice.query.order_by(Exercice.mois_annee.desc()).all()
            
            exercices_data = [
                {
                    'id': exercice.id,
                    'mois_annee': exercice.mois_annee,
                    'status': exercice.status,
                    'annee': exercice.annee,
                    'mois': exercice.mois
                }
                for exercice in exercices
            ]
            
            return {
                'success': True,
                'data': exercices_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération des exercices'}, 500

class ReferentielRubriquesResource(Resource):
    """Resource pour les rubriques"""
    
    def get(self):
        """Récupère la liste des rubriques"""
        try:
            type_filter = request.args.get('type')
            
            query = Rubrique.query.filter_by(status='actif')
            if type_filter:
                query = query.filter_by(type=type_filter)
            
            rubriques = query.all()
            
            rubriques_data = [
                {
                    'id': rubrique.id,
                    'libelle': rubrique.libelle,
                    'type': rubrique.type,
                    'mode_p': rubrique.mode_p,
                    'valeur': rubrique.valeur
                }
                for rubrique in rubriques
            ]
            
            return {
                'success': True,
                'data': rubriques_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération des rubriques'}, 500

class DocumentResource(Resource):
    """Resource pour la gestion des documents"""
    
    @permission_required('manage_hr')
    def post(self, personnel_id):
        """Upload un document pour un personnel"""
        try:
            verify_jwt_in_request()
            
            parser = reqparse.RequestParser()
            parser.add_argument('libelle', required=True, help='Libellé du document est requis')
            args = parser.parse_args()
            
            if 'file' not in request.files:
                return {'error': 'Aucun fichier fourni'}, 400
            
            file = request.files['file']
            if file.filename == '':
                return {'error': 'Nom de fichier vide'}, 400
            
            document = DocumentService.upload_document(
                personnel_id=personnel_id,
                file=file,
                libelle=args['libelle']
            )
            
            return {
                'success': True,
                'message': 'Document uploadé avec succès',
                'data': {
                    'id': document.id,
                    'libelle': document.libelle,
                    'url_fichier': document.url_fichier,
                    'date_creation': document.date_creation.isoformat()
                }
            }, 201
            
        except Exception as e:
            return {'error': 'Échec de l\'upload du document'}, 500

    @permission_required('view_personnel')
    def get(self, personnel_id):
        """Récupère tous les documents d'un personnel"""
        try:
            verify_jwt_in_request()
            
            documents = DocumentService.get_personnel_documents(personnel_id)
            
            documents_data = []
            for doc in documents:
                documents_data.append({
                    'id': doc.id,
                    'libelle': doc.libelle,
                    'url_fichier': doc.url_fichier,
                    'date_creation': doc.date_creation.isoformat(),
                    'taille_fichier': doc.taille_fichier
                })
            
            return {
                'success': True,
                'data': documents_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération des documents'}, 500

class DocumentDeleteResource(Resource):
    """Resource pour la suppression des documents"""
    
    @permission_required('manage_hr')
    def delete(self, document_id):
        """Supprime un document"""
        try:
            verify_jwt_in_request()
            
            DocumentService.delete_document(document_id)
            
            return {
                'success': True,
                'message': 'Document supprimé avec succès'
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la suppression du document'}, 500

class AbsenceResource(Resource):
    """Resource pour la gestion des absences"""
    
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('personnel_id', type=int, required=True, help='ID du personnel est requis')
        self.parser.add_argument('libelle', required=True, help='Libellé est requis')
        self.parser.add_argument('date_debut', required=True, help='Date de début est requise (YYYY-MM-DD)')
        self.parser.add_argument('date_fin', required=True, help='Date de fin est requise (YYYY-MM-DD)')
        self.parser.add_argument('motif', help='Motif de l\'absence')
        self.parser.add_argument('justifiee', type=bool, default=False, help='Absence justifiée')

    @permission_required('manage_hr')
    def post(self):
        """Enregistre une nouvelle absence"""
        try:
            args = self.parser.parse_args()
            
            absence = AbsenceService.create_absence(
                personnel_id=args['personnel_id'],
                libelle=args['libelle'],
                date_debut=datetime.strptime(args['date_debut'], '%Y-%m-%d').date(),
                date_fin=datetime.strptime(args['date_fin'], '%Y-%m-%d').date(),
                motif=args['motif'],
                justifiee=args['justifiee']
            )
            
            return {
                'success': True,
                'message': 'Absence enregistrée avec succès',
                'data': {
                    'id': absence.id,
                    'libelle': absence.libelle,
                    'nb_jours': absence.nb_jours,
                    'justifiee': absence.justifiee
                }
            }, 201
            
        except Exception as e:
            return {'error': 'Échec de l\'enregistrement de l\'absence'}, 500

class PersonnelAbsencesResource(Resource):
    """Resource pour les absences d'un personnel"""
    
    @permission_required('view_personnel')
    def get(self, personnel_id):
        """Récupère les absences d'un personnel"""
        try:
            verify_jwt_in_request()
            
            # Récupérer les paramètres de période
            periode = None
            if request.args.get('date_debut') and request.args.get('date_fin'):
                periode = {
                    'debut': datetime.strptime(request.args.get('date_debut'), '%Y-%m-%d').date(),
                    'fin': datetime.strptime(request.args.get('date_fin'), '%Y-%m-%d').date()
                }
            
            absences = AbsenceService.get_absences_personnel(personnel_id, periode)
            
            absences_data = []
            for absence in absences:
                absences_data.append({
                    'id': absence.id,
                    'libelle': absence.libelle,
                    'date_debut': absence.date_debut.isoformat(),
                    'date_fin': absence.date_fin.isoformat(),
                    'nb_jours': absence.nb_jours,
                    'motif': absence.motif,
                    'justifiee': absence.justifiee
                })
            
            return {
                'success': True,
                'data': absences_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération des absences'}, 500

class RapportAbsencesResource(Resource):
    """Resource pour les rapports d'absences"""
    
    @permission_required('manage_hr')
    def get(self):
        """Génère un rapport d'absences"""
        try:
            verify_jwt_in_request()
            
            service_id = request.args.get('service_id', type=int)
            mois_annee = request.args.get('mois_annee')
            
            rapport = AbsenceService.get_rapport_absences(service_id, mois_annee)
            
            rapport_data = []
            for ligne in rapport:
                rapport_data.append({
                    'matricule': ligne.matricule,
                    'nom_complet': f"{ligne.nom} {ligne.prenom}",
                    'service': ligne.service,
                    'nb_absences': ligne.nb_absences,
                    'total_jours': ligne.total_jours
                })
            
            return {
                'success': True,
                'message': 'Rapport d\'absences généré',
                'data': rapport_data,
                'filters': {
                    'service_id': service_id,
                    'mois_annee': mois_annee
                }
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la génération du rapport'}, 500

class ContratResource(Resource):
    """Resource pour la gestion des contrats"""
    
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('personnel_id', type=int, required=True, help='ID du personnel est requis')
        self.parser.add_argument('type', required=True, choices=['CDI', 'CDD', 'Stage', 'Consultant'], help='Type de contrat est requis')
        self.parser.add_argument('date_debut', required=True, help='Date de début est requise (YYYY-MM-DD)')
        self.parser.add_argument('salaire_base', type=float, required=True, help='Salaire base est requis')
        self.parser.add_argument('date_fin', help='Date de fin (YYYY-MM-DD)')

    @permission_required('manage_hr')
    def post(self):
        """Crée un nouveau contrat"""
        try:
            args = self.parser.parse_args()
            
            contrat = ContratService.create_contrat(
                personnel_id=args['personnel_id'],
                type_contrat=args['type'],
                date_debut=datetime.strptime(args['date_debut'], '%Y-%m-%d').date(),
                salaire_base=args['salaire_base'],
                date_fin=datetime.strptime(args['date_fin'], '%Y-%m-%d').date() if args['date_fin'] else None
            )
            
            return {
                'success': True,
                'message': 'Contrat créé avec succès',
                'data': {
                    'id': contrat.id,
                    'type': contrat.type,
                    'date_debut': contrat.date_debut.isoformat(),
                    'date_fin': contrat.date_fin.isoformat() if contrat.date_fin else None,
                    'salaire_base': contrat.salaire_base,
                    'status': contrat.status
                }
            }, 201
            
        except Exception as e:
            return {'error': 'Échec de la création du contrat'}, 500

class PersonnelContratsResource(Resource):
    """Resource pour les contrats d'un personnel"""
    
    @permission_required('view_personnel')
    def get(self, personnel_id):
        """Récupère tous les contrats d'un personnel"""
        try:
            verify_jwt_in_request()
            
            contrats = ContratService.get_contrats_personnel(personnel_id)
            
            contrats_data = []
            for contrat in contrats:
                contrats_data.append({
                    'id': contrat.id,
                    'type': contrat.type,
                    'date_debut': contrat.date_debut.isoformat(),
                    'date_fin': contrat.date_fin.isoformat() if contrat.date_fin else None,
                    'salaire_base': contrat.salaire_base,
                    'status': contrat.status
                })
            
            return {
                'success': True,
                'data': contrats_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération des contrats'}, 500

class ContratsExpiresResource(Resource):
    """Resource pour les contrats expirés"""
    
    @permission_required('manage_hr')
    def get(self):
        """Récupère les contrats qui arrivent à expiration"""
        try:
            verify_jwt_in_request()
            
            contrats = ContratService.get_contrats_expires()
            
            contrats_data = []
            for contrat in contrats:
                contrats_data.append({
                    'id': contrat.id,
                    'personnel': {
                        'id': contrat.personnel_ref.id,
                        'matricule': contrat.personnel_ref.matricule,
                        'nom_complet': contrat.personnel_ref.nom_complet,
                        'service': contrat.personnel_ref.service_ref.libelle
                    },
                    'type': contrat.type,
                    'date_fin': contrat.date_fin.isoformat(),
                    'jours_restants': (contrat.date_fin - date.today()).days
                })
            
            return {
                'success': True,
                'message': f'{len(contrats_data)} contrats arrivent à expiration',
                'data': contrats_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération des contrats expirés'}, 500

class RubriqueResource(Resource):
    """Resource pour la gestion des rubriques de paie"""
    
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('libelle', required=True, help='Libellé est requis')
        self.parser.add_argument('type', required=True, choices=['gain', 'retenue', 'information'], help='Type est requis')
        self.parser.add_argument('mode_p', required=True, choices=['fixe', 'variable', '%'], help='Mode de paiement est requis')
        self.parser.add_argument('valeur', type=float, required=True, help='Valeur est requise')

    @permission_required('manage_accounting')
    def post(self):
        """Crée une nouvelle rubrique de paie"""
        try:
            args = self.parser.parse_args()
            
            rubrique = RubriqueService.create_rubrique(
                libelle=args['libelle'],
                type_rubrique=args['type'],
                mode_p=args['mode_p'],
                valeur=args['valeur']
            )
            
            return {
                'success': True,
                'message': 'Rubrique créée avec succès',
                'data': {
                    'id': rubrique.id,
                    'libelle': rubrique.libelle,
                    'type': rubrique.type,
                    'mode_p': rubrique.mode_p,
                    'valeur': rubrique.valeur
                }
            }, 201
            
        except Exception as e:
            return {'error': 'Échec de la création de la rubrique'}, 500

class AssignRubriqueResource(Resource):
    """Resource pour l'assignation des rubriques aux postes"""
    
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('poste_id', type=int, required=True, help='ID du poste est requis')
        self.parser.add_argument('rubrique_id', type=int, required=True, help='ID de la rubrique est requis')
        self.parser.add_argument('montant', type=float, required=True, help='Montant est requis')

    @permission_required('manage_accounting')
    def post(self):
        """Assigne une rubrique à un poste"""
        try:
            args = self.parser.parse_args()
            
            RubriqueService.assign_rubrique_to_poste(
                poste_id=args['poste_id'],
                rubrique_id=args['rubrique_id'],
                montant=args['montant']
            )
            
            return {
                'success': True,
                'message': 'Rubrique assignée au poste avec succès'
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de l\'assignation de la rubrique'}, 500

class PosteRubriquesResource(Resource):
    """Resource pour les rubriques d'un poste"""
    
    @permission_required('view_personnel')
    def get(self, poste_id):
        """Récupère les rubriques d'un poste"""
        try:
            verify_jwt_in_request()
            
            rubriques = RubriqueService.get_poste_rubriques(poste_id)
            
            rubriques_data = []
            for poste_rubrique in rubriques:
                rubriques_data.append({
                    'id': poste_rubrique.id,
                    'rubrique': {
                        'id': poste_rubrique.rubrique_ref.id,
                        'libelle': poste_rubrique.rubrique_ref.libelle,
                        'type': poste_rubrique.rubrique_ref.type,
                        'mode_p': poste_rubrique.rubrique_ref.mode_p
                    },
                    'montant': poste_rubrique.montant,
                    'date_creation': poste_rubrique.date_creation.isoformat(),
                    'status': poste_rubrique.status
                })
            
            return {
                'success': True,
                'data': rubriques_data
            }, 200
            
        except Exception as e:
            return {'error': 'Échec de la récupération des rubriques du poste'}, 500

class HRDashboardResource(Resource):
    """Resource pour le dashboard RH"""
    
    @permission_required('manage_hr')
    def get(self):
        """Récupère les statistiques du dashboard RH"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
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
            
            return {
                'message': 'HR Dashboard data retrieved',
                'stats': stats,
                'hr_manager': claims.get('username'),
                'timestamp': datetime.utcnow().isoformat()
            }, 200
            
        except Exception as e:
            return {'error': f'HR dashboard failed: {str(e)}'}, 500

class AccountingDashboardResource(Resource):
    """Resource pour le dashboard comptable"""
    
    @permission_required('manage_accounting')
    def get(self):
        """Récupère les statistiques du dashboard comptable"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            from .models import Exercice, Payer
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
            
            return {
                'message': 'Accounting payroll summary retrieved',
                'stats': stats,
                'comptable': claims.get('username'),
                'timestamp': datetime.utcnow().isoformat()
            }, 200
            
        except Exception as e:
            return {'error': f'Accounting summary failed: {str(e)}'}, 500

class HealthResource(Resource):
    """Resource pour la santé du module"""
    
    def get(self):
        """Check de santé du module RH"""
        return {
            'status': 'RH module running',
            'timestamp': datetime.utcnow().isoformat(),
            'features': [
                'Personnel management',
                'Leave management', 
                'Payroll processing',
                'Contract management'
            ]
        }, 200

class TestPermissionsResource(Resource):
    """Resource pour tester les permissions"""
    
    def get(self):
        """Test des permissions du module RH"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            user_id = get_jwt_identity()
            
            # Analyser les permissions personnel
            permissions = claims.get('permissions', [])
            personnel_permissions = [p for p in permissions if 'hr' in p or 'accounting' in p or 'personnel' in p]
            
            return {
                'message': 'Personnel permissions analyzed',
                'user_id': user_id,
                'username': claims.get('username'),
                'user_type': claims.get('user_type', 'user'),
                'all_permissions': permissions,
                'personnel_permissions': personnel_permissions,
                'can_manage_hr': 'manage_hr' in permissions,
                'can_manage_accounting': 'manage_accounting' in permissions,
                'can_view_personnel': 'view_personnel' in permissions
            }, 200
            
        except Exception as e:
            return {'error': f'Permission test failed: {str(e)}'}, 401