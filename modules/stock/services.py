from datetime import datetime
from core.database import db
from .models import (
    Categorie, Produit, LotStock, MouvementStock, Fournisseur, Client,
    Achat, LigneAchat, Vente, LigneVente, LigneVenteLot, Retour, LigneRetour,
    TypeMouvement, TypeRetour
)
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload

class StockService:
    """Service principal pour la gestion des stocks"""
    
    @staticmethod
    def get_stock_global():
        """Récupère l'état global du stock"""
        # Statistiques générales
        total_produits = Produit.query.count()
        total_categories = Categorie.query.count()
        
        # Stock par catégorie
        stock_par_categorie = db.session.query(
            Categorie.libelle,
            func.count(Produit.id).label('nb_produits'),
            func.sum(LotStock.qte_disponible).label('qte_totale'),
            func.sum(LotStock.qte_disponible * LotStock.prix_achat).label('valeur_totale')
        ).join(Produit.categorie_ref).join(Produit.lots_stock)\
         .group_by(Categorie.id, Categorie.libelle).all()
        
        # Produits en rupture ou en alerte
        produits_rupture = []
        produits_alerte = []
        
        for produit in Produit.query.all():
            stock = produit.stock_total
            if stock == 0:
                produits_rupture.append(produit.to_dict())
            elif stock <= 5:  # Seuil d'alerte par défaut
                produits_alerte.append(produit.to_dict())
        
        return {
            'resume': {
                'total_produits': total_produits,
                'total_categories': total_categories,
                'produits_rupture': len(produits_rupture),
                'produits_alerte': len(produits_alerte)
            },
            'stock_par_categorie': [
                {
                    'categorie': row.libelle,
                    'nb_produits': row.nb_produits or 0,
                    'qte_totale': int(row.qte_totale or 0),
                    'valeur_totale': float(row.valeur_totale or 0)
                } for row in stock_par_categorie
            ],
            'alertes': {
                'ruptures': produits_rupture,
                'stock_faible': produits_alerte
            }
        }
    
    @staticmethod
    def ajuster_stock(produit_id, nouvelle_quantite, motif="Ajustement manuel"):
        """Ajuste le stock d'un produit"""
        produit = Produit.query.get(produit_id)
        if not produit:
            raise ValueError("Produit non trouvé")
        
        stock_actuel = produit.stock_total
        difference = nouvelle_quantite - stock_actuel
        
        if difference == 0:
            return {"message": "Aucun ajustement nécessaire"}
        
        if difference > 0:
            # Augmentation de stock - créer un nouveau lot
            lot = LotStock(
                produit_id=produit_id,
                qte_disponible=difference,
                prix_achat=produit.prix  # Utiliser le prix de vente comme prix d'achat par défaut
            )
            db.session.add(lot)
            type_mouvement = TypeMouvement.AJUSTEMENT.value
        else:
            # Diminution de stock - prélever des lots (FIFO)
            difference = abs(difference)
            lots_disponibles = LotStock.query.filter_by(produit_id=produit_id)\
                                           .filter(LotStock.qte_disponible > 0)\
                                           .order_by(LotStock.date_entree.asc()).all()
            
            stock_disponible = sum(lot.qte_disponible for lot in lots_disponibles)
            if stock_disponible < difference:
                raise ValueError(f"Stock insuffisant pour l'ajustement. Disponible: {stock_disponible}")
            
            quantite_restante = difference
            for lot in lots_disponibles:
                if quantite_restante <= 0:
                    break
                
                qte_a_prelever = min(lot.qte_disponible, quantite_restante)
                lot.qte_disponible -= qte_a_prelever
                quantite_restante -= qte_a_prelever
            
            type_mouvement = TypeMouvement.AJUSTEMENT.value
            difference = -difference  # Négative pour le mouvement
        
        # Créer le mouvement
        mouvement = MouvementStock(
            produit_id=produit_id,
            type=type_mouvement,
            qte=difference,
            reference_doc=f"ADJUST-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        )
        db.session.add(mouvement)
        db.session.commit()
        
        return {
            "message": f"Stock ajusté de {stock_actuel} à {nouvelle_quantite}",
            "difference": difference,
            "nouveau_stock": produit.stock_total
        }

class CategorieService:
    """Service pour la gestion des catégories"""
    
    @staticmethod
    def create_categorie(libelle, description=None):
        """Crée une nouvelle catégorie"""
        if Categorie.query.filter_by(libelle=libelle).first():
            raise ValueError("Une catégorie avec ce libellé existe déjà")
        
        categorie = Categorie(
            libelle=libelle,
            description=description
        )
        db.session.add(categorie)
        db.session.commit()
        
        return categorie
    
    @staticmethod
    def get_all_categories():
        """Récupère toutes les catégories avec leurs statistiques"""
        categories = Categorie.query.all()
        return [cat.to_dict() for cat in categories]
    
    @staticmethod
    def update_categorie(categorie_id, **kwargs):
        """Met à jour une catégorie"""
        categorie = Categorie.query.get(categorie_id)
        if not categorie:
            raise ValueError("Catégorie non trouvée")
        
        for key, value in kwargs.items():
            if hasattr(categorie, key) and value is not None:
                setattr(categorie, key, value)
        
        db.session.commit()
        return categorie

class ProduitService:
    """Service pour la gestion des produits"""
    
    @staticmethod
    def create_produit(nom, reference, prix, categorie_id):
        """Crée un nouveau produit"""
        # Vérifications
        if Produit.query.filter_by(reference=reference).first():
            raise ValueError("Un produit avec cette référence existe déjà")
        
        if not Categorie.query.get(categorie_id):
            raise ValueError("Catégorie non trouvée")
        
        produit = Produit(
            nom=nom,
            reference=reference,
            prix=prix,
            categorie_id=categorie_id
        )
        db.session.add(produit)
        db.session.commit()
        
        return produit
    
    @staticmethod
    def get_produit_with_stock(produit_id):
        """Récupère un produit avec ses détails de stock"""
        produit = Produit.query.get(produit_id)
        if not produit:
            raise ValueError("Produit non trouvé")
        
        return produit.to_dict(include_stock=True)
    
    @staticmethod
    def get_all_produits(include_stock=False, categorie_id=None):
        """Récupère tous les produits avec filtrage optionnel"""
        query = Produit.query
        
        if categorie_id:
            query = query.filter_by(categorie_id=categorie_id)
        
        produits = query.all()
        return [p.to_dict(include_stock=include_stock) for p in produits]
    
    @staticmethod
    def update_produit(produit_id, **kwargs):
        """Met à jour un produit"""
        produit = Produit.query.get(produit_id)
        if not produit:
            raise ValueError("Produit non trouvé")
        
        # Vérifier la référence si elle change
        if 'reference' in kwargs and kwargs['reference'] != produit.reference:
            if Produit.query.filter_by(reference=kwargs['reference']).first():
                raise ValueError("Cette référence existe déjà")
        
        for key, value in kwargs.items():
            if hasattr(produit, key) and value is not None:
                setattr(produit, key, value)
        
        db.session.commit()
        return produit

class FournisseurService:
    """Service pour la gestion des fournisseurs"""
    
    @staticmethod
    def create_fournisseur(nom, adresse=None, telephone=None):
        """Crée un nouveau fournisseur"""
        fournisseur = Fournisseur(
            nom=nom,
            adresse=adresse,
            telephone=telephone
        )
        db.session.add(fournisseur)
        db.session.commit()
        
        return fournisseur
    
    @staticmethod
    def get_all_fournisseurs():
        """Récupère tous les fournisseurs"""
        fournisseurs = Fournisseur.query.all()
        return [f.to_dict() for f in fournisseurs]

class ClientService:
    """Service pour la gestion des clients"""
    
    @staticmethod
    def create_client(nom, adresse=None, telephone=None):
        """Crée un nouveau client"""
        client = Client(
            nom=nom,
            adresse=adresse,
            telephone=telephone
        )
        db.session.add(client)
        db.session.commit()
        
        return client
    
    @staticmethod
    def get_all_clients():
        """Récupère tous les clients"""
        clients = Client.query.all()
        return [c.to_dict() for c in clients]

class AchatService:
    """Service pour la gestion des achats"""
    
    @staticmethod
    def create_achat(fournisseur_id, lignes_data):
        """
        Crée un nouvel achat
        lignes_data: [{"produit_id": 1, "qte": 10, "prix_unitaire": 15.5}, ...]
        """
        if not Fournisseur.query.get(fournisseur_id):
            raise ValueError("Fournisseur non trouvé")
        
        # Créer l'achat
        achat = Achat(fournisseur_id=fournisseur_id)
        db.session.add(achat)
        db.session.flush()  # Pour obtenir l'ID
        
        # Créer les lignes
        for ligne_data in lignes_data:
            if not Produit.query.get(ligne_data['produit_id']):
                raise ValueError(f"Produit {ligne_data['produit_id']} non trouvé")
            
            ligne = LigneAchat(
                achat_id=achat.id,
                produit_id=ligne_data['produit_id'],
                qte=ligne_data['qte'],
                prix_unitaire=ligne_data['prix_unitaire']
            )
            db.session.add(ligne)
        
        # Calculer le total
        achat.calculer_total()
        db.session.commit()
        
        return achat
    
    @staticmethod
    def valider_achat(achat_id):
        """Valide un achat et met à jour les stocks"""
        achat = Achat.query.get(achat_id)
        if not achat:
            raise ValueError("Achat non trouvé")
        
        achat.valider_achat()
        db.session.commit()
        
        return {"message": f"Achat {achat_id} validé et stocks mis à jour"}
    
    @staticmethod
    def get_all_achats(include_lignes=False):
        """Récupère tous les achats"""
        achats = Achat.query.order_by(Achat.date_achat.desc()).all()
        return [a.to_dict(include_lignes=include_lignes) for a in achats]

class VenteService:
    """Service pour la gestion des ventes"""
    
    @staticmethod
    def create_vente(client_id, lignes_data):
        """
        Crée une nouvelle vente
        lignes_data: [{"produit_id": 1, "qte": 2, "prix_unitaire": 25.0}, ...]
        """
        if not Client.query.get(client_id):
            raise ValueError("Client non trouvé")
        
        # Vérifier la disponibilité des stocks avant de créer la vente
        for ligne_data in lignes_data:
            produit = Produit.query.get(ligne_data['produit_id'])
            if not produit:
                raise ValueError(f"Produit {ligne_data['produit_id']} non trouvé")
            
            if produit.stock_total < ligne_data['qte']:
                raise ValueError(f"Stock insuffisant pour {produit.reference}. Disponible: {produit.stock_total}, Demandé: {ligne_data['qte']}")
        
        # Créer la vente
        vente = Vente(client_id=client_id)
        db.session.add(vente)
        db.session.flush()  # Pour obtenir l'ID
        
        # Créer les lignes
        for ligne_data in lignes_data:
            ligne = LigneVente(
                vente_id=vente.id,
                produit_id=ligne_data['produit_id'],
                qte=ligne_data['qte'],
                prix_unitaire=ligne_data['prix_unitaire']
            )
            db.session.add(ligne)
        
        # Calculer le total
        vente.calculer_total()
        db.session.commit()
        
        return vente
    
    @staticmethod
    def valider_vente(vente_id):
        """Valide une vente et met à jour les stocks"""
        vente = Vente.query.get(vente_id)
        if not vente:
            raise ValueError("Vente non trouvée")
        
        vente.valider_vente()
        db.session.commit()
        
        return {"message": f"Vente {vente_id} validée et stocks mis à jour"}
    
    @staticmethod
    def get_all_ventes(include_lignes=False):
        """Récupère toutes les ventes"""
        ventes = Vente.query.order_by(Vente.date_vente.desc()).all()
        return [v.to_dict(include_lignes=include_lignes) for v in ventes]

class RetourService:
    """Service pour la gestion des retours"""
    
    @staticmethod
    def create_retour(client_id, type_retour, lignes_data, vente_id=None):
        """
        Crée un nouveau retour
        lignes_data: [{"produit_id": 1, "qte": 1, "motif": "Défectueux"}, ...]
        """
        if not Client.query.get(client_id):
            raise ValueError("Client non trouvé")
        
        if type_retour not in [t.value for t in TypeRetour]:
            raise ValueError(f"Type de retour invalide. Types autorisés: {[t.value for t in TypeRetour]}")
        
        # Créer le retour
        retour = Retour(
            client_id=client_id,
            vente_id=vente_id,
            type_retour=type_retour
        )
        db.session.add(retour)
        db.session.flush()  # Pour obtenir l'ID
        
        # Créer les lignes
        for ligne_data in lignes_data:
            if not Produit.query.get(ligne_data['produit_id']):
                raise ValueError(f"Produit {ligne_data['produit_id']} non trouvé")
            
            ligne = LigneRetour(
                retour_id=retour.id,
                produit_id=ligne_data['produit_id'],
                qte=ligne_data['qte'],
                motif=ligne_data.get('motif', '')
            )
            db.session.add(ligne)
        
        db.session.commit()
        return retour
    
    @staticmethod
    def traiter_retour(retour_id):
        """Traite un retour selon son type"""
        retour = Retour.query.get(retour_id)
        if not retour:
            raise ValueError("Retour non trouvé")
        
        retour.traiter_retour()
        db.session.commit()
        
        return {"message": f"Retour {retour_id} traité selon le type {retour.type_retour}"}
    
    @staticmethod
    def get_all_retours(include_lignes=False):
        """Récupère tous les retours"""
        retours = Retour.query.order_by(Retour.date_retour.desc()).all()
        return [r.to_dict(include_lignes=include_lignes) for r in retours]

class MouvementService:
    """Service pour la gestion des mouvements de stock"""
    
    @staticmethod
    def get_mouvements(produit_id=None, type_mouvement=None, date_debut=None, date_fin=None):
        """Récupère les mouvements avec filtrage"""
        query = MouvementStock.query
        
        if produit_id:
            query = query.filter_by(produit_id=produit_id)
        
        if type_mouvement:
            query = query.filter_by(type=type_mouvement)
        
        if date_debut:
            query = query.filter(MouvementStock.date_mouvement >= date_debut)
        
        if date_fin:
            query = query.filter(MouvementStock.date_mouvement <= date_fin)
        
        mouvements = query.order_by(MouvementStock.date_mouvement.desc()).all()
        return [m.to_dict() for m in mouvements]
    
    @staticmethod
    def get_historique_produit(produit_id):
        """Récupère l'historique complet d'un produit"""
        produit = Produit.query.get(produit_id)
        if not produit:
            raise ValueError("Produit non trouvé")
        
        # Mouvements
        mouvements = MouvementService.get_mouvements(produit_id=produit_id)
        
        # Lots actuels
        lots = LotStock.query.filter_by(produit_id=produit_id).all()
        
        # Statistiques
        total_entrees = db.session.query(func.sum(MouvementStock.qte))\
            .filter_by(produit_id=produit_id, type=TypeMouvement.ENTREE.value).scalar() or 0
        
        total_sorties = db.session.query(func.sum(MouvementStock.qte))\
            .filter_by(produit_id=produit_id, type=TypeMouvement.SORTIE.value).scalar() or 0
        
        return {
            'produit': produit.to_dict(include_stock=True),
            'statistiques': {
                'total_entrees': int(total_entrees),
                'total_sorties': abs(int(total_sorties)),
                'stock_actuel': produit.stock_total
            },
            'lots_actuels': [lot.to_dict() for lot in lots],
            'mouvements': mouvements
        }

class RapportService:
    """Service pour générer des rapports"""
    
    @staticmethod
    def rapport_stock():
        """Rapport détaillé de l'état des stocks"""
        return StockService.get_stock_global()
    
    @staticmethod
    def rapport_ventes(date_debut=None, date_fin=None):
        """Rapport des ventes sur une période"""
        query = Vente.query
        
        if date_debut:
            query = query.filter(Vente.date_vente >= date_debut)
        
        if date_fin:
            query = query.filter(Vente.date_vente <= date_fin)
        
        ventes = query.all()
        
        # Statistiques
        total_ventes = len(ventes)
        chiffre_affaires = sum(vente.total for vente in ventes)
        
        # Top produits vendus
        top_produits = db.session.query(
            Produit.reference,
            Produit.nom,
            func.sum(LigneVente.qte).label('qte_vendue'),
            func.sum(LigneVente.montant).label('ca_produit')
        ).join(LigneVente.produit_ref).join(LigneVente.vente_ref)\
         .filter(query.whereclause if query.whereclause is not None else True)\
         .group_by(Produit.id)\
         .order_by(func.sum(LigneVente.qte).desc()).limit(10).all()
        
        return {
            'periode': {
                'date_debut': date_debut.isoformat() if date_debut else None,
                'date_fin': date_fin.isoformat() if date_fin else None
            },
            'resume': {
                'total_ventes': total_ventes,
                'chiffre_affaires': float(chiffre_affaires)
            },
            'top_produits': [
                {
                    'reference': p.reference,
                    'nom': p.nom,
                    'qte_vendue': int(p.qte_vendue),
                    'ca_produit': float(p.ca_produit)
                } for p in top_produits
            ]
        }
    
    @staticmethod
    def rapport_achats(date_debut=None, date_fin=None):
        """Rapport des achats sur une période"""
        query = Achat.query
        
        if date_debut:
            query = query.filter(Achat.date_achat >= date_debut)
        
        if date_fin:
            query = query.filter(Achat.date_achat <= date_fin)
        
        achats = query.all()
        
        # Statistiques
        total_achats = len(achats)
        total_depense = sum(achat.total for achat in achats)
        
        # Achats par fournisseur
        achats_fournisseur = db.session.query(
            Fournisseur.nom,
            func.count(Achat.id).label('nb_achats'),
            func.sum(Achat.total).label('total_achats')
        ).join(Achat.fournisseur_ref)\
         .filter(query.whereclause if query.whereclause is not None else True)\
         .group_by(Fournisseur.id)\
         .order_by(func.sum(Achat.total).desc()).all()
        
        return {
            'periode': {
                'date_debut': date_debut.isoformat() if date_debut else None,
                'date_fin': date_fin.isoformat() if date_fin else None
            },
            'resume': {
                'total_achats': total_achats,
                'total_depense': float(total_depense)
            },
            'achats_par_fournisseur': [
                {
                    'fournisseur': f.nom,
                    'nb_achats': f.nb_achats,
                    'total_achats': float(f.total_achats)
                } for f in achats_fournisseur
            ]
        }

class InitStockService:
    """Service d'initialisation du module stock"""
    
    @staticmethod
    def init_stock_data():
        """Initialise les données de test du module stock"""
        print("\n=== Initialisation du module Stock ===")
        
        try:
            # Créer des catégories de test
            categories_data = [
                ("Électronique", "Produits électroniques et accessoires"),
                ("Mobilier", "Meubles et équipements de bureau"),
                ("Fournitures", "Fournitures de bureau et consommables"),
                ("Alimentaire", "Produits alimentaires et boissons")
            ]
            
            categories = {}
            for libelle, description in categories_data:
                if not Categorie.query.filter_by(libelle=libelle).first():
                    cat = CategorieService.create_categorie(libelle, description)
                    categories[libelle] = cat.id
                    print(f"[+] Catégorie créée: {libelle}")
                else:
                    categories[libelle] = Categorie.query.filter_by(libelle=libelle).first().id
            
            # Créer des produits de test
            produits_data = [
                ("Ordinateur portable", "PC-001", 800.00, "Électronique"),
                ("Souris optique", "SOU-001", 25.00, "Électronique"),
                ("Bureau en bois", "BUR-001", 350.00, "Mobilier"),
                ("Chaise de bureau", "CHA-001", 120.00, "Mobilier"),
                ("Ramette papier A4", "PAP-001", 8.50, "Fournitures"),
                ("Café en grain", "CAF-001", 12.00, "Alimentaire")
            ]
            
            produits = {}
            for nom, reference, prix, categorie in produits_data:
                if not Produit.query.filter_by(reference=reference).first():
                    prod = ProduitService.create_produit(nom, reference, prix, categories[categorie])
                    produits[reference] = prod.id
                    print(f"[+] Produit créé: {reference}")
                else:
                    produits[reference] = Produit.query.filter_by(reference=reference).first().id
            
            # Créer des fournisseurs de test
            fournisseurs_data = [
                ("TechCorp Distribution", "123 Rue de la Tech, Douala", "+237 666 123 456"),
                ("Mobilier Pro", "456 Avenue du Commerce, Yaoundé", "+237 677 987 654"),
                ("Bureau Plus", "789 Boulevard Central, Douala", "+237 655 111 222")
            ]
            
            fournisseurs = {}
            for nom, adresse, telephone in fournisseurs_data:
                if not Fournisseur.query.filter_by(nom=nom).first():
                    fournisseur = FournisseurService.create_fournisseur(nom, adresse, telephone)
                    fournisseurs[nom] = fournisseur.id
                    print(f"[+] Fournisseur créé: {nom}")
                else:
                    fournisseurs[nom] = Fournisseur.query.filter_by(nom=nom).first().id
            
            # Créer des clients de test
            clients_data = [
                ("Entreprise ABC", "321 Rue des Affaires, Douala", "+237 699 555 333"),
                ("Société XYZ", "654 Avenue Centrale, Yaoundé", "+237 677 444 222"),
                ("Bureau Service", "987 Boulevard Commerce, Douala", "+237 655 777 888")
            ]
            
            clients = {}
            for nom, adresse, telephone in clients_data:
                if not Client.query.filter_by(nom=nom).first():
                    client = ClientService.create_client(nom, adresse, telephone)
                    clients[nom] = client.id
                    print(f"[+] Client créé: {nom}")
                else:
                    clients[nom] = Client.query.filter_by(nom=nom).first().id
            
            # Créer des achats de test pour alimenter les stocks
            achats_data = [
                (fournisseurs["TechCorp Distribution"], [
                    {"produit_id": produits["PC-001"], "qte": 10, "prix_unitaire": 750.00},
                    {"produit_id": produits["SOU-001"], "qte": 50, "prix_unitaire": 20.00}
                ]),
                (fournisseurs["Mobilier Pro"], [
                    {"produit_id": produits["BUR-001"], "qte": 5, "prix_unitaire": 300.00},
                    {"produit_id": produits["CHA-001"], "qte": 20, "prix_unitaire": 100.00}
                ])
            ]
            
            for fournisseur_id, lignes in achats_data:
                achat = AchatService.create_achat(fournisseur_id, lignes)
                AchatService.valider_achat(achat.id)
                print(f"[+] Achat créé et validé: {achat.id}")
            
            print("=== Initialisation stock terminée ===\n")
            
            return {
                'categories': len(categories),
                'produits': len(produits),
                'fournisseurs': len(fournisseurs),
                'clients': len(clients),
                'achats_initialises': len(achats_data)
            }
            
        except Exception as e:
            print(f"[!] Erreur initialisation stock: {str(e)}")
            db.session.rollback()
            raise