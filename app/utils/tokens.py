import hashlib
import secrets


def generate_token() -> str:
    """Generate a URL-safe random token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """SHA-256 hash of a token for safe DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()