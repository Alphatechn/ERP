# === SERVICES DE GESTION DU PERSONNEL ===

from datetime import datetime, date, timedelta
from core.database import db
from .models import (
    Personnel, Service, Poste, Document, Contrat, Conge, Absence,
    Travailleur, Occuper, Exercice, Rubrique, PosteRubrique, Payer,
    PersonnelManager, PayrollManager
)
from modules.auth.services import ExtendedAuthService
import os
from werkzeug.utils import secure_filename

class PersonnelService:
    """Service principal pour la gestion du personnel"""
    
    @staticmethod
    def create_personnel(personnel_data, create_user_account=False, user_data=None, contrat_data=None):
        """
        Crée un nouveau personnel
        
        Args:
            personnel_data (dict): Données personnelles
            create_user_account (bool): Créer un compte utilisateur
            user_data (dict): Données du compte utilisateur
            contrat_data (dict): Données du contrat
        """
        try:
            # Générer matricule si non fourni
            if not personnel_data.get('matricule'):
                personnel_data['matricule'] = PersonnelManager.generate_matricule(
                    personnel_data['service_id']
                )
            
            # Si création avec compte utilisateur
            if create_user_account and user_data and contrat_data:
                return PersonnelManager.create_personnel_with_user(
                    user_data=user_data,
                    personnel_data=personnel_data,
                    contrat_data=contrat_data
                )
            
            # Sinon création personnel seul
            personnel = Personnel(**personnel_data)
            db.session.add(personnel)
            db.session.commit()
            
            return {'personnel': personnel}
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur création personnel: {str(e)}")
    
    @staticmethod
    def get_personnel_list(filters=None, page=1, per_page=20):
        """
        Récupère la liste du personnel avec filtres
        
        Args:
            filters (dict): Filtres de recherche
            page (int): Numéro de page
            per_page (int): Éléments par page
        """
        query = Personnel.query
        
        # Appliquer les filtres
        if filters:
            if filters.get('service_id'):
                query = query.filter(Personnel.service_id == filters['service_id'])
            
            if filters.get('poste_id'):
                query = query.filter(Personnel.poste_id == filters['poste_id'])
            
            if filters.get('status'):
                query = query.filter(Personnel.status == filters['status'])
            
            if filters.get('categorie'):
                query = query.filter(Personnel.categorie == filters['categorie'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    db.or_(
                        Personnel.nom.ilike(search_term),
                        Personnel.prenom.ilike(search_term),
                        Personnel.matricule.ilike(search_term)
                    )
                )
        
        # Paginer
        pagination = query.paginate(
            page=page, 
            per_page=per_page,
            error_out=False
        )
        
        return {
            'personnels': pagination.items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
    
    @staticmethod
    def get_personnel_details(personnel_id):
        """Récupère les détails complets d'un personnel"""
        return PersonnelManager.get_personnel_with_details(personnel_id)
    
    @staticmethod
    def update_personnel(personnel_id, update_data):
        """Met à jour les informations d'un personnel"""
        try:
            personnel = Personnel.query.get(personnel_id)
            if not personnel:
                raise ValueError("Personnel introuvable")
            
            # Mise à jour des champs autorisés
            allowed_fields = [
                'nom', 'prenom', 'civilite', 'sexe', 'telephone', 'adresse',
                'categorie', 'service_id', 'poste_id', 'status'
            ]
            
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(personnel, field):
                    setattr(personnel, field, value)
            
            db.session.commit()
            return personnel
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur mise à jour personnel: {str(e)}")
    
    @staticmethod
    def delete_personnel(personnel_id):
        """Supprime un personnel (soft delete)"""
        try:
            personnel = Personnel.query.get(personnel_id)
            if not personnel:
                raise ValueError("Personnel introuvable")
            
            # Soft delete
            personnel.status = 'supprime'
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur suppression personnel: {str(e)}")

class DocumentService:
    """Service pour la gestion des documents du personnel"""
    
    @staticmethod
    def upload_document(personnel_id, file, libelle, upload_folder='uploads/documents'):
        """
        Upload un document pour un personnel
        
        Args:
            personnel_id (int): ID du personnel
            file: Fichier uploadé
            libelle (str): Libellé du document
            upload_folder (str): Dossier de destination
        """
        try:
            personnel = Personnel.query.get(personnel_id)
            if not personnel:
                raise ValueError("Personnel introuvable")
            
            # Créer le dossier si nécessaire
            os.makedirs(upload_folder, exist_ok=True)
            
            # Sécuriser le nom du fichier
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{personnel.matricule}_{timestamp}_{filename}"
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # Enregistrer en base
            document = Document(
                personnel_id=personnel_id,
                libelle=libelle,
                url_fichier=file_path
            )
            
            db.session.add(document)
            db.session.commit()
            
            return document
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur upload document: {str(e)}")
    
    @staticmethod
    def get_personnel_documents(personnel_id):
        """Récupère tous les documents d'un personnel"""
        return Document.query.filter_by(personnel_id=personnel_id).all()
    
    @staticmethod
    def delete_document(document_id):
        """Supprime un document"""
        try:
            document = Document.query.get(document_id)
            if not document:
                raise ValueError("Document introuvable")
            
            # Supprimer le fichier physique
            if document.url_fichier and os.path.exists(document.url_fichier):
                os.remove(document.url_fichier)
            
            # Supprimer de la base
            db.session.delete(document)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur suppression document: {str(e)}")

class CongeService:
    """Service pour la gestion des congés"""
    
    @staticmethod
    def create_demande_conge(personnel_id, type_conge, date_debut, date_fin):
        """Crée une demande de congé"""
        try:
            personnel = Personnel.query.get(personnel_id)
            if not personnel:
                raise ValueError("Personnel introuvable")
            
            # Vérifier les chevauchements
            chevauchement = Conge.query.filter(
                Conge.personnel_id == personnel_id,
                Conge.status.in_(['demande', 'approuve']),
                db.or_(
                    db.and_(Conge.date_debut <= date_debut, Conge.date_fin >= date_debut),
                    db.and_(Conge.date_debut <= date_fin, Conge.date_fin >= date_fin),
                    db.and_(Conge.date_debut >= date_debut, Conge.date_fin <= date_fin)
                )
            ).first()
            
            if chevauchement:
                raise ValueError(f"Conflit avec congé existant du {chevauchement.date_debut} au {chevauchement.date_fin}")
            
            # Créer la demande
            conge = Conge(
                personnel_id=personnel_id,
                type_conge=type_conge,
                date_debut=date_debut,
                date_fin=date_fin,
                status='demande'
            )
            
            db.session.add(conge)
            db.session.commit()
            
            return conge
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur demande congé: {str(e)}")
    
    @staticmethod
    def approve_conge(conge_id, approved_by_user_id):
        """Approuve une demande de congé"""
        try:
            conge = Conge.query.get(conge_id)
            if not conge:
                raise ValueError("Congé introuvable")
            
            if conge.status != 'demande':
                raise ValueError("Seules les demandes peuvent être approuvées")
            
            conge.status = 'approuve'
            db.session.commit()
            
            # Log de l'approbation (optionnel)
            print(f"[CONGE_APPROVED] Congé {conge_id} approuvé par user {approved_by_user_id}")
            
            return conge
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur approbation congé: {str(e)}")
    
    @staticmethod
    def reject_conge(conge_id, rejected_by_user_id, motif=None):
        """Rejette une demande de congé"""
        try:
            conge = Conge.query.get(conge_id)
            if not conge:
                raise ValueError("Congé introuvable")
            
            if conge.status != 'demande':
                raise ValueError("Seules les demandes peuvent être rejetées")
            
            conge.status = 'rejete'
            db.session.commit()
            
            print(f"[CONGE_REJECTED] Congé {conge_id} rejeté par user {rejected_by_user_id}")
            
            return conge
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur rejet congé: {str(e)}")
    
    @staticmethod
    def get_conges_personnel(personnel_id, annee=None):
        """Récupère les congés d'un personnel"""
        query = Conge.query.filter_by(personnel_id=personnel_id)
        
        if annee:
            query = query.filter(
                db.extract('year', Conge.date_debut) == annee
            )
        
        return query.order_by(Conge.date_debut.desc()).all()
    
    @staticmethod
    def get_conges_en_attente():
        """Récupère toutes les demandes de congé en attente"""
        return Conge.query.filter_by(status='demande').order_by(Conge.date_debut.asc()).all()

class AbsenceService:
    """Service pour la gestion des absences"""
    
    @staticmethod
    def create_absence(personnel_id, libelle, date_debut, date_fin, motif=None, justifiee=False):
        """Enregistre une absence"""
        try:
            personnel = Personnel.query.get(personnel_id)
            if not personnel:
                raise ValueError("Personnel introuvable")
            
            absence = Absence(
                personnel_id=personnel_id,
                libelle=libelle,
                date_debut=date_debut,
                date_fin=date_fin,
                motif=motif,
                justifiee=justifiee
            )
            
            db.session.add(absence)
            db.session.commit()
            
            return absence
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur création absence: {str(e)}")
    
    @staticmethod
    def get_absences_personnel(personnel_id, periode=None):
        """Récupère les absences d'un personnel"""
        query = Absence.query.filter_by(personnel_id=personnel_id)
        
        if periode:
            # Période format: {'debut': date, 'fin': date}
            query = query.filter(
                Absence.date_debut >= periode['debut'],
                Absence.date_fin <= periode['fin']
            )
        
        return query.order_by(Absence.date_debut.desc()).all()
    
    @staticmethod
    def get_rapport_absences(service_id=None, mois_annee=None):
        """Génère un rapport d'absences"""
        query = db.session.query(
            Personnel.matricule,
            Personnel.nom,
            Personnel.prenom,
            Service.libelle.label('service'),
            db.func.count(Absence.id).label('nb_absences'),
            db.func.sum(
                db.func.julianday(Absence.date_fin) - 
                db.func.julianday(Absence.date_debut) + 1
            ).label('total_jours')
        ).join(Personnel).join(Service).join(Absence)
        
        if service_id:
            query = query.filter(Personnel.service_id == service_id)
        
        if mois_annee:  # Format: "2024-01"
            year, month = mois_annee.split('-')
            query = query.filter(
                db.extract('year', Absence.date_debut) == int(year),
                db.extract('month', Absence.date_debut) == int(month)
            )
        
        return query.group_by(Personnel.id).all()

class ContratService:
    """Service pour la gestion des contrats"""
    
    @staticmethod
    def create_contrat(personnel_id, type_contrat, date_debut, salaire_base, date_fin=None):
        """Crée un nouveau contrat"""
        try:
            personnel = Personnel.query.get(personnel_id)
            if not personnel:
                raise ValueError("Personnel introuvable")
            
            # Terminer les contrats actifs précédents
            ContratService.terminate_active_contracts(personnel_id, date_debut)
            
            contrat = Contrat(
                personnel_id=personnel_id,
                type=type_contrat,
                date_debut=date_debut,
                date_fin=date_fin,
                salaire_base=salaire_base
            )
            
            db.session.add(contrat)
            db.session.commit()
            
            return contrat
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur création contrat: {str(e)}")
    
    @staticmethod
    def terminate_active_contracts(personnel_id, date_fin):
        """Termine les contrats actifs d'un personnel"""
        active_contracts = Contrat.query.filter_by(
            personnel_id=personnel_id,
            status='actif'
        ).all()
        
        for contrat in active_contracts:
            contrat.status = 'termine'
            if not contrat.date_fin or contrat.date_fin > date_fin:
                contrat.date_fin = date_fin
        
        db.session.commit()
    
    @staticmethod
    def get_contrats_personnel(personnel_id):
        """Récupère tous les contrats d'un personnel"""
        return Contrat.query.filter_by(personnel_id=personnel_id).order_by(Contrat.date_debut.desc()).all()
    
    @staticmethod
    def get_contrats_expires():
        """Récupère les contrats qui arrivent à expiration"""
        seuil_alerte = date.today() + timedelta(days=30)  # Alerte 30 jours avant
        
        return Contrat.query.filter(
            Contrat.status == 'actif',
            Contrat.date_fin.isnot(None),
            Contrat.date_fin <= seuil_alerte
        ).order_by(Contrat.date_fin.asc()).all()

# === SERVICES POUR LA PAIE ===

class PayrollService:
    """Service principal pour la gestion de la paie"""
    
    @staticmethod
    def create_exercice(mois_annee):
        """Crée un nouvel exercice comptable"""
        try:
            # Vérifier si l'exercice existe déjà
            existing = Exercice.query.filter_by(mois_annee=mois_annee).first()
            if existing:
                raise ValueError(f"L'exercice {mois_annee} existe déjà")
            
            exercice = Exercice(mois_annee=mois_annee)
            db.session.add(exercice)
            db.session.commit()
            
            return exercice
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur création exercice: {str(e)}")
    
    @staticmethod
    def process_payroll(exercice_id, personnel_ids=None):
        """
        Traite la paie pour un exercice - VERSION CORRIGÉE
        Args:
            exercice_id (int): ID de l'exercice
            personnel_ids (list): IDs du personnel à traiter (None = tous)
        """
        try:
            # Vérifications initiales
            exercice = Exercice.query.get(exercice_id)
            if not exercice:
                raise ValueError("Exercice introuvable")
            if exercice.status == 'clos':
                raise ValueError("Impossible de traiter un exercice clos")
            
            print(f"[PAYROLL_START] Début traitement paie pour exercice {exercice.mois_annee}")
            
            # Récupérer le personnel à traiter
            query = Personnel.query.filter_by(status='actif')
            if personnel_ids:
                query = query.filter(Personnel.id.in_(personnel_ids))
            
            personnels = query.all()
            
            if not personnels:
                raise ValueError("Aucun personnel actif trouvé à traiter")
            
            print(f"[PAYROLL_INFO] {len(personnels)} personnel(s) à traiter")
            
            results = {
                'success': [],
                'errors': [],
                'total_processed': 0,
                'total_amount': 0,
                'exercice': exercice.mois_annee
            }
            
            for personnel in personnels:
                try:
                    print(f"[PAYROLL_PROCESSING] Traitement de {personnel.nom_complet}")
                    
                    # Vérifier si pas déjà traité
                    existing_paie = Payer.query.filter_by(
                        personnel_id=personnel.id,
                        exercice_id=exercice_id
                    ).first()
                    
                    if existing_paie:
                        results['errors'].append({
                            'personnel': personnel.nom_complet,
                            'error': 'Déjà traité pour cet exercice'
                        })
                        print(f"[PAYROLL_SKIP] {personnel.nom_complet} déjà traité")
                        continue
                    
                    # Vérifier qu'il a un contrat actuel
                    contrat = personnel.get_contrat_actuel()
                    if not contrat:
                        results['errors'].append({
                            'personnel': personnel.nom_complet,
                            'error': 'Aucun contrat actif'
                        })
                        print(f"[PAYROLL_ERROR] {personnel.nom_complet} n'a pas de contrat actif")
                        continue
                    
                    # Générer le bulletin
                    bulletin = PayrollManager.generate_payslip(personnel.id, exercice_id)
                    
                    if bulletin:
                        results['success'].append({
                            'personnel': personnel.nom_complet,
                            'matricule': personnel.matricule,
                            'net_payer': bulletin['net_payer'],
                            'total_gains': bulletin['total_gains'],
                            'total_retenues': bulletin['total_retenues']
                        })
                        results['total_amount'] += bulletin['net_payer']
                        results['total_processed'] += 1
                        
                        print(f"[PAYROLL_SUCCESS] {personnel.nom_complet} traité avec succès - Net: {bulletin['net_payer']}")
                    else:
                        results['errors'].append({
                            'personnel': personnel.nom_complet,
                            'error': 'Échec génération bulletin'
                        })
                        
                except Exception as e:
                    error_msg = str(e)
                    results['errors'].append({
                        'personnel': personnel.nom_complet,
                        'error': error_msg
                    })
                    print(f"[PAYROLL_ERROR] Erreur pour {personnel.nom_complet}: {error_msg}")
                    continue
            
            print(f"[PAYROLL_COMPLETE] Traitement terminé - {results['total_processed']} succès, {len(results['errors'])} erreurs")
            
            return results
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Erreur traitement paie: {str(e)}"
            print(f"[PAYROLL_FATAL] {error_msg}")
            raise Exception(error_msg)

    @staticmethod
    def get_bulletin_paie(personnel_id, exercice_id):
        """Récupère le bulletin de paie d'un personnel pour un exercice"""
        paies = Payer.query.filter_by(
            personnel_id=personnel_id,
            exercice_id=exercice_id
        ).all()
        
        if not paies:
            return None
        
        personnel = Personnel.query.get(personnel_id)
        exercice = Exercice.query.get(exercice_id)
        
        bulletin = {
            'personnel': personnel,
            'exercice': exercice,
            'lignes': [],
            'total_gains': 0,
            'total_retenues': 0,
            'net_payer': 0
        }
        
        for paie in paies:
            ligne = {
                'rubrique': paie.rubrique_ref,
                'montant': paie.montant,
                'date_paiement': paie.date_p
            }
            
            if paie.rubrique_ref.type == 'gain':
                bulletin['total_gains'] += paie.montant
            elif paie.rubrique_ref.type == 'retenue':
                bulletin['total_retenues'] += paie.montant
            
            bulletin['lignes'].append(ligne)
        
        bulletin['net_payer'] = bulletin['total_gains'] - bulletin['total_retenues']
        
        return bulletin
    
    @staticmethod
    def close_exercice(exercice_id, closed_by_user_id):
        """Clôture un exercice comptable"""
        try:
            exercice = Exercice.query.get(exercice_id)
            if not exercice:
                raise ValueError("Exercice introuvable")
            
            if exercice.status == 'clos':
                raise ValueError("Exercice déjà clôturé")
            
            # Vérifications avant clôture
            nb_personnel_actif = Personnel.query.filter_by(status='actif').count()
            nb_paies_traitees = db.session.query(Payer.personnel_id).filter_by(
                exercice_id=exercice_id
            ).distinct().count()
            
            if nb_paies_traitees < nb_personnel_actif:
                raise ValueError(f"Paie incomplète: {nb_paies_traitees}/{nb_personnel_actif} personnels traités")
            
            exercice.status = 'clos'
            db.session.commit()
            
            print(f"[EXERCICE_CLOSED] Exercice {exercice.mois_annee} clôturé par user {closed_by_user_id}")
            
            return exercice
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur clôture exercice: {str(e)}")
    
    @staticmethod
    def get_rapport_paie(exercice_id, service_id=None):
        """
        Génère un rapport de paie pour un exercice
        Args:
            exercice_id (int): ID de l'exercice
            service_id (int, optional): Filtrer par service
        """
        try:
            # Vérifier que l'exercice existe
            exercice = Exercice.query.get(exercice_id)
            if not exercice:
                raise ValueError(f"Exercice avec ID {exercice_id} introuvable")
            
            # Récupérer tous les paiements pour cet exercice
            query = db.session.query(Payer).filter_by(exercice_id=exercice_id)
            
            # Filtrer par service si demandé
            if service_id:
                query = query.join(Personnel).filter(Personnel.service_id == service_id)
            
            paiements = query.all()
            
            if not paiements:
                return {
                    'exercice': exercice,
                    'personnel_data': [],
                    'totaux': {
                        'total_gains': 0, 
                        'total_retenues': 0, 
                        'net_total': 0, 
                        'nb_personnel': 0
                    }
                }
            
            # Grouper par personnel
            personnel_data = {}
            
            for paiement in paiements:
                personnel = paiement.personnel_ref
                rubrique = paiement.rubrique_ref
                
                # Filtrer par service au niveau Python si nécessaire
                if service_id and personnel.service_id != service_id:
                    continue
                
                if personnel.id not in personnel_data:
                    personnel_data[personnel.id] = {
                        'personnel_id': personnel.id,
                        'matricule': personnel.matricule,
                        'nom_complet': personnel.nom_complet,
                        'service': personnel.service_ref.libelle,
                        'poste': personnel.poste_ref.fonction,
                        'total_gains': 0,
                        'total_retenues': 0,
                        'rubriques_detail': []
                    }
                
                # Ajouter le détail de la rubrique
                personnel_data[personnel.id]['rubriques_detail'].append({
                    'rubrique': rubrique.libelle,
                    'type': rubrique.type,
                    'montant': float(paiement.montant)
                })
                
                # Totaliser
                if rubrique.type == 'gain':
                    personnel_data[personnel.id]['total_gains'] += paiement.montant
                elif rubrique.type == 'retenue':
                    personnel_data[personnel.id]['total_retenues'] += paiement.montant
            
            # Calculer les nets à payer et les totaux globaux
            report_data = []
            total_gains_global = 0
            total_retenues_global = 0
            
            for data in personnel_data.values():
                net_payer = data['total_gains'] - data['total_retenues']
                data['net_payer'] = float(net_payer)
                data['total_gains'] = float(data['total_gains'])
                data['total_retenues'] = float(data['total_retenues'])
                
                report_data.append(data)
                total_gains_global += data['total_gains']
                total_retenues_global += data['total_retenues']
            
            # Trier par nom
            report_data.sort(key=lambda x: x['nom_complet'])
            
            # Ajouter des informations sur le service si filtrage appliqué
            service_info = None
            if service_id:
                service = Service.query.get(service_id)
                service_info = {
                    'id': service.id,
                    'libelle': service.libelle
                } if service else None
            
            return {
                'exercice': exercice,
                'personnel_data': report_data,
                'totaux': {
                    'total_gains': float(total_gains_global),
                    'total_retenues': float(total_retenues_global),
                    'net_total': float(total_gains_global - total_retenues_global),
                    'nb_personnel': len(report_data)
                },
                'service_filter': service_info
            }
            
        except Exception as e:
            print(f"[PAYROLL_SERVICE_ERROR] get_rapport_paie: {str(e)}")
            raise Exception(f"Erreur génération rapport de paie: {str(e)}")

class RubriqueService:
    """Service pour la gestion des rubriques de paie"""
    
    @staticmethod
    def create_rubrique(libelle, type_rubrique, mode_p=None, valeur=0):
        """Crée une nouvelle rubrique de paie"""
        try:
            if type_rubrique not in ['gain', 'retenue', 'information']:
                raise ValueError("Type de rubrique invalide")
            
            rubrique = Rubrique(
                libelle=libelle,
                type=type_rubrique,
                mode_p=mode_p,
                valeur=valeur
            )
            
            db.session.add(rubrique)
            db.session.commit()
            
            return rubrique
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur création rubrique: {str(e)}")
    
    @staticmethod
    def assign_rubrique_to_poste(poste_id, rubrique_id, montant):
        """Assigne une rubrique à un poste avec un montant"""
        try:
            # Vérifier si l'association existe déjà
            existing = PosteRubrique.query.filter_by(
                poste_id=poste_id,
                rubrique_id=rubrique_id,
                status='actif'
            ).first()
            
            if existing:
                # Mettre à jour le montant
                existing.montant = montant
                existing.date_modification = date.today()
            else:
                # Créer nouvelle association
                poste_rubrique = PosteRubrique(
                    poste_id=poste_id,
                    rubrique_id=rubrique_id,
                    montant=montant
                )
                db.session.add(poste_rubrique)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur assignation rubrique: {str(e)}")
    
    @staticmethod
    def get_rubriques_by_type(type_rubrique):
        """Récupère les rubriques par type"""
        return Rubrique.query.filter_by(type=type_rubrique, status='actif').all()
    
    @staticmethod
    def get_poste_rubriques(poste_id):
        """Récupère les rubriques d'un poste"""
        return PosteRubrique.query.filter_by(poste_id=poste_id, status='actif').all()

# === SERVICE D'INITIALISATION ===

class PersonnelInitService:
    """Service d'initialisation du module personnel"""
    
    @staticmethod
    def init_personnel_system():
        """Initialise le système de gestion du personnel avec données de test"""
        print("\n=== Initialisation du système Personnel ===")
        
        try:
            # 1. Créer les services
            services_data = [
                ('Direction Générale', 'actif'),
                ('Ressources Humaines', 'actif'),
                ('Comptabilité', 'actif'),
                ('Informatique', 'actif'),
                ('Commercial', 'actif'),
                ('Production', 'actif')
            ]
            
            for libelle, status in services_data:
                if not Service.query.filter_by(libelle=libelle).first():
                    service = Service(libelle=libelle, status=status)
                    db.session.add(service)
                    print(f"[+] Service créé: {libelle}")
            
            # 2. Créer les postes
            postes_data = [
                ('Directeur Général', 45.0),
                ('Responsable RH', 40.0),
                ('Assistant RH', 40.0),
                ('Comptable', 40.0),
                ('Développeur Senior', 40.0),
                ('Développeur Junior', 40.0),
                ('Commercial Senior', 40.0),
                ('Secrétaire', 35.0),
                ('Ouvrier Spécialisé', 40.0),
                ('Agent de Sécurité', 40.0)
            ]
            
            for fonction, t_horaire in postes_data:
                if not Poste.query.filter_by(fonction=fonction).first():
                    poste = Poste(fonction=fonction, t_horaire=t_horaire)
                    db.session.add(poste)
                    print(f"[+] Poste créé: {fonction}")
            
            # 3. Créer les rubriques de base
            rubriques_data = [
                ('Salaire de Base', 'gain', 'fixe', 0),
                ('Prime d\'Ancienneté', 'gain', 'variable', 0),
                ('Prime de Rendement', 'gain', 'variable', 0),
                ('Heures Supplémentaires', 'gain', 'variable', 0),
                ('CNPS Employé', 'retenue', '%', 4.2),
                ('IRPP', 'retenue', '%', 15.0),
                ('Avance sur Salaire', 'retenue', 'variable', 0),
                ('Cotisation Syndicale', 'retenue', 'fixe', 5000),
                ('Nombre d\'Enfants', 'information', 'fixe', 0),
                ('Jours Travaillés', 'information', 'variable', 0)
            ]
            
            for libelle, type_rub, mode_p, valeur in rubriques_data:
                if not Rubrique.query.filter_by(libelle=libelle).first():
                    rubrique = Rubrique(
                        libelle=libelle,
                        type=type_rub,
                        mode_p=mode_p,
                        valeur=valeur
                    )
                    db.session.add(rubrique)
                    print(f"[+] Rubrique créée: {libelle}")
            
            db.session.commit()
            print("=== Initialisation Personnel terminée ===\n")
            
            return True
            
        except Exception as e: 
            db.session.rollback()
            print(f"[ERROR] Erreur initialisation: {str(e)}")
            return False