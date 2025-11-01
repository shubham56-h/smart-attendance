from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

def hash_password(password):
    """Hash a password using werkzeug's security utilities."""
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    """Verify a password against its hash."""
    return check_password_hash(hashed_password, password)

def generate_tokens(identity, additional_claims=None):
    """
    Generate access and refresh tokens for a user.
    
    Args:
        identity: Unique identifier for the user (typically user ID or email)
        additional_claims: Optional dictionary of additional claims to include in token
    
    Returns:
        tuple: (access_token, refresh_token)
    """
    access_token = create_access_token(identity=identity, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=identity, additional_claims=additional_claims)
    return access_token, refresh_token

