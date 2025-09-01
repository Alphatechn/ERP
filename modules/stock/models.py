from datetime import datetime
from core.database import db
from enum import Enum

class TypeMouvement(Enum):
    ENTREE = "entree"
    SORTIE = "sortie"
    TRANSFERT = "transfert"
    AJUSTEMENT = "ajustement"

class TypeRetour(Enum):
    DEFECTUEUX = "defectueux"
    GARANTIE = "garantie"
    ERREUR_COMMANDE = "erreur_commande"
    AUTRE = "autre"

class Categorie(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Relations
    produits = db.relationship('Produit', backref='categorie_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<Categorie {self.libelle}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'libelle': self.libelle,
            'description': self.description,
            'nb_produits': self.produits.count()
        }

class Produit(db.Model):
    __tablename__ = 'produits'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    reference = db.Column(db.String(50), nullable=False, unique=True)
    prix = db.Column(db.Numeric(10, 2), nullable=False)
    categorie_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    # Relations
    lots_stock = db.relationship('LotStock', backref='produit_ref', lazy='dynamic', cascade='all, delete-orphan')
    mouvements = db.relationship('MouvementStock', backref='produit_ref', lazy='dynamic')
    lignes_achat = db.relationship('LigneAchat', backref='produit_ref', lazy='dynamic')
    lignes_vente = db.relationship('LigneVente', backref='produit_ref', lazy='dynamic')
    lignes_retour = db.relationship('LigneRetour', backref='produit_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<Produit {self.reference} - {self.nom}>'
    
    @property
    def stock_total(self):
        """Calcul du stock total disponible"""
        return sum(lot.qte_disponible for lot in self.lots_stock.filter_by())
    
    @property
    def valeur_stock(self):
        """Valeur totale du stock"""
        return sum(lot.qte_disponible * lot.prix_achat for lot in self.lots_stock.filter_by())
    
    def get_stock_details(self):
        """Détails complets du stock par lot"""
        lots = []
        for lot in self.lots_stock.all():
            lots.append({
                'id': lot.id,
                'qte_disponible': lot.qte_disponible,
                'prix_achat': float(lot.prix_achat),
                'date_entree': lot.date_entree.isoformat()
            })
        return lots
    
    def to_dict(self, include_stock=False):
        data = {
            'id': self.id,
            'nom': self.nom,
            'reference': self.reference,
            'prix': float(self.prix),
            'categorie_id': self.categorie_id,
            'categorie_libelle': self.categorie_ref.libelle if self.categorie_ref else None
        }
        
        if include_stock:
            data.update({
                'stock_total': self.stock_total,
                'valeur_stock': float(self.valeur_stock),
                'lots': self.get_stock_details()
            })
        
        return data

class LotStock(db.Model):
    __tablename__ = 'lots_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    qte_disponible = db.Column(db.Integer, nullable=False, default=0)
    prix_achat = db.Column(db.Numeric(10, 2), nullable=False)
    date_entree = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    lignes_vente_lot = db.relationship('LigneVenteLot', backref='lot_stock_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<LotStock {self.produit_id} - Qte: {self.qte_disponible}>'
    
    def peut_servir(self, quantite_demandee):
        """Vérifie si le lot peut satisfaire la quantité demandée"""
        return self.qte_disponible >= quantite_demandee
    
    def prelever(self, quantite):
        """Prélève une quantité du lot"""
        if not self.peut_servir(quantite):
            raise ValueError(f"Stock insuffisant. Disponible: {self.qte_disponible}, Demandé: {quantite}")
        
        self.qte_disponible -= quantite
        
        # Créer un mouvement de stock
        mouvement = MouvementStock(
            produit_id=self.produit_id,
            type=TypeMouvement.SORTIE.value,
            qte=quantite,
            reference_doc=f"PRELEV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        )
        db.session.add(mouvement)
    
    def to_dict(self):
        return {
            'id': self.id,
            'produit_id': self.produit_id,
            'qte_disponible': self.qte_disponible,
            'prix_achat': float(self.prix_achat),
            'date_entree': self.date_entree.isoformat()
        }

class MouvementStock(db.Model):
    __tablename__ = 'mouvements_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # entree, sortie, transfert, ajustement
    qte = db.Column(db.Integer, nullable=False)
    date_mouvement = db.Column(db.DateTime, default=datetime.utcnow)
    reference_doc = db.Column(db.String(100))  # Référence du document source
    
    def __repr__(self):
        return f'<MouvementStock {self.type} - {self.qte} - {self.produit_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'produit_id': self.produit_id,
            'produit_reference': self.produit_ref.reference if self.produit_ref else None,
            'produit_nom': self.produit_ref.nom if self.produit_ref else None,
            'type': self.type,
            'qte': self.qte,
            'date_mouvement': self.date_mouvement.isoformat(),
            'reference_doc': self.reference_doc
        }

class Fournisseur(db.Model):
    __tablename__ = 'fournisseurs'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    adresse = db.Column(db.Text)
    telephone = db.Column(db.String(20))
    
    # Relations
    achats = db.relationship('Achat', backref='fournisseur_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<Fournisseur {self.nom}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'adresse': self.adresse,
            'telephone': self.telephone,
            'nb_achats': self.achats.count()
        }

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    adresse = db.Column(db.Text)
    telephone = db.Column(db.String(20))
    
    # Relations
    ventes = db.relationship('Vente', backref='client_ref', lazy='dynamic')
    retours = db.relationship('Retour', backref='client_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<Client {self.nom}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'adresse': self.adresse,
            'telephone': self.telephone,
            'nb_ventes': self.ventes.count(),
            'nb_retours': self.retours.count()
        }

class Achat(db.Model):
    __tablename__ = 'achats'
    
    id = db.Column(db.Integer, primary_key=True)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.id'), nullable=False)
    date_achat = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    
    # Relations
    lignes = db.relationship('LigneAchat', backref='achat_ref', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Achat {self.id} - {self.fournisseur_ref.nom if self.fournisseur_ref else "N/A"}>'
    
    def calculer_total(self):
        """Calcule le total de l'achat"""
        self.total = sum(ligne.qte * ligne.prix_unitaire for ligne in self.lignes.all())
        return self.total
    
    def valider_achat(self):
        """Valide l'achat et met à jour les stocks"""
        for ligne in self.lignes.all():
            # Créer ou mettre à jour le lot de stock
            lot = LotStock(
                produit_id=ligne.produit_id,
                qte_disponible=ligne.qte,
                prix_achat=ligne.prix_unitaire
            )
            db.session.add(lot)
            
            # Créer un mouvement d'entrée
            mouvement = MouvementStock(
                produit_id=ligne.produit_id,
                type=TypeMouvement.ENTREE.value,
                qte=ligne.qte,
                reference_doc=f"ACHAT-{self.id}"
            )
            db.session.add(mouvement)
    
    def to_dict(self, include_lignes=False):
        data = {
            'id': self.id,
            'fournisseur_id': self.fournisseur_id,
            'fournisseur_nom': self.fournisseur_ref.nom if self.fournisseur_ref else None,
            'date_achat': self.date_achat.isoformat(),
            'total': float(self.total),
            'nb_lignes': self.lignes.count()
        }
        
        if include_lignes:
            data['lignes'] = [ligne.to_dict() for ligne in self.lignes.all()]
        
        return data

class LigneAchat(db.Model):
    __tablename__ = 'lignes_achat'
    
    id = db.Column(db.Integer, primary_key=True)
    achat_id = db.Column(db.Integer, db.ForeignKey('achats.id'), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    qte = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=False)
    montant = db.Column(db.Numeric(12, 2), nullable=False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculer_montant()
    
    def calculer_montant(self):
        """Calcule le montant de la ligne"""
        if self.qte and self.prix_unitaire:
            self.montant = self.qte * self.prix_unitaire
    
    def __repr__(self):
        return f'<LigneAchat {self.achat_id} - {self.produit_id} - Qte: {self.qte}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'achat_id': self.achat_id,
            'produit_id': self.produit_id,
            'produit_reference': self.produit_ref.reference if self.produit_ref else None,
            'produit_nom': self.produit_ref.nom if self.produit_ref else None,
            'qte': self.qte,
            'prix_unitaire': float(self.prix_unitaire),
            'montant': float(self.montant)
        }

class Vente(db.Model):
    __tablename__ = 'ventes'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    date_vente = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    
    # Relations
    lignes = db.relationship('LigneVente', backref='vente_ref', lazy='dynamic', cascade='all, delete-orphan')
    retours = db.relationship('Retour', backref='vente_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<Vente {self.id} - {self.client_ref.nom if self.client_ref else "N/A"}>'
    
    def calculer_total(self):
        """Calcule le total de la vente"""
        self.total = sum(ligne.montant for ligne in self.lignes.all())
        return self.total
    
    def valider_vente(self):
        """Valide la vente et met à jour les stocks"""
        for ligne in self.lignes.all():
            # Traiter chaque ligne de vente avec les lots
            quantite_restante = ligne.qte
            
            # Récupérer les lots disponibles (FIFO)
            lots_disponibles = LotStock.query.filter_by(produit_id=ligne.produit_id)\
                                           .filter(LotStock.qte_disponible > 0)\
                                           .order_by(LotStock.date_entree.asc()).all()
            
            if not lots_disponibles or sum(lot.qte_disponible for lot in lots_disponibles) < quantite_restante:
                raise ValueError(f"Stock insuffisant pour le produit {ligne.produit_ref.reference}")
            
            # Prélever des lots
            for lot in lots_disponibles:
                if quantite_restante <= 0:
                    break
                
                qte_a_prelever = min(lot.qte_disponible, quantite_restante)
                
                # Créer une ligne de vente-lot
                ligne_lot = LigneVenteLot(
                    ligne_vente_id=ligne.id,
                    lot_stock_id=lot.id,
                    qte_utilisee=qte_a_prelever
                )
                db.session.add(ligne_lot)
                
                # Prélever du lot
                lot.prelever(qte_a_prelever)
                quantite_restante -= qte_a_prelever
    
    def to_dict(self, include_lignes=False):
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'client_nom': self.client_ref.nom if self.client_ref else None,
            'date_vente': self.date_vente.isoformat(),
            'total': float(self.total),
            'nb_lignes': self.lignes.count(),
            'nb_retours': self.retours.count()
        }
        
        if include_lignes:
            data['lignes'] = [ligne.to_dict() for ligne in self.lignes.all()]
        
        return data

class LigneVente(db.Model):
    __tablename__ = 'lignes_vente'
    
    id = db.Column(db.Integer, primary_key=True)
    vente_id = db.Column(db.Integer, db.ForeignKey('ventes.id'), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    qte = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=False)
    montant = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Relations
    lignes_lot = db.relationship('LigneVenteLot', backref='ligne_vente_ref', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculer_montant()
    
    def calculer_montant(self):
        """Calcule le montant de la ligne"""
        if self.qte and self.prix_unitaire:
            self.montant = self.qte * self.prix_unitaire
    
    def __repr__(self):
        return f'<LigneVente {self.vente_id} - {self.produit_id} - Qte: {self.qte}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'vente_id': self.vente_id,
            'produit_id': self.produit_id,
            'produit_reference': self.produit_ref.reference if self.produit_ref else None,
            'produit_nom': self.produit_ref.nom if self.produit_ref else None,
            'qte': self.qte,
            'prix_unitaire': float(self.prix_unitaire),
            'montant': float(self.montant),
            'lots_utilises': [ll.to_dict() for ll in self.lignes_lot.all()]
        }

class LigneVenteLot(db.Model):
    __tablename__ = 'lignes_vente_lot'
    
    id = db.Column(db.Integer, primary_key=True)
    ligne_vente_id = db.Column(db.Integer, db.ForeignKey('lignes_vente.id'), nullable=False)
    lot_stock_id = db.Column(db.Integer, db.ForeignKey('lots_stock.id'), nullable=False)
    qte_utilisee = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'<LigneVenteLot {self.ligne_vente_id} - Lot: {self.lot_stock_id} - Qte: {self.qte_utilisee}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'ligne_vente_id': self.ligne_vente_id,
            'lot_stock_id': self.lot_stock_id,
            'qte_utilisee': self.qte_utilisee,
            'prix_achat_lot': float(self.lot_stock_ref.prix_achat) if self.lot_stock_ref else None
        }

class Retour(db.Model):
    __tablename__ = 'retours'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    vente_id = db.Column(db.Integer, db.ForeignKey('ventes.id'))
    date_retour = db.Column(db.DateTime, default=datetime.utcnow)
    type_retour = db.Column(db.String(20), nullable=False)  # defectueux, garantie, erreur_commande, autre
    
    # Relations
    lignes = db.relationship('LigneRetour', backref='retour_ref', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Retour {self.id} - {self.type_retour}>'
    
    def traiter_retour(self):
        """Traite le retour selon son type"""
        for ligne in self.lignes.all():
            if self.type_retour in [TypeRetour.ERREUR_COMMANDE.value, TypeRetour.GARANTIE.value]:
                # Remettre en stock
                lot = LotStock(
                    produit_id=ligne.produit_id,
                    qte_disponible=ligne.qte,
                    prix_achat=ligne.produit_ref.prix  # Prix actuel du produit
                )
                db.session.add(lot)
                
                # Mouvement d'entrée
                mouvement = MouvementStock(
                    produit_id=ligne.produit_id,
                    type=TypeMouvement.ENTREE.value,
                    qte=ligne.qte,
                    reference_doc=f"RETOUR-{self.id}"
                )
                db.session.add(mouvement)
    
    def to_dict(self, include_lignes=False):
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'client_nom': self.client_ref.nom if self.client_ref else None,
            'vente_id': self.vente_id,
            'date_retour': self.date_retour.isoformat(),
            'type_retour': self.type_retour,
            'nb_lignes': self.lignes.count()
        }
        
        if include_lignes:
            data['lignes'] = [ligne.to_dict() for ligne in self.lignes.all()]
        
        return data

class LigneRetour(db.Model):
    __tablename__ = 'lignes_retour'
    
    id = db.Column(db.Integer, primary_key=True)
    retour_id = db.Column(db.Integer, db.ForeignKey('retours.id'), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    qte = db.Column(db.Integer, nullable=False)
    motif = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<LigneRetour {self.retour_id} - {self.produit_id} - Qte: {self.qte}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'retour_id': self.retour_id,
            'produit_id': self.produit_id,
            'produit_reference': self.produit_ref.reference if self.produit_ref else None,
            'produit_nom': self.produit_ref.nom if self.produit_ref else None,
            'qte': self.qte,
            'motif': self.motif
        }