from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """Hash a password using werkzeug's security utilities."""
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    """Verify a password against its hash."""
    return check_password_hash(hashed_password, password)

