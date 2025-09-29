from argon2 import PasswordHasher

ph = PasswordHasher()

def hash_password(password: str) -> str:
    """Hash a password using Argon2"""
    return ph.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        ph.verify(hashed_password, password)
        return True
    except Exception:
        return False
