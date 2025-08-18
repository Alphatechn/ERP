# === CONTRÔLEURS POUR LA GESTION DU PERSONNEL ===

from flask import request, jsonify, current_app
from datetime import datetime, date
from .services import (
    PersonnelService, DocumentService, CongeService, 
    AbsenceService, ContratService, PayrollService, RubriqueService
)
from .models import Personnel, Service, Poste, Exercice, Rubrique, Absence, Document
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity


class PersonnelController:
    """Contrôleur pour la gestion du personnel"""
    
    @staticmethod
    def create_personnel():
        """Crée un nouveau personnel"""
        try:
            data = request.get_json()
            
            personnel_data = {
                'matricule': data.get('matricule'),
                'nom': data.get('nom'),
                'prenom': data.get('prenom'),
                'civilite': data.get('civilite'),
                'sexe': data.get('sexe'),
                'telephone': data.get('telephone'),
                'adresse': data.get('adresse'),
                'categorie': data.get('categorie'),
                'date_embauche': datetime.strptime(data.get('date_embauche'), '%Y-%m-%d').date(),
                'service_id': data.get('service_id'),
                'poste_id': data.get('poste_id')
            }
            
            # Options pour création de compte utilisateur
            create_user_account = data.get('create_user_account', False)
            user_data = data.get('user_data') if create_user_account else None
            contrat_data = data.get('contrat_data') if create_user_account else None
            
            result = PersonnelService.create_personnel(
                personnel_data=personnel_data,
                create_user_account=create_user_account,
                user_data=user_data,
                contrat_data=contrat_data
            )
            
            return jsonify({
                'success': True,
                'message': 'Personnel créé avec succès',
                'data': {
                    'id': result['personnel'].id,
                    'matricule': result['personnel'].matricule,
                    'nom_complet': result['personnel'].nom_complet
                }
            }), 201
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_personnel_list():
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
            
            return jsonify({
                'success': True,
                'data': personnels_data,
                'pagination': {
                    'total': result['total'],
                    'pages': result['pages'],
                    'current_page': result['current_page'],
                    'per_page': result['per_page']
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_personnel_details(personnel_id):
        """Récupère les détails d'un personnel"""
        try:
            result = PersonnelService.get_personnel_details(personnel_id)
            
            if not result:
                return jsonify({
                    'success': False,
                    'message': 'Personnel introuvable'
                }), 404
            
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
            
            return jsonify({
                'success': True,
                'data': personnel_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def update_personnel(personnel_id):
        """Met à jour un personnel"""
        try:
            data = request.get_json()
            
            personnel = PersonnelService.update_personnel(personnel_id, data)
            
            return jsonify({
                'success': True,
                'message': 'Personnel mis à jour avec succès',
                'data': {
                    'id': personnel.id,
                    'nom_complet': personnel.nom_complet
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def delete_personnel(personnel_id):
        """Supprime un personnel"""
        try:
            PersonnelService.delete_personnel(personnel_id)
            
            return jsonify({
                'success': True,
                'message': 'Personnel supprimé avec succès'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

class CongeController:
    """Contrôleur pour la gestion des congés"""
    
    @staticmethod
    def create_conge():
        """Crée une demande de congé"""
        try:
            data = request.get_json()
            
            conge = CongeService.create_demande_conge(
                personnel_id=data.get('personnel_id'),
                type_conge=data.get('type_conge'),
                date_debut=datetime.strptime(data.get('date_debut'), '%Y-%m-%d').date(),
                date_fin=datetime.strptime(data.get('date_fin'), '%Y-%m-%d').date()
            )
            
            return jsonify({
                'success': True,
                'message': 'Demande de congé créée avec succès',
                'data': {
                    'id': conge.id,
                    'type_conge': conge.type_conge,
                    'nb_jours': conge.nb_jours,
                    'status': conge.status
                }
            }), 201
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def approve_conge(conge_id):
        """Approuve une demande de congé"""
        try:
            # TODO: Récupérer l'utilisateur connecté
            approved_by_user_id = 1  # Placeholder
            
            conge = CongeService.approve_conge(conge_id, approved_by_user_id)
            
            return jsonify({
                'success': True,
                'message': 'Congé approuvé avec succès',
                'data': {
                    'id': conge.id,
                    'status': conge.status
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def reject_conge(conge_id):
        """Rejette une demande de congé"""
        try:
            # TODO: Récupérer l'utilisateur connecté
            rejected_by_user_id = 1  # Placeholder
            
            conge = CongeService.reject_conge(conge_id, rejected_by_user_id)
            
            return jsonify({
                'success': True,
                'message': 'Congé rejeté avec succès',
                'data': {
                    'id': conge.id,
                    'status': conge.status
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_conges_personnel(personnel_id):
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
            
            return jsonify({
                'success': True,
                'data': conges_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

class PayrollController:
    """Contrôleur pour la gestion de la paie"""
    
    @staticmethod
    def create_exercice():
        """Crée un nouvel exercice"""
        try:
            data = request.get_json()
            
            exercice = PayrollService.create_exercice(data.get('mois_annee'))
            
            return jsonify({
                'success': True,
                'message': 'Exercice créé avec succès',
                'data': {
                    'id': exercice.id,
                    'mois_annee': exercice.mois_annee,
                    'status': exercice.status
                }
            }), 201
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def process_payroll():
        """Traite la paie pour un exercice"""
        try:
            data = request.get_json()
            
            result = PayrollService.process_payroll(
                exercice_id=data.get('exercice_id'),
                personnel_ids=data.get('personnel_ids')
            )
            
            return jsonify({
                'success': True,
                'message': 'Traitement de la paie terminé',
                'data': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_bulletin_paie(personnel_id, exercice_id):
        """Récupère le bulletin de paie"""
        try:
            bulletin = PayrollService.get_bulletin_paie(personnel_id, exercice_id)
            
            if not bulletin:
                return jsonify({
                    'success': False,
                    'message': 'Bulletin de paie introuvable'
                }), 404
            
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
            
            return jsonify({
                'success': True,
                'data': bulletin_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

class ReferentielController:
    """Contrôleur pour les données de référence"""
    
    @staticmethod
    def get_services():
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
            
            return jsonify({
                'success': True,
                'data': services_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_postes():
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
            
            return jsonify({
                'success': True,
                'data': postes_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_exercices():
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
            
            return jsonify({
                'success': True,
                'data': exercices_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_rubriques():
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
            
            return jsonify({
                'success': True,
                'data': rubriques_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

class DocumentController:
    """Contrôleur pour la gestion des documents du personnel"""
    
    @staticmethod
    def upload_document():
        """Upload un document pour un personnel"""
        try:
            verify_jwt_in_request()
            
            personnel_id = request.form.get('personnel_id', type=int)
            libelle = request.form.get('libelle')
            
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'message': 'Aucun fichier fourni'
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'message': 'Nom de fichier vide'
                }), 400
            
            document = DocumentService.upload_document(
                personnel_id=personnel_id,
                file=file,
                libelle=libelle
            )
            
            return jsonify({
                'success': True,
                'message': 'Document uploadé avec succès',
                'data': {
                    'id': document.id,
                    'libelle': document.libelle,
                    'url_fichier': document.url_fichier,
                    'date_creation': document.date_creation.isoformat()
                }
            }), 201
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_personnel_documents(personnel_id):
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
            
            return jsonify({
                'success': True,
                'data': documents_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def delete_document(document_id):
        """Supprime un document"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            # Vérification des permissions
            if 'manage_hr' not in claims.get('permissions', []):
                return jsonify({
                    'success': False,
                    'message': 'Permissions insuffisantes'
                }), 403
            
            DocumentService.delete_document(document_id)
            
            return jsonify({
                'success': True,
                'message': 'Document supprimé avec succès'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

class AbsenceController:
    """Contrôleur pour la gestion des absences"""
    
    @staticmethod
    def create_absence():
        """Enregistre une nouvelle absence"""
        try:
            verify_jwt_in_request()
            data = request.get_json()
            
            absence = AbsenceService.create_absence(
                personnel_id=data.get('personnel_id'),
                libelle=data.get('libelle'),
                date_debut=datetime.strptime(data.get('date_debut'), '%Y-%m-%d').date(),
                date_fin=datetime.strptime(data.get('date_fin'), '%Y-%m-%d').date(),
                motif=data.get('motif'),
                justifiee=data.get('justifiee', False)
            )
            
            return jsonify({
                'success': True,
                'message': 'Absence enregistrée avec succès',
                'data': {
                    'id': absence.id,
                    'libelle': absence.libelle,
                    'nb_jours': absence.nb_jours,
                    'justifiee': absence.justifiee
                }
            }), 201
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_absences_personnel(personnel_id):
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
            
            return jsonify({
                'success': True,
                'data': absences_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_rapport_absences():
        """Génère un rapport d'absences"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            # Vérification des permissions
            if claims.get('user_type') not in ['responsable_rh', 'administrateur']:
                return jsonify({
                    'success': False,
                    'message': 'Accès limité aux responsables RH et administrateurs'
                }), 403
            
            service_id = request.args.get('service_id', type=int)
            mois_annee = request.args.get('mois_annee')  # Format: "2024-01"
            
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
            
            return jsonify({
                'success': True,
                'message': 'Rapport d\'absences généré',
                'data': rapport_data,
                'filters': {
                    'service_id': service_id,
                    'mois_annee': mois_annee
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

class ContratController:
    """Contrôleur pour la gestion des contrats"""
    
    @staticmethod
    def create_contrat():
        """Crée un nouveau contrat"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            # Vérification des permissions
            if 'manage_hr' not in claims.get('permissions', []):
                return jsonify({
                    'success': False,
                    'message': 'Permissions insuffisantes'
                }), 403
            
            data = request.get_json()
            
            contrat = ContratService.create_contrat(
                personnel_id=data.get('personnel_id'),
                type_contrat=data.get('type'),
                date_debut=datetime.strptime(data.get('date_debut'), '%Y-%m-%d').date(),
                salaire_base=float(data.get('salaire_base')),
                date_fin=datetime.strptime(data.get('date_fin'), '%Y-%m-%d').date() if data.get('date_fin') else None
            )
            
            return jsonify({
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
            }), 201
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_contrats_personnel(personnel_id):
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
            
            return jsonify({
                'success': True,
                'data': contrats_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_contrats_expires():
        """Récupère les contrats qui arrivent à expiration"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            # Vérification des permissions
            if claims.get('user_type') not in ['responsable_rh', 'administrateur']:
                return jsonify({
                    'success': False,
                    'message': 'Accès limité aux responsables RH et administrateurs'
                }), 403
            
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
            
            return jsonify({
                'success': True,
                'message': f'{len(contrats_data)} contrats arrivent à expiration',
                'data': contrats_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

class RubriqueController:
    """Contrôleur pour la gestion des rubriques de paie"""
    
    @staticmethod
    def create_rubrique():
        """Crée une nouvelle rubrique de paie"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            # Vérification des permissions
            if claims.get('user_type') not in ['comptable', 'administrateur']:
                return jsonify({
                    'success': False,
                    'message': 'Accès limité aux comptables et administrateurs'
                }), 403
            
            if 'manage_accounting' not in claims.get('permissions', []):
                return jsonify({
                    'success': False,
                    'message': 'Permissions comptables insuffisantes'
                }), 403
            
            data = request.get_json()
            
            rubrique = RubriqueService.create_rubrique(
                libelle=data.get('libelle'),
                type_rubrique=data.get('type'),
                mode_p=data.get('mode_p'),
                valeur=float(data.get('valeur', 0))
            )
            
            return jsonify({
                'success': True,
                'message': 'Rubrique créée avec succès',
                'data': {
                    'id': rubrique.id,
                    'libelle': rubrique.libelle,
                    'type': rubrique.type,
                    'mode_p': rubrique.mode_p,
                    'valeur': rubrique.valeur
                }
            }), 201
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def assign_rubrique_to_poste():
        """Assigne une rubrique à un poste"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            # Vérification des permissions
            if 'manage_accounting' not in claims.get('permissions', []):
                return jsonify({
                    'success': False,
                    'message': 'Permissions comptables insuffisantes'
                }), 403
            
            data = request.get_json()
            
            RubriqueService.assign_rubrique_to_poste(
                poste_id=data.get('poste_id'),
                rubrique_id=data.get('rubrique_id'),
                montant=float(data.get('montant'))
            )
            
            return jsonify({
                'success': True,
                'message': 'Rubrique assignée au poste avec succès'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @staticmethod
    def get_poste_rubriques(poste_id):
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
            
            return jsonify({
                'success': True,
                'data': rubriques_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400