from werkzeug.security import generate_password_hash, check_password_hash
import re
from functools import wraps
from flask import redirect, url_for, session, flash

# 🔐 HASH MOT DE PASSE
def hash_password(password):
    """Hasher un mot de passe"""
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    """Vérifier un mot de passe hashé"""
    return check_password_hash(hashed_password, password)

# 📧 VALIDATION EMAIL
def is_valid_email(email):
    """Valider format email"""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

# 📱 VALIDATION TELEPHONE (Bénin)
def is_valid_phone(phone):
    """Valider numéro téléphone Bénin
    Accepte: +229XXXXXXXX, 229XXXXXXXX, XXXXXXXX
    """
    pattern = r"^(\+229|229)?\d{8}$"
    return bool(re.match(pattern, phone))

# 🔒 PROTECTION DES PAGES (LOGIN REQUIRED)
def login_required(f):
    """Décorateur pour routes protégées"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "id" not in session:  # IMPORTANT: 'id' pas 'user_id'
            flash("Connectez-vous d'abord.", 'danger')
            return redirect(url_for('auth.connexion'))
        return f(*args, **kwargs)
    return wrapper