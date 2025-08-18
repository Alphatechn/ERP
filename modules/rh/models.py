# === MODÈLES POUR LA GESTION DU PERSONNEL ET PAIE ===

from datetime import datetime, date
from core.database import db
from ..auth.models import User  # Lien avec notre système d'auth étendu

class Service(db.Model):
    """Les différents services/départements de l'entreprise"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='actif')  # actif, inactif
    
    # Relations
    personnels = db.relationship('Personnel', backref='service_ref', lazy=True)
    
    def __repr__(self):
        return f'<Service {self.libelle}>'

class Poste(db.Model):
    """Les postes/fonctions dans l'entreprise"""
    __tablename__ = 'postes'
    
    id = db.Column(db.Integer, primary_key=True)
    fonction = db.Column(db.String(100), nullable=False)
    t_horaire = db.Column(db.Float, default=40.0)  # Temps de travail hebdomadaire
    status = db.Column(db.String(20), default='actif')
    
    # Relations
    personnels = db.relationship('Personnel', backref='poste_ref', lazy=True)
    rubriques = db.relationship('PosteRubrique', backref='poste_ref', lazy=True)
    
    def __repr__(self):
        return f'<Poste {self.fonction}>'

class Personnel(db.Model):
    """Table principale du personnel - étend User"""
    __tablename__ = 'personnels'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Référence vers le système d'auth (optionnel si le personnel n'a pas de compte)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Informations personnelles
    matricule = db.Column(db.String(20), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    civilite = db.Column(db.String(10))  # M., Mme, Mlle
    sexe = db.Column(db.String(1))  # M, F
    telephone = db.Column(db.String(20))
    adresse = db.Column(db.Text)
    categorie = db.Column(db.String(50))  # Cadre, Employé, Ouvrier, etc.
    date_embauche = db.Column(db.Date, nullable=False)
    photo = db.Column(db.String(255))  # Chemin vers la photo
    status = db.Column(db.String(20), default='actif')  # actif, congé, suspendu, démissionné
    
    # Relations professionnelles
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    poste_id = db.Column(db.Integer, db.ForeignKey('postes.id'), nullable=False)
    
    # Relations
    user = db.relationship('User', backref='personnel_info')
    documents = db.relationship('Document', backref='personnel_ref', lazy=True)
    conges = db.relationship('Conge', backref='personnel_ref', lazy=True)
    absences = db.relationship('Absence', backref='personnel_ref', lazy=True)
    contrats = db.relationship('Contrat', backref='personnel_ref', lazy=True)
    
    def __repr__(self):
        return f'<Personnel {self.matricule} - {self.nom} {self.prenom}>'
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}"
    
    def get_contrat_actuel(self):
        """Retourne le contrat actuel du personnel"""
        return Contrat.query.filter_by(
            personnel_id=self.id, 
            status='actif'
        ).first()
    
    def get_salaire_base(self):
        """Retourne le salaire de base du contrat actuel"""
        contrat = self.get_contrat_actuel()
        return contrat.salaire_base if contrat else 0

class Document(db.Model):
    """Documents associés au personnel"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(200), nullable=False)
    url_fichier = db.Column(db.String(500))  # Chemin vers le fichier
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id'), nullable=False)
    
    def __repr__(self):
        return f'<Document {self.libelle}>'

class Contrat(db.Model):
    """Contrats de travail"""
    __tablename__ = 'contrats'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # CDI, CDD, Stage, Consultant
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=True)  # NULL pour CDI
    url_fichier = db.Column(db.String(500))  # Fichier PDF du contrat
    salaire_base = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='actif')  # actif, terminé, suspendu
    
    # Relations
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id'), nullable=False)
    
    def __repr__(self):
        return f'<Contrat {self.type} - {self.personnel_ref.nom_complet}>'
    
    @property
    def is_cdi(self):
        return self.type.upper() == 'CDI'
    
    @property
    def is_active(self):
        if self.status != 'actif':
            return False
        if self.date_fin and self.date_fin < date.today():
            return False
        return True

class Conge(db.Model):
    """Gestion des congés"""
    __tablename__ = 'conges'
    
    id = db.Column(db.Integer, primary_key=True)
    type_conge = db.Column(db.String(50), nullable=False)  # Annuel, Maladie, Maternité, etc.
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='demande')  # demande, approuvé, rejeté, pris
    
    # Relations
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id'), nullable=False)
    
    @property
    def nb_jours(self):
        return (self.date_fin - self.date_debut).days + 1
    
    def __repr__(self):
        return f'<Congé {self.type_conge} - {self.personnel_ref.nom_complet}>'

class Absence(db.Model):
    """Gestion des absences"""
    __tablename__ = 'absences'
    
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(200), nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    motif = db.Column(db.Text)
    justifiee = db.Column(db.Boolean, default=False)
    
    # Relations
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id'), nullable=False)
    
    @property
    def nb_jours(self):
        return (self.date_fin - self.date_debut).days + 1
    
    def __repr__(self):
        return f'<Absence {self.libelle} - {self.personnel_ref.nom_complet}>'

class Travailleur(db.Model):
    """État de travail du personnel (actif/inactif)"""
    __tablename__ = 'travailleurs'
    
    id = db.Column(db.Integer, primary_key=True)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='actif')  # actif, inactif
    
    # Relations
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id'), nullable=False)
    personnel_ref = db.relationship('Personnel', backref='periodes_travail')
    
    def __repr__(self):
        return f'<Travailleur {self.personnel_ref.nom_complet} - {self.status}>'

class Occuper(db.Model):
    """Association Personnel-Poste avec période"""
    __tablename__ = 'occuper'
    
    id = db.Column(db.Integer, primary_key=True)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='actif')
    
    # Relations
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id'), nullable=False)
    poste_id = db.Column(db.Integer, db.ForeignKey('postes.id'), nullable=False)
    
    # Relations explicites
    personnel_ref = db.relationship('Personnel', backref='occupations')
    poste_ref = db.relationship('Poste', backref='occupants')
    
    def __repr__(self):
        return f'<Occupation {self.personnel_ref.nom_complet} -> {self.poste_ref.fonction}>'

class Exercice(db.Model):
    """Exercices comptables/fiscaux"""
    __tablename__ = 'exercices'
    
    id = db.Column(db.Integer, primary_key=True)
    mois_annee = db.Column(db.String(7), nullable=False)  # Format: "2024-01"
    status = db.Column(db.String(20), default='ouvert')  # ouvert, clos
    
    # Relations
    paies = db.relationship('Payer', backref='exercice_ref', lazy=True)
    
    def __repr__(self):
        return f'<Exercice {self.mois_annee}>'
    
    @property
    def annee(self):
        return int(self.mois_annee.split('-')[0])
    
    @property
    def mois(self):
        return int(self.mois_annee.split('-')[1])

# === SYSTÈME DE PAIE ===

class Rubrique(db.Model):
    """Rubriques de paie (salaire, primes, déductions, etc.)"""
    __tablename__ = 'rubriques'
    
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(30), nullable=False)  # gain, retenue, information
    mode_p = db.Column(db.String(20))  # Mode de paiement: fixe, variable, %
    valeur = db.Column(db.Float, default=0)  # Valeur par défaut
    status = db.Column(db.String(20), default='actif')
    
    # Relations
    postes_rubriques = db.relationship('PosteRubrique', backref='rubrique_ref', lazy=True)
    paies = db.relationship('Payer', backref='rubrique_ref', lazy=True)
    
    def __repr__(self):
        return f'<Rubrique {self.libelle} ({self.type})>'

class PosteRubrique(db.Model):
    """Association Poste-Rubrique avec montants spécifiques"""
    __tablename__ = 'poste_rubriques'
    
    id = db.Column(db.Integer, primary_key=True)
    montant = db.Column(db.Float, nullable=False)
    date_definition = db.Column(db.Date, default=date.today)
    date_modification = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='actif')
    
    # Relations
    poste_id = db.Column(db.Integer, db.ForeignKey('postes.id'), nullable=False)
    rubrique_id = db.Column(db.Integer, db.ForeignKey('rubriques.id'), nullable=False)
    
    def __repr__(self):
        return f'<PosteRubrique {self.poste_ref.fonction} -> {self.rubrique_ref.libelle}: {self.montant}>'

class Payer(db.Model):
    """Enregistrements de paie (bulletins de salaire)"""
    __tablename__ = 'payer'
    
    id = db.Column(db.Integer, primary_key=True)
    montant = db.Column(db.Float, nullable=False)
    date_p = db.Column(db.Date, default=date.today)  # Date de paiement
    
    # Relations
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id'), nullable=False)
    exercice_id = db.Column(db.Integer, db.ForeignKey('exercices.id'), nullable=False)
    rubrique_id = db.Column(db.Integer, db.ForeignKey('rubriques.id'), nullable=False)
    
    # Relations explicites
    personnel_ref = db.relationship('Personnel', backref='paies')
    
    def __repr__(self):
        return f'<Paie {self.personnel_ref.nom_complet} - {self.exercice_ref.mois_annee}: {self.montant}>'

# === CLASSES HELPER POUR LA GESTION MÉTIER ===

class PersonnelManager:
    """Gestionnaire métier pour le personnel"""
    
    @staticmethod
    def create_personnel_with_user(user_data, personnel_data, contrat_data):
        """
        Crée un personnel avec compte utilisateur et contrat
        
        Args:
            user_data: Données pour créer le compte utilisateur
            personnel_data: Données personnelles
            contrat_data: Données du contrat
        """
        from ..auth.services import ExtendedAuthService
        
        try:
            # 1. Créer le compte utilisateur si nécessaire
            user = None
            if user_data:
                user = ExtendedAuthService.register_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    role_name=user_data.get('role', 'user'),
                    user_type=user_data.get('user_type', 'user')
                )
            
            # 2. Créer le personnel
            personnel = Personnel(
                user_id=user.id if user else None,
                matricule=personnel_data['matricule'],
                nom=personnel_data['nom'],
                prenom=personnel_data['prenom'],
                civilite=personnel_data.get('civilite'),
                sexe=personnel_data.get('sexe'),
                telephone=personnel_data.get('telephone'),
                adresse=personnel_data.get('adresse'),
                categorie=personnel_data.get('categorie'),
                date_embauche=personnel_data['date_embauche'],
                service_id=personnel_data['service_id'],
                poste_id=personnel_data['poste_id']
            )
            
            db.session.add(personnel)
            db.session.flush()  # Pour avoir l'ID du personnel
            
            # 3. Créer le contrat
            contrat = Contrat(
                personnel_id=personnel.id,
                type=contrat_data['type'],
                date_debut=contrat_data['date_debut'],
                date_fin=contrat_data.get('date_fin'),
                salaire_base=contrat_data['salaire_base']
            )
            
            db.session.add(contrat)
            
            # 4. Créer l'occupation du poste
            occupation = Occuper(
                personnel_id=personnel.id,
                poste_id=personnel_data['poste_id'],
                date_debut=personnel_data['date_embauche']
            )
            
            db.session.add(occupation)
            
            # 5. Créer le statut travailleur
            travailleur = Travailleur(
                personnel_id=personnel.id,
                date_debut=personnel_data['date_embauche']
            )
            
            db.session.add(travailleur)
            
            db.session.commit()
            
            print(f"[PERSONNEL_CREATED] {personnel.nom_complet} créé avec succès")
            
            return {
                'personnel': personnel,
                'user': user,
                'contrat': contrat
            }
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erreur création personnel: {str(e)}")
    
    @staticmethod
    def get_personnel_with_details(personnel_id):
        """Récupère un personnel avec tous ses détails"""
        personnel = Personnel.query.get(personnel_id)
        if not personnel:
            return None
        
        return {
            'personnel': personnel,
            'contrat_actuel': personnel.get_contrat_actuel(),
            'service': personnel.service_ref,
            'poste': personnel.poste_ref,
            'user': personnel.user,
            'nb_conges_pris': len([c for c in personnel.conges if c.status == 'pris']),
            'nb_absences': len(personnel.absences)
        }
    
    @staticmethod
    def generate_matricule(service_id, annee=None):
        """Génère un matricule automatique"""
        if not annee:
            annee = datetime.now().year
        
        # Compter les personnels du service pour cette année
        count = Personnel.query.join(Service).filter(
            Personnel.service_id == service_id,
            db.extract('year', Personnel.date_embauche) == annee
        ).count()
        
        service = Service.query.get(service_id)
        service_code = service.libelle[:3].upper() if service else "GEN"
        
        return f"{service_code}{annee}{str(count + 1).zfill(3)}"

class PayrollManager:
    """Gestionnaire de paie"""
    
    @staticmethod
    def calculate_salary(personnel_id, exercice_id):
        """Calcule le salaire complet pour un personnel et un exercice"""
        personnel = Personnel.query.get(personnel_id)
        exercice = Exercice.query.get(exercice_id)
        
        if not personnel or not exercice:
            return None
        
        # Récupérer les rubriques applicables au poste
        poste_rubriques = PosteRubrique.query.filter_by(
            poste_id=personnel.poste_id,
            status='actif'
        ).all()
        
        # Si aucune rubrique configurée pour ce poste, utiliser le salaire de base
        if not poste_rubriques:
            contrat = personnel.get_contrat_actuel()
            if not contrat:
                return None
            
            # Créer une rubrique de base avec le salaire
            calculation = {
                'personnel': personnel,
                'exercice': exercice,
                'rubriques': [{
                    'rubrique': {
                        'id': None,  # Rubrique virtuelle
                        'libelle': 'Salaire de base',
                        'type': 'gain'
                    },
                    'montant_base': contrat.salaire_base,
                    'montant_calcule': contrat.salaire_base
                }],
                'total_gains': contrat.salaire_base,
                'total_retenues': 0,
                'net_payer': contrat.salaire_base
            }
            return calculation
        
        calculation = {
            'personnel': personnel,
            'exercice': exercice,
            'rubriques': [],
            'total_gains': 0,
            'total_retenues': 0,
            'net_payer': 0
        }
        
        for pr in poste_rubriques:
            rubrique_calc = {
                'rubrique': pr.rubrique_ref,
                'montant_base': pr.montant,
                'montant_calcule': pr.montant  # Simplifié, peut être plus complexe
            }
            
            if pr.rubrique_ref.type == 'gain':
                calculation['total_gains'] += pr.montant
            elif pr.rubrique_ref.type == 'retenue':
                calculation['total_retenues'] += pr.montant
            
            calculation['rubriques'].append(rubrique_calc)
        
        calculation['net_payer'] = calculation['total_gains'] - calculation['total_retenues']
        
        return calculation
    
    @staticmethod
    def generate_payslip(personnel_id, exercice_id):
        """Génère un bulletin de paie"""
        try:
            calculation = PayrollManager.calculate_salary(personnel_id, exercice_id)
            
            if not calculation:
                raise Exception("Impossible de calculer le salaire")
            
            # Vérifier que le personnel et l'exercice existent
            personnel = Personnel.query.get(personnel_id)
            exercice = Exercice.query.get(exercice_id)
            
            if not personnel:
                raise Exception(f"Personnel avec ID {personnel_id} introuvable")
            if not exercice:
                raise Exception(f"Exercice avec ID {exercice_id} introuvable")
            
            # Enregistrer les lignes de paie
            paies_created = []
            
            for rubrique_calc in calculation['rubriques']:
                rubrique = rubrique_calc['rubrique']
                
                # Si c'est une rubrique virtuelle (salaire de base), créer ou récupérer la rubrique
                if isinstance(rubrique, dict) and rubrique.get('id') is None:
                    # Chercher ou créer la rubrique "Salaire de base"
                    rubrique_obj = Rubrique.query.filter_by(
                        libelle='Salaire de base',
                        type='gain'
                    ).first()
                    
                    if not rubrique_obj:
                        rubrique_obj = Rubrique(
                            libelle='Salaire de base',
                            type='gain',
                            mode_p='fixe',
                            status='actif'
                        )
                        db.session.add(rubrique_obj)
                        db.session.flush()  # Pour avoir l'ID
                    
                    rubrique_id = rubrique_obj.id
                else:
                    rubrique_id = rubrique.id
                
                # Créer l'enregistrement de paie
                paie = Payer(
                    personnel_id=personnel_id,
                    exercice_id=exercice_id,
                    rubrique_id=rubrique_id,
                    montant=rubrique_calc['montant_calcule']
                )
                
                db.session.add(paie)
                paies_created.append(paie)
            
            # Sauvegarder en base
            db.session.commit()
            
            print(f"[PAYROLL_GENERATED] Bulletin créé pour {personnel.nom_complet} - Exercice {exercice.mois_annee}")
            print(f"[PAYROLL_DETAILS] {len(paies_created)} lignes de paie créées, Net à payer: {calculation['net_payer']}")
            
            return calculation
            
        except Exception as e:
            db.session.rollback()
            print(f"[PAYROLL_ERROR] Erreur génération bulletin: {str(e)}")
            raise Exception(f"Erreur génération bulletin de paie: {str(e)}")
    
    @staticmethod
    def get_payslip_data(personnel_id, exercice_id):
        """Récupère les données d'un bulletin de paie existant"""
        paies = Payer.query.filter_by(
            personnel_id=personnel_id,
            exercice_id=exercice_id
        ).all()
        
        if not paies:
            return None
        
        personnel = Personnel.query.get(personnel_id)
        exercice = Exercice.query.get(exercice_id)
        
        total_gains = 0
        total_retenues = 0
        rubriques = []
        
        for paie in paies:
            if paie.rubrique_ref.type == 'gain':
                total_gains += paie.montant
            elif paie.rubrique_ref.type == 'retenue':
                total_retenues += paie.montant
            
            rubriques.append({
                'rubrique': paie.rubrique_ref,
                'montant': paie.montant
            })
        
        return {
            'personnel': personnel,
            'exercice': exercice,
            'rubriques': rubriques,
            'total_gains': total_gains,
            'total_retenues': total_retenues,
            'net_payer': total_gains - total_retenues
        }