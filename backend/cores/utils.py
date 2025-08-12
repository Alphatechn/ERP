import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from flask import jsonify
from werkzeug.exceptions import HTTPException

def validate_email(email: str) -> bool:
    """Valide le format d'un email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Valide le format d'un numéro de téléphone"""
    # Supprime les espaces et caractères spéciaux
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    # Vérifie si c'est un numéro français valide
    return re.match(r'^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$', phone) is not None

def format_currency(amount: float, currency: str = "EUR") -> str:
    """Formate un montant en devise"""
    return f"{amount:.2f} {currency}"

def format_date(date_obj: date, format_str: str = "%d/%m/%Y") -> str:
    """Formate une date"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
        except ValueError:
            return date_obj
    return date_obj.strftime(format_str)

def generate_reference(prefix: str, sequence: int) -> str:
    """Génère une référence unique"""
    return f"{prefix}{datetime.now().year}{sequence:06d}"

def handle_api_error(error: Exception) -> tuple:
    """Gère les erreurs API de manière uniforme"""
    if isinstance(error, HTTPException):
        response = {
            'error': True,
            'message': error.description,
            'code': error.code
        }
        return jsonify(response), error.code
    
    # Erreur interne du serveur
    response = {
        'error': True,
        'message': 'Une erreur interne s\'est produite',
        'code': 500
    }
    return jsonify(response), 500

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Optional[str]:
    """Valide que tous les champs requis sont présents"""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return f"Champs manquants: {', '.join(missing_fields)}"
    return None

def sanitize_string(text: str) -> str:
    """Nettoie une chaîne de caractères"""
    if not text:
        return ""
    # Supprime les caractères dangereux
    return re.sub(r'[<>"\']', '', text.strip())

def paginate_results(query, page: int = 1, per_page: int = 20):
    """Pagine les résultats d'une requête"""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def create_pagination_response(pagination):
    """Crée une réponse de pagination standardisée"""
    return {
        'items': [item.to_dict() for item in pagination.items],
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }
