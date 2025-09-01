from flask import Blueprint
from flask_restful import Api
from flasgger import swag_from
from .resources import (
    PersonnelResource, PersonnelDetailResource, CongeResource, CongeApproveResource,
    CongeRejectResource, PersonnelCongesResource, PayrollExerciceResource,
    PayrollProcessResource, BulletinPaieResource, ReferentielServicesResource,
    ReferentielPostesResource, ReferentielExercicesResource, ReferentielRubriquesResource,
    DocumentResource, DocumentDeleteResource, AbsenceResource, PersonnelAbsencesResource,
    RapportAbsencesResource, ContratResource, PersonnelContratsResource,
    ContratsExpiresResource, RubriqueResource, AssignRubriqueResource,
    PosteRubriquesResource, HRDashboardResource, AccountingDashboardResource,
    HealthResource, TestPermissionsResource
)

# Configuration Swagger pour le module RH
swagger_config = {
    "swagger": "2.0",
    "info": {
        "title": "API Gestion du Personnel et Paie",
        "description": """
API complète pour la gestion des ressources humaines et de la paie.

## Fonctionnalités principales :
- **Gestion du personnel** : CRUD, fiches personnels, matricules
- **Gestion des congés** : Demandes, approbations, rejets
- **Gestion des absences** : Enregistrement et suivi  
- **Gestion des contrats** : CDI/CDD, renouvellements, alertes
- **Système de paie** : Exercices, bulletins, rubriques
- **Documents** : Upload et gestion des fichiers
- **Rapports** : Dashboards RH et comptable

## Authentification
Toutes les routes protégées nécessitent un token JWT dans le header :
```
Authorization: Bearer <votre_token_jwt>
```

## Permissions
- `view_personnel` : Consultation des données personnel
- `manage_hr` : Gestion complète RH
- `manage_accounting` : Gestion de la paie et comptabilité
        """,
        "version": "1.0.0",
        "contact": {
            "name": "Support API",
            "email": "support@entreprise.com"
        }
    },
    "host": "localhost:5000",
    "basePath": "/api/personnel",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "JWT": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Token JWT au format: Bearer <token>"
        }
    },
    "security": [{"JWT": []}],
    "tags": [
        {
            "name": "Personnel",
            "description": "Gestion du personnel et employés"
        },
        {
            "name": "Congés",
            "description": "Gestion des demandes de congés"
        },
        {
            "name": "Absences", 
            "description": "Gestion des absences du personnel"
        },
        {
            "name": "Contrats",
            "description": "Gestion des contrats de travail"
        },
        {
            "name": "Documents",
            "description": "Gestion des documents personnel"
        },
        {
            "name": "Paie",
            "description": "Système de paie et bulletins"
        },
        {
            "name": "Rubriques",
            "description": "Gestion des rubriques de paie"
        },
        {
            "name": "Référentiels",
            "description": "Services, postes, exercices"
        },
        {
            "name": "Dashboards",
            "description": "Tableaux de bord et statistiques"
        },
        {
            "name": "System",
            "description": "Santé et tests du système"
        }
    ]
}

# Définitions des modèles réutilisables
swagger_definitions = {
    "PersonnelBase": {
        "type": "object",
        "required": ["nom", "prenom", "date_embauche", "service_id", "poste_id"],
        "properties": {
            "matricule": {"type": "string", "description": "Matricule unique"},
            "nom": {"type": "string", "description": "Nom de famille"},
            "prenom": {"type": "string", "description": "Prénom"},
            "civilite": {"type": "string", "enum": ["M.", "Mme", "Mlle"]},
            "sexe": {"type": "string", "enum": ["M", "F"]},
            "telephone": {"type": "string"},
            "adresse": {"type": "string"},
            "categorie": {"type": "string", "description": "Cadre, Employé, Ouvrier..."},
            "date_embauche": {"type": "string", "format": "date"},
            "service_id": {"type": "integer"},
            "poste_id": {"type": "integer"}
        }
    },
    "PersonnelResponse": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "matricule": {"type": "string"},
            "nom_complet": {"type": "string"},
            "service": {"type": "string"},
            "poste": {"type": "string"},
            "categorie": {"type": "string"},
            "date_embauche": {"type": "string", "format": "date"},
            "status": {"type": "string"}
        }
    },
    "CongeRequest": {
        "type": "object",
        "required": ["personnel_id", "type_conge", "date_debut", "date_fin"],
        "properties": {
            "personnel_id": {"type": "integer"},
            "type_conge": {"type": "string", "description": "Annuel, Maladie, Maternité..."},
            "date_debut": {"type": "string", "format": "date"},
            "date_fin": {"type": "string", "format": "date"}
        }
    },
    "ContratRequest": {
        "type": "object", 
        "required": ["personnel_id", "type", "date_debut", "salaire_base"],
        "properties": {
            "personnel_id": {"type": "integer"},
            "type": {"type": "string", "enum": ["CDI", "CDD", "Stage", "Consultant"]},
            "date_debut": {"type": "string", "format": "date"},
            "date_fin": {"type": "string", "format": "date"},
            "salaire_base": {"type": "number", "format": "float"}
        }
    },
    "RubriqueRequest": {
        "type": "object",
        "required": ["libelle", "type", "mode_p", "valeur"],
        "properties": {
            "libelle": {"type": "string"},
            "type": {"type": "string", "enum": ["gain", "retenue", "information"]},
            "mode_p": {"type": "string", "enum": ["fixe", "variable", "%"]},
            "valeur": {"type": "number", "format": "float"}
        }
    },
    "StandardResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "data": {"type": "object"}
        }
    },
    "ErrorResponse": {
        "type": "object",
        "properties": {
            "error": {"type": "string"}
        }
    }
}

personnel_bp = Blueprint('personnel', __name__, url_prefix='/api/personnel')
api = Api(personnel_bp)

# Ajouter les définitions Swagger
personnel_bp.swagger_config = swagger_config
personnel_bp.swagger_definitions = swagger_definitions

# === SPÉCIFICATIONS SWAGGER POUR CHAQUE ENDPOINT ===

# Personnel CRUD
PersonnelResource.post.__doc__ = """
Créer un nouveau personnel
---
tags:
  - Personnel
summary: Créer un nouveau personnel
description: Crée un nouveau personnel avec possibilité de créer un compte utilisateur et un contrat
security:
  - JWT: []
parameters:
  - in: body
    name: personnel_data
    required: true
    schema:
      allOf:
        - type: object
          properties:
            create_user_account:
              type: boolean
              default: false
              description: Créer un compte utilisateur associé
            user_data:
              type: object
              properties:
                username: {type: string}
                email: {type: string, format: email}
                password: {type: string}
                role: {type: string, default: "user"}
            contrat_data:
              $ref: '#/definitions/ContratRequest'
responses:
  201:
    description: Personnel créé avec succès
    schema:
      $ref: '#/definitions/StandardResponse'
  400:
    description: Données invalides
    schema:
      $ref: '#/definitions/ErrorResponse'
  500:
    description: Erreur serveur
    schema:
      $ref: '#/definitions/ErrorResponse'
"""

PersonnelResource.get.__doc__ = """
Lister le personnel avec filtres
---
tags:
  - Personnel
summary: Obtenir la liste du personnel
description: Récupère la liste du personnel avec possibilité de filtrage et pagination
security:
  - JWT: []
parameters:
  - in: query
    name: service_id
    type: integer
    description: Filtrer par service
  - in: query
    name: poste_id
    type: integer
    description: Filtrer par poste
  - in: query
    name: status
    type: string
    description: Filtrer par statut
  - in: query
    name: categorie
    type: string
    description: Filtrer par catégorie
  - in: query
    name: search
    type: string
    description: Recherche par nom, prénom ou matricule
  - in: query
    name: page
    type: integer
    default: 1
    description: Numéro de page
  - in: query
    name: per_page
    type: integer
    default: 20
    description: Éléments par page
responses:
  200:
    description: Liste du personnel récupérée
    schema:
      type: object
      properties:
        success: {type: boolean}
        data:
          type: array
          items:
            $ref: '#/definitions/PersonnelResponse'
        pagination:
          type: object
          properties:
            total: {type: integer}
            pages: {type: integer}
            current_page: {type: integer}
            per_page: {type: integer}
"""

PersonnelDetailResource.get.__doc__ = """
Détails d'un personnel
---
tags:
  - Personnel
summary: Obtenir les détails d'un personnel
security:
  - JWT: []
parameters:
  - in: path
    name: personnel_id
    type: integer
    required: true
    description: ID du personnel
responses:
  200:
    description: Détails du personnel
    schema:
      $ref: '#/definitions/StandardResponse'
  404:
    description: Personnel introuvable
"""

PersonnelDetailResource.put.__doc__ = """
Mettre à jour un personnel
---
tags:
  - Personnel
summary: Modifier les informations d'un personnel
security:
  - JWT: []
parameters:
  - in: path
    name: personnel_id
    type: integer
    required: true
  - in: body
    name: update_data
    schema:
      $ref: '#/definitions/PersonnelBase'
responses:
  200:
    description: Personnel mis à jour
    schema:
      $ref: '#/definitions/StandardResponse'
"""

PersonnelDetailResource.delete.__doc__ = """
Supprimer un personnel
---
tags:
  - Personnel
summary: Supprimer un personnel (soft delete)
security:
  - JWT: []
parameters:
  - in: path
    name: personnel_id
    type: integer
    required: true
responses:
  200:
    description: Personnel supprimé
    schema:
      $ref: '#/definitions/StandardResponse'
"""

# Congés
CongeResource.post.__doc__ = """
Créer une demande de congé
---
tags:
  - Congés
summary: Créer une nouvelle demande de congé
security:
  - JWT: []
parameters:
  - in: body
    name: conge_data
    required: true
    schema:
      $ref: '#/definitions/CongeRequest'
responses:
  201:
    description: Demande de congé créée
    schema:
      $ref: '#/definitions/StandardResponse'
"""

CongeApproveResource.put.__doc__ = """
Approuver un congé
---
tags:
  - Congés
summary: Approuver une demande de congé
security:
  - JWT: []
parameters:
  - in: path
    name: conge_id
    type: integer
    required: true
responses:
  200:
    description: Congé approuvé
"""

CongeRejectResource.put.__doc__ = """
Rejeter un congé
---
tags:
  - Congés
summary: Rejeter une demande de congé
security:
  - JWT: []
parameters:
  - in: path
    name: conge_id
    type: integer
    required: true
  - in: body
    name: reject_data
    schema:
      type: object
      properties:
        motif: {type: string, description: "Motif du rejet"}
responses:
  200:
    description: Congé rejeté
"""

PersonnelCongesResource.get.__doc__ = """
Congés d'un personnel
---
tags:
  - Congés
summary: Obtenir les congés d'un personnel
security:
  - JWT: []
parameters:
  - in: path
    name: personnel_id
    type: integer
    required: true
  - in: query
    name: annee
    type: integer
    description: Filtrer par année
responses:
  200:
    description: Liste des congés du personnel
"""

# Paie
PayrollExerciceResource.post.__doc__ = """
Créer un exercice de paie
---
tags:
  - Paie
summary: Créer un nouvel exercice comptable
security:
  - JWT: []
parameters:
  - in: body
    name: exercice_data
    required: true
    schema:
      type: object
      required: [mois_annee]
      properties:
        mois_annee: {type: string, example: "2024-01"}
responses:
  201:
    description: Exercice créé
"""

PayrollProcessResource.post.__doc__ = """
Traiter la paie
---
tags:
  - Paie
summary: Traiter la paie pour un exercice
description: Lance le processus de calcul et génération des bulletins de paie
security:
  - JWT: []
parameters:
  - in: body
    name: payroll_data
    required: true
    schema:
      type: object
      required: [exercice_id]
      properties:
        exercice_id: {type: integer}
        personnel_ids: 
          type: array
          items: {type: integer}
          description: "IDs du personnel à traiter (tous si omis)"
responses:
  200:
    description: Traitement de paie terminé
    schema:
      type: object
      properties:
        success: {type: boolean}
        message: {type: string}
        data:
          type: object
          properties:
            total_processed: {type: integer}
            total_amount: {type: number}
            success: {type: array}
            errors: {type: array}
"""

BulletinPaieResource.get.__doc__ = """
Bulletin de paie
---
tags:
  - Paie
summary: Obtenir un bulletin de paie
security:
  - JWT: []
parameters:
  - in: path
    name: personnel_id
    type: integer
    required: true
  - in: path
    name: exercice_id
    type: integer
    required: true
responses:
  200:
    description: Bulletin de paie
    schema:
      type: object
      properties:
        success: {type: boolean}
        data:
          type: object
          properties:
            personnel: {type: object}
            exercice: {type: object}
            lignes: {type: array}
            totaux:
              type: object
              properties:
                total_gains: {type: number}
                total_retenues: {type: number}
                net_payer: {type: number}
  404:
    description: Bulletin introuvable
"""

# Références
ReferentielServicesResource.get.__doc__ = """
Liste des services
---
tags:
  - Référentiels
summary: Obtenir tous les services actifs
responses:
  200:
    description: Liste des services
    schema:
      type: object
      properties:
        success: {type: boolean}
        data:
          type: array
          items:
            type: object
            properties:
              id: {type: integer}
              libelle: {type: string}
              status: {type: string}
"""

ReferentielPostesResource.get.__doc__ = """
Liste des postes
---
tags:
  - Référentiels
summary: Obtenir tous les postes actifs
responses:
  200:
    description: Liste des postes
"""

ReferentielExercicesResource.get.__doc__ = """
Liste des exercices
---
tags:
  - Référentiels
summary: Obtenir tous les exercices comptables
responses:
  200:
    description: Liste des exercices
"""

ReferentielRubriquesResource.get.__doc__ = """
Liste des rubriques
---
tags:
  - Référentiels
summary: Obtenir les rubriques de paie
parameters:
  - in: query
    name: type
    type: string
    enum: [gain, retenue, information]
    description: Filtrer par type de rubrique
responses:
  200:
    description: Liste des rubriques
"""

# Documents
DocumentResource.post.__doc__ = """
Upload de document
---
tags:
  - Documents
summary: Uploader un document pour un personnel
security:
  - JWT: []
consumes:
  - multipart/form-data
parameters:
  - in: path
    name: personnel_id
    type: integer
    required: true
  - in: formData
    name: file
    type: file
    required: true
    description: Fichier à uploader
  - in: formData
    name: libelle
    type: string
    required: true
    description: Libellé du document
responses:
  201:
    description: Document uploadé avec succès
"""

DocumentResource.get.__doc__ = """
Documents d'un personnel
---
tags:
  - Documents
summary: Obtenir tous les documents d'un personnel
security:
  - JWT: []
parameters:
  - in: path
    name: personnel_id
    type: integer
    required: true
responses:
  200:
    description: Liste des documents
"""

# Absences
AbsenceResource.post.__doc__ = """
Enregistrer une absence
---
tags:
  - Absences
summary: Enregistrer une nouvelle absence
security:
  - JWT: []
parameters:
  - in: body
    name: absence_data
    required: true
    schema:
      type: object
      required: [personnel_id, libelle, date_debut, date_fin]
      properties:
        personnel_id: {type: integer}
        libelle: {type: string}
        date_debut: {type: string, format: date}
        date_fin: {type: string, format: date}
        motif: {type: string}
        justifiee: {type: boolean, default: false}
responses:
  201:
    description: Absence enregistrée
"""

PersonnelAbsencesResource.get.__doc__ = """
Absences d'un personnel
---
tags:
  - Absences
summary: Obtenir les absences d'un personnel
security:
  - JWT: []
parameters:
  - in: path
    name: personnel_id
    type: integer
    required: true
  - in: query
    name: date_debut
    type: string
    format: date
  - in: query
    name: date_fin
    type: string
    format: date
responses:
  200:
    description: Liste des absences
"""

# Contrats
ContratResource.post.__doc__ = """
Créer un contrat
---
tags:
  - Contrats
summary: Créer un nouveau contrat de travail
security:
  - JWT: []
parameters:
  - in: body
    name: contrat_data
    required: true
    schema:
      $ref: '#/definitions/ContratRequest'
responses:
  201:
    description: Contrat créé
"""

PersonnelContratsResource.get.__doc__ = """
Contrats d'un personnel
---
tags:
  - Contrats
summary: Obtenir tous les contrats d'un personnel
security:
  - JWT: []
parameters:
  - in: path
    name: personnel_id
    type: integer
    required: true
responses:
  200:
    description: Liste des contrats
"""

# Rubriques
RubriqueResource.post.__doc__ = """
Créer une rubrique
---
tags:
  - Rubriques
summary: Créer une nouvelle rubrique de paie
security:
  - JWT: []
parameters:
  - in: body
    name: rubrique_data
    required: true
    schema:
      $ref: '#/definitions/RubriqueRequest'
responses:
  201:
    description: Rubrique créée
"""

AssignRubriqueResource.post.__doc__ = """
Assigner rubrique à poste
---
tags:
  - Rubriques
summary: Assigner une rubrique à un poste avec montant
security:
  - JWT: []
parameters:
  - in: body
    name: assignment_data
    required: true
    schema:
      type: object
      required: [poste_id, rubrique_id, montant]
      properties:
        poste_id: {type: integer}
        rubrique_id: {type: integer}
        montant: {type: number, format: float}
responses:
  200:
    description: Rubrique assignée
"""

# Dashboards
HRDashboardResource.get.__doc__ = """
Dashboard RH
---
tags:
  - Dashboards
summary: Statistiques du dashboard RH
security:
  - JWT: []
responses:
  200:
    description: Statistiques RH
    schema:
      type: object
      properties:
        message: {type: string}
        stats:
          type: object
          properties:
            total_personnel: {type: integer}
            nouveaux_ce_mois: {type: integer}
            conges_en_attente: {type: integer}
            conges_approuves_ce_mois: {type: integer}
        hr_manager: {type: string}
        timestamp: {type: string}
"""

AccountingDashboardResource.get.__doc__ = """
Dashboard comptable paie
---
tags:
  - Dashboards
summary: Résumé comptable de la paie
security:
  - JWT: []
responses:
  200:
    description: Statistiques comptables
    schema:
      type: object
      properties:
        message: {type: string}
        stats:
          type: object
          properties:
            exercices_ouverts: {type: integer}
            exercices_clos: {type: integer}
            dernier_exercice: {type: object}
            total_paies_traitees: {type: integer}
            montant_total_paies: {type: number}
        comptable: {type: string}
        timestamp: {type: string}
"""

# System
HealthResource.get.__doc__ = """
Santé du module RH
---
tags:
  - System
summary: Vérifier l'état du module RH
responses:
  200:
    description: Module opérationnel
    schema:
      type: object
      properties:
        status: {type: string}
        timestamp: {type: string}
        features: 
          type: array
          items: {type: string}
"""

TestPermissionsResource.get.__doc__ = """
Test des permissions RH
---
tags:
  - System
summary: Analyser les permissions de l'utilisateur actuel
security:
  - JWT: []
responses:
  200:
    description: Analyse des permissions
    schema:
      type: object
      properties:
        message: {type: string}
        user_id: {type: string}
        username: {type: string}
        user_type: {type: string}
        all_permissions: {type: array, items: {type: string}}
        personnel_permissions: {type: array, items: {type: string}}
        can_manage_hr: {type: boolean}
        can_manage_accounting: {type: boolean}
        can_view_personnel: {type: boolean}
"""

# === ENREGISTREMENT DES ROUTES ===
api.add_resource(PersonnelResource, '/')
api.add_resource(PersonnelDetailResource, '/<int:personnel_id>')

# Routes congés
api.add_resource(CongeResource, '/conges')
api.add_resource(CongeApproveResource, '/conges/<int:conge_id>/approve')
api.add_resource(CongeRejectResource, '/conges/<int:conge_id>/reject')
api.add_resource(PersonnelCongesResource, '/conges/personnel/<int:personnel_id>')

# Routes paie
api.add_resource(PayrollExerciceResource, '/payroll/exercice')
api.add_resource(PayrollProcessResource, '/payroll/process')
api.add_resource(BulletinPaieResource, '/payroll/bulletin/<int:personnel_id>/<int:exercice_id>')

# Routes référentiels
api.add_resource(ReferentielServicesResource, '/referentiels/services')
api.add_resource(ReferentielPostesResource, '/referentiels/postes')
api.add_resource(ReferentielExercicesResource, '/referentiels/exercices')
api.add_resource(ReferentielRubriquesResource, '/referentiels/rubriques')

# Routes documents
api.add_resource(DocumentResource, '/<int:personnel_id>/documents')
api.add_resource(DocumentDeleteResource, '/documents/<int:document_id>')

# Routes absences
api.add_resource(AbsenceResource, '/absences')
api.add_resource(PersonnelAbsencesResource, '/absences/personnel/<int:personnel_id>')
api.add_resource(RapportAbsencesResource, '/absences/rapport')

# Routes contrats
api.add_resource(ContratResource, '/contrats')
api.add_resource(PersonnelContratsResource, '/contrats/personnel/<int:personnel_id>')
api.add_resource(ContratsExpiresResource, '/contrats/expires')

# Routes rubriques
api.add_resource(RubriqueResource, '/rubriques')
api.add_resource(AssignRubriqueResource, '/rubriques/assign-poste')
api.add_resource(PosteRubriquesResource, '/rubriques/poste/<int:poste_id>')

# Routes dashboards
api.add_resource(HRDashboardResource, '/hr/dashboard')
api.add_resource(AccountingDashboardResource, '/accounting/payroll-summary')

# Routes système
api.add_resource(HealthResource, '/health')
api.add_resource(TestPermissionsResource, '/test-permissions')