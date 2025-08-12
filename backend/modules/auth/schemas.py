from marshmallow import Schema, fields, validate, ValidationError
from backend.cores.utils import validate_email, validate_phone

class UserSchema(Schema):
    """Schéma pour la sérialisation des utilisateurs"""
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    role = fields.Str(validate=validate.OneOf(['admin', 'manager', 'user']))
    is_active = fields.Bool(dump_only=True)
    is_verified = fields.Bool(dump_only=True)
    last_login = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class UserCreateSchema(Schema):
    """Schéma pour la création d'utilisateur"""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    confirm_password = fields.Str(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    role = fields.Str(validate=validate.OneOf(['admin', 'manager', 'user']), missing='user')
    
    def validate_confirm_password(self, value, data, **kwargs):
        if value != data.get('password'):
            raise ValidationError('Les mots de passe ne correspondent pas')
        return value

class UserUpdateSchema(Schema):
    """Schéma pour la mise à jour d'utilisateur"""
    first_name = fields.Str(validate=validate.Length(min=1, max=50))
    last_name = fields.Str(validate=validate.Length(min=1, max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    role = fields.Str(validate=validate.OneOf(['admin', 'manager', 'user']))

class LoginSchema(Schema):
    """Schéma pour la connexion"""
    username = fields.Str(required=True)
    password = fields.Str(required=True)
    remember = fields.Bool(missing=False)

class PasswordChangeSchema(Schema):
    """Schéma pour le changement de mot de passe"""
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=6))
    confirm_password = fields.Str(required=True)
    
    def validate_confirm_password(self, value, data, **kwargs):
        if value != data.get('new_password'):
            raise ValidationError('Les nouveaux mots de passe ne correspondent pas')
        return value

class PasswordResetSchema(Schema):
    """Schéma pour la réinitialisation de mot de passe"""
    email = fields.Email(required=True)

class PasswordResetConfirmSchema(Schema):
    """Schéma pour la confirmation de réinitialisation de mot de passe"""
    session_id = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=6))
    confirm_password = fields.Str(required=True)
    
    def validate_confirm_password(self, value, data, **kwargs):
        if value != data.get('new_password'):
            raise ValidationError('Les nouveaux mots de passe ne correspondent pas')
        return value 