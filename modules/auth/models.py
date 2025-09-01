
from datetime import datetime
from core.database import db
from werkzeug.security import generate_password_hash, check_password_hash

# Table de jointure pour les permissions des rôles
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

class TokenBlacklist(db.Model):
    __tablename__ = 'token_blacklist'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    user = db.relationship('User', backref='revoked_tokens')

    def __repr__(self):
        return f'<TokenBlacklist {self.jti[:8]}... by user {self.user_id}>'

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.relationship('Permission', secondary=role_permissions, backref='roles')
    users = db.relationship('User', backref='role_ref')

    def __repr__(self):
        return f'<Role {self.name}>'

class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Permission {self.code}>'

# Classe de base User
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Informations personnelles de base
    noms = db.Column(db.String(100))
    prenoms = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    
    # Champ discriminateur pour l'héritage
    user_type = db.Column(db.String(50))
    
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_permissions(self):
        """Retourne les permissions de l'utilisateur"""
        if self.role_ref:
            return [p.code for p in self.role_ref.permissions]
        return []

    def has_permission(self, permission_code):
        """Vérifie si l'utilisateur a une permission spécifique"""
        return permission_code in self.get_permissions()

    def __repr__(self):
        return f'<User {self.username}>'

# Classes spécialisées héritant de User
class Administrateur(User):
    __tablename__ = 'administrateurs'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    # Attributs spécifiques à l'administrateur
    niveau_acces = db.Column(db.String(20), default='complet')  # complet, partiel
    derniere_connexion_admin = db.Column(db.DateTime)
    ip_autorisees = db.Column(db.Text)  # JSON des IPs autorisées
    
    __mapper_args__ = {
        'polymorphic_identity': 'administrateur'
    }
    
    def gerer_utilisateur(self, user_id, action):
        """Méthodes spécifiques aux administrateurs"""
        if not self.has_permission('manage_users'):
            raise PermissionError("Permission insuffisante")
        
        # Logique de gestion d'utilisateur
        print(f"Admin {self.username} effectue l'action {action} sur l'utilisateur {user_id}")
        return True
    
    def attribuer_roles(self, user_id, role_id):
        """Attribuer un rôle à un utilisateur"""
        if not self.has_permission('manage_users'):
            raise PermissionError("Permission insuffisante")
        
        user = User.query.get(user_id)
        role = Role.query.get(role_id)
        
        if user and role:
            user.role_id = role_id
            db.session.commit()
            return True
        return False

class ResponsableRH(User):
    __tablename__ = 'responsables_rh'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    # Attributs spécifiques au RH
    departement = db.Column(db.String(100))
    certification_rh = db.Column(db.String(200))
    date_certification = db.Column(db.Date)
    
    __mapper_args__ = {
        'polymorphic_identity': 'responsable_rh'
    }
    
    def gerer_employes(self, employe_id, action_data):
        """Gérer les données des employés"""
        if not self.has_permission('manage_users'):
            raise PermissionError("Permission insuffisante pour gérer les employés")
        
        # Logique spécifique RH
        print(f"RH {self.username} gère l'employé {employe_id}")
        return True
    
    def gerer_absences(self, employe_id, absence_data):
        """Gérer les absences des employés"""
        if not self.has_permission('view_reports'):
            raise PermissionError("Permission insuffisante")
        
        # Logique de gestion des absences
        print(f"RH {self.username} traite l'absence pour l'employé {employe_id}")
        return True

class Magasinier(User):
    __tablename__ = 'magasiniers'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    # Attributs spécifiques au magasinier
    entrepot_assigne = db.Column(db.String(100))
    niveau_autorisation = db.Column(db.String(50))  # lecture, ecriture, supervision
    formations_securite = db.Column(db.Text)  # JSON des formations
    
    __mapper_args__ = {
        'polymorphic_identity': 'magasinier'
    }
    
    def gerer_stock(self, produit_id, quantite, operation):
        """Gérer les opérations de stock"""
        # Vérification des permissions métier
        if operation == 'sortie' and not self.has_permission('manage_inventory'):
            raise PermissionError("Permission insuffisante pour les sorties")
        
        # Logique de gestion du stock
        print(f"Magasinier {self.username} : {operation} de {quantite} pour produit {produit_id}")
        return True
    
    def generer_rapport_stock(self):
        """Générer un rapport de stock"""
        if not self.has_permission('view_reports'):
            raise PermissionError("Permission insuffisante pour les rapports")
        
        # Logique de génération de rapport
        return {"entrepot": self.entrepot_assigne, "timestamp": datetime.utcnow()}

class Comptable(User):
    __tablename__ = 'comptables'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    # Attributs spécifiques au comptable
    numero_ordre = db.Column(db.String(50))  # Numéro d'ordre des comptables
    specialite = db.Column(db.String(100))  # fiscalité, audit, etc.
    certification_comptable = db.Column(db.String(200))
    
    __mapper_args__ = {
        'polymorphic_identity': 'comptable'
    }
    
    def gerer_comptabilite(self, transaction_data):
        """Gérer les opérations comptables"""
        if not self.has_permission('manage_payroll'):
            raise PermissionError("Permission insuffisante pour la comptabilité")
        
        # Logique comptable
        print(f"Comptable {self.username} traite une transaction")
        return True
    
    def generer_bilan(self, periode):
        """Générer un bilan comptable"""
        if not self.has_permission('manage_payroll'):
            raise PermissionError("Permission insuffisante")
        
        # Logique de génération de bilan
        return {"periode": periode, "comptable": self.username}

# Factory pattern pour créer les utilisateurs
class UserFactory:
    """Factory pour créer les différents types d'utilisateurs"""
    
    USER_CLASSES = {
        'administrateur': Administrateur,
        'responsable_rh': ResponsableRH,
        'magasinier': Magasinier,
        'comptable': Comptable,
        'user': User  # Utilisateur de base
    }
    
    @classmethod
    def create_user(cls, user_type, **kwargs):
        """
        Crée un utilisateur du type spécifié
        
        Args:
            user_type (str): Type d'utilisateur à créer
            **kwargs: Arguments pour la création de l'utilisateur
            
        Returns:
            User: Instance du type d'utilisateur créé
        """
        user_class = cls.USER_CLASSES.get(user_type.lower(), User)
        
        # Créer l'instance
        user = user_class(**kwargs)
        user.user_type = user_type.lower()
        
        return user
    
    @classmethod
    def get_user_class(cls, user_type):
        """Retourne la classe correspondant au type d'utilisateur"""
        return cls.USER_CLASSES.get(user_type.lower(), User)

# Modèle pour les permissions étendues par type d'utilisateur
class UserTypePermission(db.Model):
    """Permissions spécifiques par type d'utilisateur"""
    __tablename__ = 'user_type_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(50), nullable=False)
    permission_code = db.Column(db.String(100), nullable=False)
    is_default = db.Column(db.Boolean, default=False)  # Permission par défaut pour ce type
    
    __table_args__ = (
        db.UniqueConstraint('user_type', 'permission_code'),
    )