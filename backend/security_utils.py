from werkzeug.security import generate_password_hash, check_password_hash
import re
from functools import wraps
from flask import redirect, url_for, session

# 🔐 HASH MOT DE PASSE
def hash_password(password):
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    return check_password_hash(hashed_password, password)

# 📧 VALIDATION EMAIL
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

# 📱 VALIDATION TELEPHONE (Bénin)
def is_valid_phone(phone):
    pattern = r"^\+229\d{8}$"
    return bool(re.match(pattern, phone))

# 🔒 PROTECTION DES PAGES (LOGIN REQUIRED)
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper